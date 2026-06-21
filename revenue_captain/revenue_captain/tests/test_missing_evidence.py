from __future__ import annotations

from revenue_captain.models import EvidenceItem, ReasonCode
from revenue_captain.rules import evaluate

from .conftest import make_app, make_event, make_route


def test_within_grace_period_not_flagged(now):
    # now = 2026-06-21; created 3 days ago, nothing requested yet.
    apps = [make_app("app_a", status="contacted", created_at="2026-06-18T00:00:00Z", evidence=[])]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.MISSING_EVIDENCE.value not in flags["app_a"]["reason_codes"]


def test_past_grace_period_with_no_evidence_is_flagged(now):
    apps = [make_app("app_a", status="contacted", created_at="2026-05-01T00:00:00Z", evidence=[])]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.MISSING_EVIDENCE.value in flags["app_a"]["reason_codes"]


def test_grace_period_measured_from_evidence_requested_event(now):
    # Created long ago, but evidence wasn't requested until recently --
    # the clock should start at the request, not at creation.
    apps = [make_app("app_a", status="contacted", created_at="2026-01-01T00:00:00Z", evidence=[])]
    events = {"app_a": [make_event("evt_1", "app_a", "evidence_requested", "2026-06-19T00:00:00Z")]}
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, events, routes, now)

    assert ReasonCode.MISSING_EVIDENCE.value not in flags["app_a"]["reason_codes"]


def test_partial_evidence_still_flags_for_missing_types(now):
    apps = [
        make_app(
            "app_a",
            status="contacted",
            created_at="2026-05-01T00:00:00Z",
            evidence=[EvidenceItem("transcript", "2026-05-02T00:00:00Z")],  # essay still missing
        )
    ]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.MISSING_EVIDENCE.value in flags["app_a"]["reason_codes"]


def test_complete_evidence_is_not_flagged(now):
    apps = [
        make_app(
            "app_a",
            status="contacted",
            created_at="2026-05-01T00:00:00Z",
            evidence=[
                EvidenceItem("transcript", "2026-05-02T00:00:00Z"),
                EvidenceItem("essay", "2026-05-03T00:00:00Z"),
            ],
        )
    ]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.MISSING_EVIDENCE.value not in flags["app_a"]["reason_codes"]


def test_brand_new_unactioned_application_is_not_flagged(now):
    # status "new" means nobody has even reached out yet -- chasing
    # evidence at this stage isn't a meaningful next action.
    apps = [make_app("app_a", status="new", created_at="2026-01-01T00:00:00Z", evidence=[])]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.MISSING_EVIDENCE.value not in flags["app_a"]["reason_codes"]
