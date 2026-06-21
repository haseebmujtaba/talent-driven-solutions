from __future__ import annotations

from revenue_captain.models import ReasonCode
from revenue_captain.rules import evaluate

from .conftest import make_app, make_event, make_route


def test_route_marked_bounced_flags_application(now):
    apps = [make_app("app_a", school_id="sch_01")]
    routes = {"sch_01": make_route("sch_01", status="bounced")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.BOUNCED_ROUTE.value in flags["app_a"]["reason_codes"]


def test_active_route_with_bounce_event_still_flags(now):
    # The school's route record hasn't been updated yet, but we directly
    # observed a bounce -- the event is independent corroborating signal.
    apps = [make_app("app_a", school_id="sch_01")]
    events = {"app_a": [make_event("evt_1", "app_a", "email_bounced", "2026-06-15T00:00:00Z")]}
    routes = {"sch_01": make_route("sch_01", status="active")}

    flags = evaluate(apps, events, routes, now)

    assert ReasonCode.BOUNCED_ROUTE.value in flags["app_a"]["reason_codes"]


def test_active_route_no_bounce_event_not_flagged(now):
    apps = [make_app("app_a", school_id="sch_01")]
    routes = {"sch_01": make_route("sch_01", status="active")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.BOUNCED_ROUTE.value not in flags["app_a"]["reason_codes"]


def test_unknown_school_id_routes_to_human_review(now):
    apps = [make_app("app_a", school_id="sch_does_not_exist")]
    routes = {"sch_01": make_route("sch_01", status="active")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.UNKNOWN_SCHOOL_ROUTE.value in flags["app_a"]["reason_codes"]
    assert flags["app_a"]["needs_human_review"] is True
    # An unknown route is a data problem, not necessarily a bounce --
    # don't conflate the two reason codes.
    assert ReasonCode.BOUNCED_ROUTE.value not in flags["app_a"]["reason_codes"]
