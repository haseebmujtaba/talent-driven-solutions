"""
Ingestion: turn raw JSON (whatever shape the upstream system hands us)
into the normalized model objects defined in models.py.

This is the one place in the codebase that should know about the raw
JSON field names from applications.json / events.json / school_routes.json.
Everything downstream works with Application / Event / SchoolRoute
dataclasses, not dicts -- that boundary keeps the rules engine and
queue builder decoupled from upstream schema drift.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Application, Event, EvidenceItem, SchoolRoute


def _read_json(path: str | Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        # Tolerate a top-level {"applications": [...]} wrapper as well
        # as a bare list, since real-world export formats vary.
        for key in ("applications", "events", "school_routes", "routes", "items", "data"):
            if key in data:
                return data[key]
        raise ValueError(f"Could not find a list of records in {path}")
    return data


def load_applications(path: str | Path) -> list[Application]:
    apps = []
    for row in _read_json(path):
        evidence = [
            EvidenceItem(type=e["type"], received_at=e.get("received_at"))
            for e in row.get("evidence", [])
        ]
        apps.append(
            Application(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                school_id=row["school_id"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row.get("updated_at", row["created_at"]),
                evidence=evidence,
            )
        )
    return apps


def load_events(path: str | Path) -> list[Event]:
    events = []
    for row in _read_json(path):
        events.append(
            Event(
                id=row["id"],
                application_id=row["application_id"],
                type=row["type"],
                timestamp=row["timestamp"],
                payload=row.get("payload", {}),
            )
        )
    return events


def load_school_routes(path: str | Path) -> list[SchoolRoute]:
    routes = []
    for row in _read_json(path):
        routes.append(
            SchoolRoute(
                school_id=row["school_id"],
                contact_email=row["contact_email"],
                status=row["status"],
                last_checked_at=row.get("last_checked_at"),
            )
        )
    return routes
