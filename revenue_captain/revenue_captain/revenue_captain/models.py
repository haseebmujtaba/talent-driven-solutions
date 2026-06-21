"""
Core state model for Revenue Captain.

An Application is the durable unit of state. Everything else (events,
school routes) either feeds into an Application's derived fields or is
looked up alongside it when building the next-action queue.

Design note: status is the *source-of-truth* lifecycle field (set by the
input data / upstream system). reason_codes, duplicate_of, and
needs_human_review are *derived* fields recomputed fresh on every worker
run -- they are never hand-edited or incrementally patched. That split is
what makes the worker idempotent (see worker.py / README for details).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ApplicationStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    EVIDENCE_PENDING = "evidence_pending"
    EVIDENCE_COMPLETE = "evidence_complete"
    ROUTED = "routed"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

    @classmethod
    def is_closed(cls, status: str) -> bool:
        return status in (cls.CLOSED_WON.value, cls.CLOSED_LOST.value)


class RouteStatus(str, Enum):
    ACTIVE = "active"
    BOUNCED = "bounced"
    UNKNOWN = "unknown"


# Evidence types every application is expected to eventually have.
REQUIRED_EVIDENCE_TYPES = frozenset({"transcript", "essay"})

# Reason codes the rules engine can attach to an application.
class ReasonCode(str, Enum):
    STALE = "STALE"
    DUPLICATE_APPLICANT = "DUPLICATE_APPLICANT"
    POSSIBLE_DUPLICATE_NAME_MATCH = "POSSIBLE_DUPLICATE_NAME_MATCH"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    BOUNCED_ROUTE = "BOUNCED_ROUTE"
    UNKNOWN_SCHOOL_ROUTE = "UNKNOWN_SCHOOL_ROUTE"
    MANUAL_FLAG_FOR_REVIEW = "MANUAL_FLAG_FOR_REVIEW"

    # Reason codes that, if present, force a human-review queue entry
    # regardless of anything else.
    @classmethod
    def human_review_codes(cls) -> frozenset[str]:
        return frozenset(
            {
                cls.POSSIBLE_DUPLICATE_NAME_MATCH.value,
                cls.UNKNOWN_SCHOOL_ROUTE.value,
                cls.MANUAL_FLAG_FOR_REVIEW.value,
            }
        )


@dataclass
class EvidenceItem:
    type: str
    received_at: Optional[str] = None


@dataclass
class Application:
    id: str
    name: str
    email: str
    school_id: str
    status: str
    created_at: str
    updated_at: str
    evidence: list[EvidenceItem] = field(default_factory=list)


@dataclass
class Event:
    id: str
    application_id: str
    type: str
    timestamp: str
    payload: dict = field(default_factory=dict)


@dataclass
class SchoolRoute:
    school_id: str
    contact_email: str
    status: str
    last_checked_at: Optional[str] = None


@dataclass
class QueueItem:
    application_id: str
    action: str
    priority_score: float
    reason_codes: list[str]


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())
