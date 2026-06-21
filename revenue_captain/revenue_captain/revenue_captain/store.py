"""
Durable state store, backed by SQLite.

Two kinds of tables live here:

1. SOURCE tables (applications, evidence, events_seen, school_routes) --
   these hold normalized copies of whatever was in the input JSON files.
   They are written with upserts keyed by a stable id, so re-ingesting
   the same file twice (or a file with a few new rows appended) never
   creates duplicate rows and never loses data.

2. DERIVED tables (application_flags, next_action_queue) -- these hold
   the *output* of the rules engine. They are fully recomputed and
   rewritten (inside a single transaction) on every worker run. They are
   never incrementally patched. That is the core idempotency mechanism:
   derived state is a pure function of source state, recomputed from
   scratch each time, so running the worker N times in a row produces
   byte-identical derived tables after the first run.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Iterator

from .models import (
    Application,
    Event,
    EvidenceItem,
    QueueItem,
    SchoolRoute,
    normalize_email,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    email_normalized TEXT NOT NULL,
    school_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    application_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    received_at TEXT,
    PRIMARY KEY (application_id, evidence_type)
);

CREATE TABLE IF NOT EXISTS events_seen (
    event_id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS school_routes (
    school_id TEXT PRIMARY KEY,
    contact_email TEXT NOT NULL,
    status TEXT NOT NULL,
    last_checked_at TEXT
);

CREATE TABLE IF NOT EXISTS application_flags (
    application_id TEXT PRIMARY KEY,
    last_activity_at TEXT,
    reason_codes_json TEXT NOT NULL DEFAULT '[]',
    duplicate_of TEXT,
    needs_human_review INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS next_action_queue (
    rank INTEGER NOT NULL,
    application_id TEXT NOT NULL,
    action TEXT NOT NULL,
    priority_score REAL NOT NULL,
    reason_codes_json TEXT NOT NULL DEFAULT '[]'
);
"""


class Store:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # ---------------------------------------------------------------
    # Upserts for source data. Each one is keyed by a stable id so
    # re-running ingestion with the same (or extended) input is safe.
    # ---------------------------------------------------------------

    def upsert_applications(self, applications: Iterable[Application]) -> None:
        with self.transaction() as conn:
            for app in applications:
                conn.execute(
                    """
                    INSERT INTO applications
                        (id, name, email, email_normalized, school_id, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        email=excluded.email,
                        email_normalized=excluded.email_normalized,
                        school_id=excluded.school_id,
                        status=excluded.status,
                        created_at=excluded.created_at,
                        updated_at=excluded.updated_at
                    """,
                    (
                        app.id,
                        app.name,
                        app.email,
                        normalize_email(app.email),
                        app.school_id,
                        app.status,
                        app.created_at,
                        app.updated_at,
                    ),
                )
                for ev in app.evidence:
                    conn.execute(
                        """
                        INSERT INTO evidence (application_id, evidence_type, received_at)
                        VALUES (?, ?, ?)
                        ON CONFLICT(application_id, evidence_type) DO UPDATE SET
                            received_at=excluded.received_at
                        """,
                        (app.id, ev.type, ev.received_at),
                    )

    def upsert_events(self, events: Iterable[Event]) -> None:
        with self.transaction() as conn:
            for ev in events:
                conn.execute(
                    """
                    INSERT INTO events_seen (event_id, application_id, type, timestamp, payload_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        application_id=excluded.application_id,
                        type=excluded.type,
                        timestamp=excluded.timestamp,
                        payload_json=excluded.payload_json
                    """,
                    (ev.id, ev.application_id, ev.type, ev.timestamp, json.dumps(ev.payload, sort_keys=True)),
                )

    def upsert_school_routes(self, routes: Iterable[SchoolRoute]) -> None:
        with self.transaction() as conn:
            for r in routes:
                conn.execute(
                    """
                    INSERT INTO school_routes (school_id, contact_email, status, last_checked_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(school_id) DO UPDATE SET
                        contact_email=excluded.contact_email,
                        status=excluded.status,
                        last_checked_at=excluded.last_checked_at
                    """,
                    (r.school_id, r.contact_email, r.status, r.last_checked_at),
                )

    # ---------------------------------------------------------------
    # Readers used by the rules engine to build derived state.
    # ---------------------------------------------------------------

    def all_applications(self) -> list[Application]:
        cur = self.conn.execute(
            "SELECT id, name, email, school_id, status, created_at, updated_at FROM applications"
        )
        apps = []
        for row in cur.fetchall():
            app = Application(*row)
            ev_cur = self.conn.execute(
                "SELECT evidence_type, received_at FROM evidence WHERE application_id = ?",
                (app.id,),
            )
            app.evidence = [EvidenceItem(t, r) for t, r in ev_cur.fetchall()]
            apps.append(app)
        return apps

    def events_for_application(self, application_id: str) -> list[Event]:
        cur = self.conn.execute(
            """
            SELECT event_id, application_id, type, timestamp, payload_json
            FROM events_seen WHERE application_id = ? ORDER BY timestamp ASC
            """,
            (application_id,),
        )
        return [
            Event(eid, aid, typ, ts, json.loads(payload))
            for eid, aid, typ, ts, payload in cur.fetchall()
        ]

    def all_events_by_application(self) -> dict[str, list[Event]]:
        cur = self.conn.execute(
            """
            SELECT event_id, application_id, type, timestamp, payload_json
            FROM events_seen ORDER BY application_id, timestamp ASC
            """
        )
        out: dict[str, list[Event]] = {}
        for eid, aid, typ, ts, payload in cur.fetchall():
            out.setdefault(aid, []).append(Event(eid, aid, typ, ts, json.loads(payload)))
        return out

    def all_school_routes(self) -> dict[str, SchoolRoute]:
        cur = self.conn.execute(
            "SELECT school_id, contact_email, status, last_checked_at FROM school_routes"
        )
        return {row[0]: SchoolRoute(*row) for row in cur.fetchall()}

    # ---------------------------------------------------------------
    # Derived-state writers. ALWAYS a full delete + reinsert inside one
    # transaction -- never an incremental patch. This is what makes
    # re-running the rules engine idempotent regardless of how many
    # times it has run before.
    # ---------------------------------------------------------------

    def replace_application_flags(self, flags: Iterable[dict]) -> None:
        with self.transaction() as conn:
            conn.execute("DELETE FROM application_flags")
            for f in flags:
                conn.execute(
                    """
                    INSERT INTO application_flags
                        (application_id, last_activity_at, reason_codes_json, duplicate_of, needs_human_review)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        f["application_id"],
                        f["last_activity_at"],
                        json.dumps(f["reason_codes"]),
                        f["duplicate_of"],
                        1 if f["needs_human_review"] else 0,
                    ),
                )

    def replace_queue(self, items: list[QueueItem]) -> None:
        with self.transaction() as conn:
            conn.execute("DELETE FROM next_action_queue")
            for rank, item in enumerate(items, start=1):
                conn.execute(
                    """
                    INSERT INTO next_action_queue
                        (rank, application_id, action, priority_score, reason_codes_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        rank,
                        item.application_id,
                        item.action,
                        item.priority_score,
                        json.dumps(item.reason_codes),
                    ),
                )

    def get_queue(self) -> list[dict]:
        cur = self.conn.execute(
            """
            SELECT rank, application_id, action, priority_score, reason_codes_json
            FROM next_action_queue ORDER BY rank ASC
            """
        )
        return [
            {
                "rank": rank,
                "application_id": aid,
                "action": action,
                "priority_score": score,
                "reason_codes": json.loads(reasons),
            }
            for rank, aid, action, score, reasons in cur.fetchall()
        ]

    def get_flags(self) -> dict[str, dict]:
        cur = self.conn.execute(
            """
            SELECT application_id, last_activity_at, reason_codes_json, duplicate_of, needs_human_review
            FROM application_flags
            """
        )
        return {
            aid: {
                "last_activity_at": last_activity,
                "reason_codes": json.loads(reasons),
                "duplicate_of": dup,
                "needs_human_review": bool(review),
            }
            for aid, last_activity, reasons, dup, review in cur.fetchall()
        }
