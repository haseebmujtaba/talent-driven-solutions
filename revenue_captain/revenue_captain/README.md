# Revenue Captain

A small service that turns three feeds of upstream data — applications,
activity events, and school routing config — into a durable state model
and a ranked, reason-coded next-action queue for an admissions/outreach
team.

## Quick start

```bash
pip install -e .  # or just run from the repo root, stdlib-only
python -m revenue_captain.worker run \
  --applications data/applications.json \
  --events data/events.json \
  --school-routes data/school_routes.json \
  --db state.db \
  --now 2026-06-21T00:00:00Z

python -m revenue_captain.worker queue --db state.db   # reprint without re-ingesting

pytest -v
```

`data/` contains a small sample dataset that deliberately exercises
every detector: an exact-email duplicate, a same-name/different-email
ambiguous match, a stale candidate, a missing-evidence candidate, a
bounced route (both via route status and via a bounce event), an
unknown school id, a manually-flagged record, and a closed (control)
record that should never appear in the queue.

## Architecture

```
applications.json ─┐
events.json ────────┼─► ingest.py ─► models.py ─► store.py (SQLite) ─► rules.py ─► queue.py
school_routes.json ┘                  (source tables)        (derived tables)
```

**models.py** — the normalized shape everything else operates on:
`Application`, `Event`, `SchoolRoute`, plus the `ReasonCode` enum. This
is the "durable state model" the spec asks for — a small, stable
vocabulary that the raw JSON gets mapped into immediately at the
boundary, so nothing downstream needs to know about upstream field
names.

**ingest.py** — the only file that knows the raw JSON schema. It maps
rows into model objects. If the upstream export format changes, this
is the only file that should need to change.

**store.py** — a SQLite file is the durable store. It holds two kinds
of tables:
- *Source tables* (`applications`, `evidence`, `events_seen`,
  `school_routes`) — upserted by stable id (`INSERT ... ON CONFLICT DO
  UPDATE`). Re-ingesting the same or an extended file never creates
  duplicate rows.
- *Derived tables* (`application_flags`, `next_action_queue`) — fully
  deleted and rebuilt, inside one transaction, on every run.

**rules.py** — pure functions that take the full current state plus a
`now` timestamp and return reason codes per application: `STALE`,
`DUPLICATE_APPLICANT`, `POSSIBLE_DUPLICATE_NAME_MATCH`,
`MISSING_EVIDENCE`, `BOUNCED_ROUTE`, `UNKNOWN_SCHOOL_ROUTE`,
`MANUAL_FLAG_FOR_REVIEW`. No I/O, no hidden state — that's what makes
them straightforward to unit test in isolation from the database.

**queue.py** — turns applications + their reason codes into a ranked
list of `(application_id, action, priority_score, reason_codes)`,
sorted by score descending and application id ascending as a
tiebreaker, so ordering never depends on dict/set iteration order.

**worker.py** — the CLI. `run` is the one idempotent command the spec
asks for: ingest, then fully recompute derived state. `queue` just
reprints the last computed queue without touching source data.

## Why idempotency works here

The mechanism is deliberately boring: **derived state is a pure
function of source state, recomputed from scratch every run, inside a
transaction.**

- Source writes are keyed upserts, so replaying the same file (or a
  file with new rows appended) never duplicates anything; it either
  inserts a new row or overwrites an existing one with identical data.
- Derived writes (`application_flags`, `next_action_queue`) are never
  patched incrementally. Each run does `DELETE FROM ...` then
  re-`INSERT`, in one SQLite transaction. If the process dies
  mid-recompute, the transaction never commits and the database is
  left exactly as it was before the run started — there's no
  in-between state to corrupt into.
- The rules and queue functions take `now` as an explicit argument
  rather than reading the wall clock internally, so the same inputs
  always produce the same outputs (verified by
  `tests/test_idempotency.py`, which runs the worker against the same
  files repeatedly and asserts row counts and queue contents are
  byte-identical after the first run).

The cost of this approach is that every run is O(all applications),
not O(what changed). For the size of dataset this kind of system
typically deals with (thousands, maybe low tens of thousands of
applications) that's a non-issue and the correctness guarantee is
worth far more than the savings from incremental computation. See
"Production hardening" for what changes at real scale.

## Tradeoffs I made on purpose

- **Possible duplicates by name are never auto-merged.** Two
  applications with the same normalized name but different emails are
  routed to `human_review` (`POSSIBLE_DUPLICATE_NAME_MATCH`), not
  silently linked or merged. Common names collide; auto-merging on a
  false positive would corrupt a real applicant's record, which is a
  worse failure mode than asking a human to glance at it. Exact-email
  duplicates *are* auto-linked (`duplicate_of`), because email
  collision is a much stronger signal — but even then the system only
  links, it never deletes or merges data itself.
- **Thresholds are fixed constants** (`STALE_DAYS = 14`,
  `EVIDENCE_GRACE_DAYS = 7`), not a configurable rules table. For a
  take-home-sized system, a config table is speculative complexity. In
  production these would likely move to a per-school or per-program
  config, since a 14-day staleness window probably isn't right for
  every partner school.
- **Full recompute over incremental update** for derived state, as
  described above — correctness over cleverness at this scale.
- **Missing-evidence required types are a single global set**
  (`transcript`, `essay`). Real programs likely have different
  requirements per school, which would turn this into a per-school
  lookup rather than a constant.
- **"Bounced route" treats a stale `school_routes.json` status and a
  live `email_bounced` event as independent, OR'd signals** rather
  than trying to reconcile them, because the route config and the
  event stream can legitimately disagree about reality at any given
  moment, and ORing them is the conservative (don't miss a real
  bounce) choice.

## Production hardening

If this were going into production rather than being a take-home, the
things I'd change first, roughly in order:

1. **Concurrency control.** Right now nothing stops two worker
   invocations from running at the same time and racing on the same
   SQLite file. I'd either move to a database that handles concurrent
   writers properly (Postgres) or add an explicit run-lock (e.g. an
   advisory lock row, or just a single-flight queue in front of the
   worker).
2. **Incremental recompute.** Full recompute is fine at this scale but
   won't stay fine forever. I'd add a `dirty` watermark (last-seen
   event timestamp or a changed-application set) so a run only
   re-evaluates applications touched since the last run, while keeping
   the same "delete-and-rewrite-derived-rows-for-affected-ids" pattern
   so the idempotency guarantee doesn't weaken.
3. **Schema validation at the ingest boundary.** `ingest.py` currently
   trusts the JSON shape and will raise a `KeyError` on a malformed
   row. I'd add explicit schema validation (e.g. `pydantic`) with
   per-row error collection, so one bad row in a 5,000-row file doesn't
   kill the whole ingest run — it should fail that row, log it, and
   keep going.
4. **Observability.** Structured logging per run (rows ingested,
   counts per reason code, run duration), plus a way to diff this
   run's queue against the previous one, so a human can see "what
   changed" instead of re-reading the whole queue every time.
5. **Action execution, not just action *recommendation*.** This
   service currently stops at "here's the ranked queue" — it doesn't
   send the email or fix the route itself. Production would need an
   execution layer with its own idempotency keys (so a retried "send
   reminder" doesn't double-email a candidate), plus a feedback loop
   that records what was actually done.
6. **Soft-delete / audit trail on duplicate merges.** Right now a
   duplicate is only *linked* (`duplicate_of`), which is intentionally
   conservative — but a real merge workflow needs an audit log of who
   merged what into what and when, with the ability to undo it.
7. **Time zone / locale handling at the edges.** Internally everything
   is UTC, which is right for the engine, but a real product surfaces
   "stale for 49 days" to a human, and that human cares about wall
   clock dates in their own time zone.

## Tests

```
tests/test_duplicates.py        exact-email duplicates, ambiguous name matches, normalization
tests/test_stale.py             staleness threshold, activity from events/evidence, closed exclusion
tests/test_missing_evidence.py  grace period from creation vs. from evidence_requested, partial evidence
tests/test_bounced_route.py     route-status bounce, event-based bounce, unknown school routing
tests/test_idempotency.py       rerun-is-a-no-op, repeated reruns stay stable, append-only event growth,
                                 re-ingesting an updated record doesn't duplicate it, deterministic ordering
```

Run everything with `pytest -v`.
