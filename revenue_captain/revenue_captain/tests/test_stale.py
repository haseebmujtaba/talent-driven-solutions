from __future__ import annotations

from revenue_captain.models import EvidenceItem, ReasonCode
from revenue_captain.rules import evaluate

from .conftest import make_app, make_event, make_route


def test_no_activity_within_threshold_is_not_stale(now):
    apps = [make_app("app_a", created_at="2026-06-10T00:00:00Z", updated_at="2026-06-15T00:00:00Z")]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.STALE.value not in flags["app_a"]["reason_codes"]


def test_no_activity_past_threshold_is_stale(now):
    # now = 2026-06-21. updated_at 40 days earlier, no events, no evidence.
    apps = [make_app("app_a", created_at="2026-05-12T00:00:00Z", updated_at="2026-05-12T00:00:00Z")]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.STALE.value in flags["app_a"]["reason_codes"]


def test_recent_event_resets_staleness_even_if_updated_at_old(now):
    apps = [make_app("app_a", created_at="2026-05-01T00:00:00Z", updated_at="2026-05-01T00:00:00Z")]
    events = {
        "app_a": [make_event("evt_1", "app_a", "call_logged", "2026-06-18T00:00:00Z")]
    }
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, events, routes, now)

    assert ReasonCode.STALE.value not in flags["app_a"]["reason_codes"]
    assert flags["app_a"]["last_activity_at"].startswith("2026-06-18")


def test_recent_evidence_receipt_counts_as_activity(now):
    apps = [
        make_app(
            "app_a",
            created_at="2026-05-01T00:00:00Z",
            updated_at="2026-05-01T00:00:00Z",
            evidence=[EvidenceItem("transcript", "2026-06-19T00:00:00Z")],
        )
    ]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.STALE.value not in flags["app_a"]["reason_codes"]


def test_closed_applications_are_never_stale(now):
    apps = [make_app("app_a", status="closed_won", created_at="2026-01-01T00:00:00Z", updated_at="2026-01-01T00:00:00Z")]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.STALE.value not in flags["app_a"]["reason_codes"]
