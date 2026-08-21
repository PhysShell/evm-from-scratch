"""Core vocabulary of the AI final-review shadow governor.

Everything here is provider-neutral. No emoji, no Markdown phrases, no
provider-specific carrier shapes — those live in adapters, which normalize
raw GitHub artifacts into this vocabulary.

Design rule (fail-closed): every state that is not an explicit, evidence-backed
CLEAN must reduce to "not clean". Absence of evidence, timeouts, rate limits,
malformed artifacts and stale bindings are all distinct states so the shadow
check can display *why* the round is not clean, but none of them may ever
satisfy the gate.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


class Provider(str, enum.Enum):
    CODEX = "codex"
    CODERABBIT = "coderabbit"


class ProviderState(str, enum.Enum):
    """Normalized per-provider result state for one review round."""

    PENDING = "PENDING"
    CLEAN = "CLEAN"
    FINDINGS = "FINDINGS"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    MALFORMED_EVIDENCE = "MALFORMED_EVIDENCE"
    INCONCLUSIVE = "INCONCLUSIVE"
    STALE = "STALE"


#: Provider states that terminate a round for that provider.
TERMINAL_PROVIDER_STATES = frozenset(
    {
        ProviderState.CLEAN,
        ProviderState.FINDINGS,
        ProviderState.RATE_LIMITED,
        ProviderState.UNAVAILABLE,
        ProviderState.MALFORMED_EVIDENCE,
    }
)


class Verdict(str, enum.Enum):
    """Shadow verdict for one review epoch."""

    CLEAN = "CLEAN"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"
    STALE = "STALE"


class EpochState(str, enum.Enum):
    ACTIVE = "ACTIVE"
    #: A newer head SHA exists; every provider reply for this epoch is audit
    #: evidence only and must never make the new head clean.
    STALE = "STALE"
    #: A newer generation exists for the same head (label re-added). The old
    #: round's request comments no longer accept new bindings.
    SUPERSEDED = "SUPERSEDED"


class RequestState(str, enum.Enum):
    #: Intent persisted; the POST has not been confirmed either way yet.
    REQUEST_PENDING = "REQUEST_PENDING"
    #: The provider trigger comment exists and its ID is recorded.
    REQUEST_BOUND = "REQUEST_BOUND"
    #: The POST was attempted but the response was lost. The comment may or
    #: may not exist. Never retried automatically; only reconciliation against
    #: a complete comment listing may move it to BOUND or FAILED.
    REQUEST_OUTCOME_UNKNOWN = "REQUEST_OUTCOME_UNKNOWN"
    #: Proven not created (definite error response, or complete listing shows
    #: no matching comment after the reconciliation window).
    REQUEST_FAILED = "REQUEST_FAILED"


class Carrier(str, enum.Enum):
    """GitHub artifact kind that carried a piece of provider evidence."""

    PULL_REQUEST_REVIEW = "pull_request_review"
    ISSUE_COMMENT = "issue_comment"
    REVIEW_COMMENT = "review_comment"
    REACTION = "reaction"


class EvidenceRole(str, enum.Enum):
    #: Terminal authority candidate — participates in provider-state selection.
    TERMINAL = "terminal"
    #: Liveness/acknowledgement only (e.g. an "eyes" reaction, a "review
    #: triggered" reply). Never terminal, but recorded and usable as a veto.
    ACK = "ack"
    #: Informational output that is part of a review run but carries no
    #: parseable outcome on its own (e.g. a walkthrough summary comment).
    INFORMATIONAL = "informational"


class RejectionReason(str, enum.Enum):
    ACTOR_MISMATCH = "ACTOR_MISMATCH"
    BEFORE_REQUEST = "BEFORE_REQUEST"
    WRONG_REQUEST_COMMENT = "WRONG_REQUEST_COMMENT"
    NOT_CURRENT_GENERATION = "NOT_CURRENT_GENERATION"
    UNKNOWN_SHAPE = "UNKNOWN_SHAPE"


def parse_ts(value: str) -> datetime:
    """Parse a GitHub ISO-8601 timestamp ('2026-08-20T02:49:12Z')."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def iso_now(dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ReviewEpoch:
    """One review round scope: a specific PR head at a specific generation.

    Invariant: provider evidence bound to SHA A must never make SHA B clean.
    The epoch is the unit that enforces it — evidence is admitted to an epoch,
    and the verdict for an epoch is only meaningful while the PR head still
    equals ``head_sha``.
    """

    epoch_id: int
    repository_id: int
    pr_number: int
    head_sha: str
    base_sha: str
    generation: int
    state: EpochState
    requested_at: str


@dataclass
class ProviderRun:
    """One provider's request/response lifecycle inside one epoch."""

    run_id: int
    epoch_id: int
    provider: Provider
    generation: int
    request_state: RequestState
    request_comment_id: Optional[int] = None
    requested_at: Optional[str] = None
    result_state: ProviderState = ProviderState.PENDING


@dataclass(frozen=True)
class Evidence:
    """A single normalized provider artifact admitted to a run.

    ``bound_sha`` is the SHA the artifact explicitly claims (for a PR review,
    GitHub's ``commit_id``). ``sha_explicit`` distinguishes "the carrier said
    sha X" from "the carrier has no SHA field at all" — the two must never be
    conflated, because only explicit bindings can support CLEAN.
    """

    provider: Provider
    carrier: Carrier
    carrier_id: int
    actor_id: int
    actor_login: str
    created_at: str
    classification: ProviderState
    role: EvidenceRole
    detail: str
    bound_sha: Optional[str] = None
    sha_explicit: bool = False
    raw_ref: str = ""

    def to_dict(self) -> dict:
        return {
            "provider": self.provider.value,
            "carrier": self.carrier.value,
            "carrier_id": self.carrier_id,
            "actor_id": self.actor_id,
            "actor_login": self.actor_login,
            "created_at": self.created_at,
            "classification": self.classification.value,
            "role": self.role.value,
            "detail": self.detail,
            "bound_sha": self.bound_sha,
            "sha_explicit": self.sha_explicit,
            "raw_ref": self.raw_ref,
        }


@dataclass(frozen=True)
class Rejection:
    """A provider-shaped artifact the adapter refused to admit."""

    provider: Provider
    reason: RejectionReason
    detail: str
    carrier_id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "provider": self.provider.value,
            "reason": self.reason.value,
            "detail": self.detail,
            "carrier_id": self.carrier_id,
        }


@dataclass(frozen=True)
class PRSnapshot:
    """The freshly-read PR state a round is anchored to."""

    repository_id: int
    pr_number: int
    head_sha: str
    base_sha: str


@dataclass
class ProviderResolution:
    state: ProviderState
    reason: str
    #: Evidence item that decided the state, if any.
    deciding: Optional[Evidence] = None


@dataclass
class VerdictResult:
    verdict: Verdict
    reason: str
    codex_state: ProviderState = ProviderState.PENDING
    coderabbit_state: ProviderState = ProviderState.PENDING
