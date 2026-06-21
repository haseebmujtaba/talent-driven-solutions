from __future__ import annotations

from datetime import datetime, timezone

import pytest

from revenue_captain.models import Application, Event, EvidenceItem, SchoolRoute

NOW = datetime(2026, 6, 21, 0, 0, 0, tzinfo=timezone.utc)


def make_app(
    id,
    name="Test Person",
    email="test@example.com",
    school_id="sch_01",
    status="contacted",
    created_at="2026-06-01T00:00:00Z",
    updated_at=None,
    evidence=None,
):
    return Application(
        id=id,
        name=name,
        email=email,
        school_id=school_id,
        status=status,
        created_at=created_at,
        updated_at=updated_at or created_at,
        evidence=evidence or [],
    )


def make_event(id, application_id, type, timestamp, payload=None):
    return Event(id=id, application_id=application_id, type=type, timestamp=timestamp, payload=payload or {})


def make_route(school_id, status="active", contact_email=None, last_checked_at="2026-06-01T00:00:00Z"):
    return SchoolRoute(
        school_id=school_id,
        contact_email=contact_email or f"admissions@{school_id}.edu",
        status=status,
        last_checked_at=last_checked_at,
    )


@pytest.fixture
def now():
    return NOW
