from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from revenue_captain import worker

DATA_DIR = Path(__file__).parent.parent / "data"
FIXED_NOW = "2026-06-21T00:00:00Z"


def _run(db_path, applications=None, events=None, routes=None):
    worker.main(
        [
            "run",
            "--applications", str(applications or DATA_DIR / "applications.json"),
            "--events", str(events or DATA_DIR / "events.json"),
            "--school-routes", str(routes or DATA_DIR / "school_routes.json"),
            "--db", str(db_path),
            "--now", FIXED_NOW,
            "--quiet",
        ]
    )


def _table_counts(db_path):
    conn = sqlite3.connect(db_path)
    try:
        tables = ["applications", "evidence", "events_seen", "school_routes", "application_flags", "next_action_queue"]
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
    finally:
        conn.close()


def _queue_snapshot(db_path):
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT rank, application_id, action, priority_score, reason_codes_json FROM next_action_queue ORDER BY rank"
        ).fetchall()
        return rows
    finally:
        conn.close()


def test_rerun_with_identical_inputs_is_a_no_op(tmp_path):
    db_path = tmp_path / "state.db"

    _run(db_path)
    counts_after_first = _table_counts(db_path)
    queue_after_first = _queue_snapshot(db_path)

    _run(db_path)
    counts_after_second = _table_counts(db_path)
    queue_after_second = _queue_snapshot(db_path)

    assert counts_after_first == counts_after_second
    assert queue_after_first == queue_after_second


def test_rerun_many_times_stays_stable(tmp_path):
    db_path = tmp_path / "state.db"

    for _ in range(5):
        _run(db_path)

    counts = _table_counts(db_path)
    queue = _queue_snapshot(db_path)

    _run(db_path)
    assert _table_counts(db_path) == counts
    assert _queue_snapshot(db_path) == queue


def test_reingesting_same_application_with_updated_fields_does_not_duplicate_row(tmp_path):
    db_path = tmp_path / "state.db"
    apps_path = tmp_path / "applications.json"
    events_path = tmp_path / "events.json"
    routes_path = tmp_path / "school_routes.json"

    base_app = {
        "id": "app_solo",
        "name": "Solo Person",
        "email": "solo@example.com",
        "school_id": "sch_01",
        "status": "contacted",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "evidence": [],
    }
    routes = [{"school_id": "sch_01", "contact_email": "a@sch01.edu", "status": "active", "last_checked_at": "2026-06-01T00:00:00Z"}]

    apps_path.write_text(json.dumps([base_app]))
    events_path.write_text(json.dumps([]))
    routes_path.write_text(json.dumps(routes))

    _run(db_path, applications=apps_path, events=events_path, routes=routes_path)
    assert _table_counts(db_path)["applications"] == 1

    # "Re-export" the same application with a status change -- this
    # simulates the upstream system re-sending a record that changed.
    updated_app = dict(base_app, status="evidence_pending", updated_at="2026-06-10T00:00:00Z")
    apps_path.write_text(json.dumps([updated_app]))

    _run(db_path, applications=apps_path, events=events_path, routes=routes_path)
    counts = _table_counts(db_path)
    assert counts["applications"] == 1  # still one row, not two

    conn = sqlite3.connect(db_path)
    try:
        status = conn.execute("SELECT status FROM applications WHERE id = 'app_solo'").fetchone()[0]
    finally:
        conn.close()
    assert status == "evidence_pending"


def test_appending_a_new_event_only_adds_that_event_on_rerun(tmp_path):
    db_path = tmp_path / "state.db"
    apps_path = tmp_path / "applications.json"
    events_path = tmp_path / "events.json"
    routes_path = tmp_path / "school_routes.json"

    apps_path.write_text(json.dumps([
        {
            "id": "app_solo",
            "name": "Solo Person",
            "email": "solo@example.com",
            "school_id": "sch_01",
            "status": "contacted",
            "created_at": "2026-06-01T00:00:00Z",
            "updated_at": "2026-06-01T00:00:00Z",
            "evidence": [],
        }
    ]))
    routes_path.write_text(json.dumps([
        {"school_id": "sch_01", "contact_email": "a@sch01.edu", "status": "active", "last_checked_at": "2026-06-01T00:00:00Z"}
    ]))

    first_events = [{"id": "evt_a", "application_id": "app_solo", "type": "email_sent", "timestamp": "2026-06-01T00:05:00Z"}]
    events_path.write_text(json.dumps(first_events))

    _run(db_path, applications=apps_path, events=events_path, routes=routes_path)
    assert _table_counts(db_path)["events_seen"] == 1

    # Re-run with the exact same file: count must not change.
    _run(db_path, applications=apps_path, events=events_path, routes=routes_path)
    assert _table_counts(db_path)["events_seen"] == 1

    # Append a genuinely new event and re-run: count should grow by
    # exactly one, not duplicate the original.
    second_events = first_events + [
        {"id": "evt_b", "application_id": "app_solo", "type": "call_logged", "timestamp": "2026-06-15T00:00:00Z"}
    ]
    events_path.write_text(json.dumps(second_events))

    _run(db_path, applications=apps_path, events=events_path, routes=routes_path)
    assert _table_counts(db_path)["events_seen"] == 2


def test_queue_output_is_deterministically_ordered_across_runs(tmp_path):
    db_path_a = tmp_path / "a.db"
    db_path_b = tmp_path / "b.db"

    _run(db_path_a)
    _run(db_path_b)

    assert _queue_snapshot(db_path_a) == _queue_snapshot(db_path_b)
