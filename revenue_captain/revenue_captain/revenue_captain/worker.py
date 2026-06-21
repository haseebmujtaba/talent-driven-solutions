"""
Worker CLI. The `run` command is the one idempotent entrypoint required
by the spec: it can be invoked any number of times, in any order
relative to itself, against the same or appended input files, and the
resulting database + queue output will be identical (modulo the `now`
timestamp, which you can pin with --now for reproducible runs).

Usage:
    python -m revenue_captain.worker run \\
        --applications data/applications.json \\
        --events data/events.json \\
        --school-routes data/school_routes.json \\
        --db state.db \\
        --now 2026-06-21T00:00:00Z

    python -m revenue_captain.worker queue --db state.db
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from . import ingest
from .queue import build_queue
from .rules import evaluate
from .store import Store


def run(args: argparse.Namespace) -> None:
    store = Store(args.db)
    try:
        applications = ingest.load_applications(args.applications)
        events = ingest.load_events(args.events)
        routes = ingest.load_school_routes(args.school_routes)

        # 1. Upsert all source data. Safe to repeat: every write is
        #    keyed by a stable id (application id / event id / school
        #    id) using INSERT ... ON CONFLICT DO UPDATE.
        store.upsert_applications(applications)
        store.upsert_events(events)
        store.upsert_school_routes(routes)

        # 2. Recompute ALL derived state from scratch. We never patch
        #    flags or the queue incrementally -- we delete and rebuild
        #    inside one transaction. That means a crash mid-run leaves
        #    either the old derived state (txn never committed) or the
        #    new one (txn committed), never a half-applied mix.
        now = _parse_now(args.now)
        all_apps = store.all_applications()
        events_by_app = store.all_events_by_application()
        routes_by_id = store.all_school_routes()

        flags = evaluate(all_apps, events_by_app, routes_by_id, now)
        store.replace_application_flags(
            [{"application_id": aid, **f} for aid, f in flags.items()]
        )

        queue_items = build_queue(all_apps, flags, now)
        store.replace_queue(queue_items)

        if not args.quiet:
            _print_queue(store)
    finally:
        store.close()


def queue_cmd(args: argparse.Namespace) -> None:
    store = Store(args.db)
    try:
        _print_queue(store)
    finally:
        store.close()


def _print_queue(store: Store) -> None:
    rows = store.get_queue()
    print(json.dumps(rows, indent=2))


def _parse_now(now_str: str | None) -> datetime:
    if now_str is None:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(now_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="revenue_captain.worker")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Ingest inputs and recompute derived state + queue. Idempotent.")
    run_p.add_argument("--applications", required=True)
    run_p.add_argument("--events", required=True)
    run_p.add_argument("--school-routes", required=True)
    run_p.add_argument("--db", required=True)
    run_p.add_argument("--now", default=None, help="ISO timestamp to use as 'now' (default: real current time)")
    run_p.add_argument("--quiet", action="store_true")
    run_p.set_defaults(func=run)

    queue_p = sub.add_parser("queue", help="Print the current next-action queue without re-ingesting.")
    queue_p.add_argument("--db", required=True)
    queue_p.set_defaults(func=queue_cmd)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
