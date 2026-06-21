from __future__ import annotations

from revenue_captain.models import ReasonCode
from revenue_captain.rules import evaluate

from .conftest import make_app, make_route


def test_exact_email_duplicate_flags_later_record_only(now):
    apps = [
        make_app("app_a", name="Maria Lopez", email="maria@example.com", created_at="2026-06-01T00:00:00Z"),
        make_app("app_b", name="Maria Lopez", email="maria@example.com", created_at="2026-06-05T00:00:00Z"),
    ]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert ReasonCode.DUPLICATE_APPLICANT.value not in flags["app_a"]["reason_codes"]
    assert flags["app_a"]["duplicate_of"] is None

    assert ReasonCode.DUPLICATE_APPLICANT.value in flags["app_b"]["reason_codes"]
    assert flags["app_b"]["duplicate_of"] == "app_a"
    assert flags["app_b"]["needs_human_review"] is False


def test_three_way_duplicate_all_link_to_earliest(now):
    apps = [
        make_app("app_a", email="x@example.com", created_at="2026-06-03T00:00:00Z"),
        make_app("app_b", email="x@example.com", created_at="2026-06-01T00:00:00Z"),  # earliest
        make_app("app_c", email="x@example.com", created_at="2026-06-05T00:00:00Z"),
    ]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert flags["app_b"]["duplicate_of"] is None
    assert flags["app_a"]["duplicate_of"] == "app_b"
    assert flags["app_c"]["duplicate_of"] == "app_b"


def test_different_email_same_name_is_human_review_not_auto_duplicate(now):
    apps = [
        make_app("app_a", name="Maria Lopez", email="maria.lopez@example.com", created_at="2026-06-01T00:00:00Z"),
        make_app("app_b", name="Maria Lopez", email="m.lopez@example.com", created_at="2026-06-02T00:00:00Z"),
    ]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    for app_id in ("app_a", "app_b"):
        assert ReasonCode.DUPLICATE_APPLICANT.value not in flags[app_id]["reason_codes"]
        assert ReasonCode.POSSIBLE_DUPLICATE_NAME_MATCH.value in flags[app_id]["reason_codes"]
        assert flags[app_id]["needs_human_review"] is True
        assert flags[app_id]["duplicate_of"] is None


def test_case_and_whitespace_insensitive_email_matching(now):
    apps = [
        make_app("app_a", email="Maria.Lopez@Example.com", created_at="2026-06-01T00:00:00Z"),
        make_app("app_b", email="  maria.lopez@example.com  ", created_at="2026-06-02T00:00:00Z"),
    ]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    assert flags["app_b"]["duplicate_of"] == "app_a"


def test_distinct_email_and_name_no_duplicate_flags(now):
    apps = [
        make_app("app_a", name="Maria Lopez", email="maria@example.com", created_at="2026-06-01T00:00:00Z"),
        make_app("app_b", name="James Chen", email="james@example.com", created_at="2026-06-02T00:00:00Z"),
    ]
    routes = {"sch_01": make_route("sch_01")}

    flags = evaluate(apps, {}, routes, now)

    for app_id in ("app_a", "app_b"):
        assert flags[app_id]["reason_codes"] == [] or ReasonCode.DUPLICATE_APPLICANT.value not in flags[app_id]["reason_codes"]
