"""
Rules engine: derives reason codes, duplicate links, and human-review
flags from the current source state. Every function here is a pure
function of (applications, events_by_application, school_routes, now) --
no hidden state, no I/O. That purity is what makes the detectors easy
to unit test and is also half of why re-running the worker is safe:
the output is fully determined by the inputs you pass in.

Thresholds are deliberately simple constants rather than configurable
business rules. See README "Tradeoffs" for why.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .models import (
    Application,
    ApplicationStatus,
    Event,
    REQUIRED_EVIDENCE_TYPES,
    ReasonCode,
    SchoolRoute,
    normalize_email,
    normalize_name,
)

STALE_DAYS = 14
EVIDENCE_GRACE_DAYS = 7


def parse_ts(ts: str) -> datetime:
    # Accept trailing 'Z' as UTC, which is what our JSON inputs use.
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _last_activity(app: Application, events: list[Event]) -> datetime:
    timestamps = [parse_ts(app.updated_at)]
    timestamps += [parse_ts(e.timestamp) for e in events]
    for ev in app.evidence:
        if ev.received_at:
            timestamps.append(parse_ts(ev.received_at))
    return max(timestamps)


def _first_evidence_requested_at(app: Application, events: list[Event]) -> datetime | None:
    requested = [e for e in events if e.type == "evidence_requested"]
    if not requested:
        return None
    return min(parse_ts(e.timestamp) for e in requested)


def evaluate(
    applications: list[Application],
    events_by_application: dict[str, list[Event]],
    school_routes: dict[str, SchoolRoute],
    now: datetime,
) -> dict[str, dict]:
    """
    Returns a dict keyed by application_id:
        {
            "last_activity_at": iso str,
            "reason_codes": [str, ...],
            "duplicate_of": Optional[str],
            "needs_human_review": bool,
        }
    """
    flags: dict[str, dict] = {
        app.id: {
            "last_activity_at": None,
            "reason_codes": [],
            "duplicate_of": None,
            "needs_human_review": False,
        }
        for app in applications
    }

    apps_by_id = {app.id: app for app in applications}

    _detect_stale(applications, events_by_application, now, flags)
    _detect_duplicates(applications, flags)
    _detect_possible_name_matches(applications, flags)
    _detect_missing_evidence(applications, events_by_application, now, flags)
    _detect_bounced_routes(applications, events_by_application, school_routes, flags)
    _detect_manual_flags(applications, events_by_application, flags)

    human_review_codes = ReasonCode.human_review_codes()
    for app_id, f in flags.items():
        if any(code in human_review_codes for code in f["reason_codes"]):
            f["needs_human_review"] = True

    return flags


def _detect_stale(
    applications: list[Application],
    events_by_application: dict[str, list[Event]],
    now: datetime,
    flags: dict[str, dict],
) -> None:
    for app in applications:
        events = events_by_application.get(app.id, [])
        last_activity = _last_activity(app, events)
        flags[app.id]["last_activity_at"] = last_activity.isoformat()
        if ApplicationStatus.is_closed(app.status):
            continue
        age_days = (now - last_activity).total_seconds() / 86400
        if age_days > STALE_DAYS:
            flags[app.id]["reason_codes"].append(ReasonCode.STALE.value)


def _detect_duplicates(applications: list[Application], flags: dict[str, dict]) -> None:
    """Exact-email duplicates: the earliest-created application by a
    given normalized email is the primary; later ones are flagged and
    linked via duplicate_of. We never silently merge or delete records
    -- a human (or a separate merge action) does that."""
    by_email: dict[str, list[Application]] = {}
    for app in applications:
        by_email.setdefault(normalize_email(app.email), []).append(app)

    for _, group in by_email.items():
        if len(group) < 2:
            continue
        group_sorted = sorted(group, key=lambda a: (a.created_at, a.id))
        primary = group_sorted[0]
        for dup in group_sorted[1:]:
            flags[dup.id]["reason_codes"].append(ReasonCode.DUPLICATE_APPLICANT.value)
            flags[dup.id]["duplicate_of"] = primary.id


def _detect_possible_name_matches(applications: list[Application], flags: dict[str, dict]) -> None:
    """Same normalized name, *different* email. This is intentionally
    NOT auto-merged -- common names collide, and merging on a false
    positive silently destroys a legitimate applicant's record. We
    route it to a human instead. See README tradeoffs."""
    by_name: dict[str, list[Application]] = {}
    for app in applications:
        by_name.setdefault(normalize_name(app.name), []).append(app)

    for _, group in by_name.items():
        emails = {normalize_email(a.email) for a in group}
        if len(group) < 2 or len(emails) < 2:
            continue
        for app in group:
            # Don't double-flag something already resolved as an exact
            # email duplicate.
            if ReasonCode.DUPLICATE_APPLICANT.value in flags[app.id]["reason_codes"]:
                continue
            flags[app.id]["reason_codes"].append(ReasonCode.POSSIBLE_DUPLICATE_NAME_MATCH.value)


def _detect_missing_evidence(
    applications: list[Application],
    events_by_application: dict[str, list[Event]],
    now: datetime,
    flags: dict[str, dict],
) -> None:
    for app in applications:
        if ApplicationStatus.is_closed(app.status) or app.status == ApplicationStatus.NEW.value:
            continue
        have_types = {e.type for e in app.evidence if e.received_at}
        missing = REQUIRED_EVIDENCE_TYPES - have_types
        if not missing:
            continue
        events = events_by_application.get(app.id, [])
        requested_at = _first_evidence_requested_at(app, events)
        # If evidence was never formally requested, fall back to the
        # application's creation date as the start of the grace period.
        baseline = requested_at or parse_ts(app.created_at)
        age_days = (now - baseline).total_seconds() / 86400
        if age_days > EVIDENCE_GRACE_DAYS:
            flags[app.id]["reason_codes"].append(ReasonCode.MISSING_EVIDENCE.value)


def _detect_bounced_routes(
    applications: list[Application],
    events_by_application: dict[str, list[Event]],
    school_routes: dict[str, SchoolRoute],
    flags: dict[str, dict],
) -> None:
    for app in applications:
        route = school_routes.get(app.school_id)
        events = events_by_application.get(app.id, [])
        bounced_event = any(e.type == "email_bounced" for e in events)
        if route is None:
            flags[app.id]["reason_codes"].append(ReasonCode.UNKNOWN_SCHOOL_ROUTE.value)
            continue
        if route.status == "bounced" or bounced_event:
            flags[app.id]["reason_codes"].append(ReasonCode.BOUNCED_ROUTE.value)


def _detect_manual_flags(
    applications: list[Application],
    events_by_application: dict[str, list[Event]],
    flags: dict[str, dict],
) -> None:
    for app in applications:
        events = events_by_application.get(app.id, [])
        if any(e.type == "flag_for_review" for e in events):
            flags[app.id]["reason_codes"].append(ReasonCode.MANUAL_FLAG_FOR_REVIEW.value)
