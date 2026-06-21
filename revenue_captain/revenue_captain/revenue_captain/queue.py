"""
Builds the ranked next-action queue from applications + the flags
computed by rules.py. Pure function, deterministic ordering -- ties are
broken by application id so the output order never depends on dict /
set iteration order or wall-clock timing.
"""

from __future__ import annotations

from datetime import datetime

from .models import Application, ApplicationStatus, QueueItem, ReasonCode
from .rules import parse_ts

# Base scores per category. Higher = more urgent / earlier in the queue.
SCORE_HUMAN_REVIEW = 100.0
SCORE_BOUNCED_ROUTE = 90.0
SCORE_DUPLICATE = 80.0
SCORE_MISSING_EVIDENCE_BASE = 60.0
SCORE_STALE_BASE = 40.0
SCORE_NEW = 20.0
SCORE_HEALTHY_IN_PROGRESS = 10.0

# Caps so an extremely old/overdue item can't jump into a higher band
# than its category (e.g. a 400-day-stale app should still rank below
# any bounced route, not above it).
_OVERDUE_DAYS_CAP = 30


def build_queue(
    applications: list[Application],
    flags: dict[str, dict],
    now: datetime,
) -> list[QueueItem]:
    items: list[QueueItem] = []

    for app in applications:
        if ApplicationStatus.is_closed(app.status):
            continue

        f = flags[app.id]
        reasons = f["reason_codes"]

        action, score = _classify(app, f, reasons, now)
        if action is None:
            continue

        items.append(
            QueueItem(
                application_id=app.id,
                action=action,
                priority_score=round(score, 4),
                reason_codes=list(reasons),
            )
        )

    items.sort(key=lambda i: (-i.priority_score, i.application_id))
    return items


def _classify(app: Application, f: dict, reasons: list[str], now: datetime) -> tuple[str | None, float]:
    if f["needs_human_review"]:
        return "human_review", SCORE_HUMAN_REVIEW

    if ReasonCode.BOUNCED_ROUTE.value in reasons:
        return "fix_route_and_resend", SCORE_BOUNCED_ROUTE

    if ReasonCode.DUPLICATE_APPLICANT.value in reasons:
        return "merge_into_primary", SCORE_DUPLICATE

    if ReasonCode.MISSING_EVIDENCE.value in reasons:
        baseline = parse_ts(app.created_at)
        overdue_days = min((now - baseline).total_seconds() / 86400, _OVERDUE_DAYS_CAP)
        return "request_missing_evidence", SCORE_MISSING_EVIDENCE_BASE + overdue_days * 0.5

    if ReasonCode.STALE.value in reasons:
        last_activity = parse_ts(f["last_activity_at"])
        stale_days = min((now - last_activity).total_seconds() / 86400, _OVERDUE_DAYS_CAP)
        return "re_engage_candidate", SCORE_STALE_BASE + stale_days * 0.3

    if app.status == ApplicationStatus.NEW.value:
        return "initial_outreach", SCORE_NEW

    return "advance_pipeline", SCORE_HEALTHY_IN_PROGRESS
