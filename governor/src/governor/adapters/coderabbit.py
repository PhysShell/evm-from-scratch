"""CodeRabbit evidence adapter.

Trigger: an issue comment with the exact body ``@coderabbitai full review``.
``full review`` re-reviews the whole PR from scratch; the final round must
re-evaluate the entire PR, not the incremental diff (docs.coderabbit.ai,
fetched 2026-08-21).

Observed in this repository before the pilot (PR #2/#7/#8/#10):

* actor ``coderabbitai[bot]`` id 136622811;
* auto-review is disabled ("fewer than 10 stars"), so a manual trigger is
  the only path;
* an on-PR-open placeholder comment ("Review available on request" /
  "Trigger review") that CodeRabbit later *edits in place*;
* plan "Pro Plus" (10 PR reviews per hour per docs).

NOT yet observed here (EMPIRICALLY-UNVERIFIED until the pilot): the
completion carrier for a manual full review, the "Actionable comments
posted: N" marker, ack/rate-limit/failure texts, and whether any check run
or commit status is produced. The recognizers below encode the expected
shapes; the phrase "Full review finished" alone is deliberately NOT a clean
signal — it reports command completion, not absence of findings.
"""

from __future__ import annotations

import re
from typing import Optional

from ..model import (
    Carrier,
    Evidence,
    EvidenceRole,
    Provider,
    ProviderState,
    Rejection,
)
from .common import AdmissionContext, ClassificationResult, check_actor, check_timing

TRIGGER_BODY = "@coderabbitai full review"

#: The authority marker for review outcome. N==0 is the only comment/review
#: text that may support CLEAN, and only from a carrier bound to the epoch
#: head.
_ACTIONABLE_RE = re.compile(r"Actionable comments posted:\s*(\d+)")

_RATE_LIMIT_RE = re.compile(r"rate.?limit", re.IGNORECASE)
# "Action performed" observed singular on PR #11 (comment 5364757871,
# 2026-08-21): "I will perform a full review of pull request `#11`. /
# Action performed / Full review triggered."
_ACK_RE = re.compile(
    r"(Full review triggered|Actions? performed|I will (perform a full review|re-?review))",
    re.IGNORECASE,
)
_PLACEHOLDER_RE = re.compile(r"(Review available on request|Trigger review)")
_WALKTHROUGH_RE = re.compile(r"#+\s*Walkthrough")
_FINISHED_RE = re.compile(r"full review (finished|completed?)", re.IGNORECASE)
_FAILURE_RE = re.compile(
    r"(encountered an error|something went wrong|review failed|unable to (process|review))",
    re.IGNORECASE,
)


def _actionable_count(body: str) -> Optional[int]:
    m = _ACTIONABLE_RE.search(body or "")
    return int(m.group(1)) if m else None


def classify_review(
    payload: dict,
    ctx: AdmissionContext,
    inline_comment_count: Optional[int] = None,
    raw_ref: str = "",
) -> ClassificationResult:
    """Classify a submitted pull-request review authored by CodeRabbit."""
    rej = check_actor(Provider.CODERABBIT, payload.get("user"))
    if rej:
        return None, Rejection(rej.provider, rej.reason, rej.detail, payload.get("id"))
    created = payload.get("submitted_at") or payload.get("created_at")
    rej = check_timing(Provider.CODERABBIT, ctx, created, payload.get("id"))
    if rej:
        return None, rej

    commit_id = payload.get("commit_id")
    state = (payload.get("state") or "").upper()
    body = payload.get("body") or ""
    count = _actionable_count(body)

    if commit_id != ctx.epoch.head_sha:
        classification = ProviderState.STALE
        detail = (
            f"review commit_id {commit_id} does not match epoch head "
            f"{ctx.epoch.head_sha}"
        )
    elif state == "CHANGES_REQUESTED":
        classification = ProviderState.FINDINGS
        detail = "review state CHANGES_REQUESTED"
    elif count is not None and count > 0:
        classification = ProviderState.FINDINGS
        detail = f"Actionable comments posted: {count}"
    elif inline_comment_count and inline_comment_count > 0:
        classification = ProviderState.FINDINGS
        detail = f"review carries {inline_comment_count} inline comment(s)"
    elif count == 0:
        classification = ProviderState.CLEAN
        detail = "Actionable comments posted: 0 (head-bound review payload)"
    else:
        classification = ProviderState.MALFORMED_EVIDENCE
        detail = (
            "review without a parseable actionable-comment count "
            f"(state={state!r})"
        )

    return (
        Evidence(
            provider=Provider.CODERABBIT,
            carrier=Carrier.PULL_REQUEST_REVIEW,
            carrier_id=payload.get("id", 0),
            actor_id=payload["user"]["id"],
            actor_login=payload["user"].get("login", ""),
            created_at=created,
            classification=classification,
            role=EvidenceRole.TERMINAL,
            detail=detail,
            bound_sha=commit_id,
            sha_explicit=commit_id is not None,
            raw_ref=raw_ref,
        ),
        None,
    )


def classify_review_comment(
    payload: dict, ctx: AdmissionContext, raw_ref: str = ""
) -> ClassificationResult:
    """Classify a CodeRabbit-authored inline review comment.

    CodeRabbit's inline comments include non-actionable material (nitpicks,
    tips), so an inline comment is **not** independent terminal evidence —
    the parent review's "Actionable comments posted: N" is the outcome
    authority. Inline comments are recorded as informational only.
    """
    rej = check_actor(Provider.CODERABBIT, payload.get("user"))
    if rej:
        return None, Rejection(rej.provider, rej.reason, rej.detail, payload.get("id"))
    rej = check_timing(
        Provider.CODERABBIT, ctx, payload.get("created_at"), payload.get("id")
    )
    if rej:
        return None, rej

    commit_id = payload.get("commit_id")
    return (
        Evidence(
            provider=Provider.CODERABBIT,
            carrier=Carrier.REVIEW_COMMENT,
            carrier_id=payload.get("id", 0),
            actor_id=payload["user"]["id"],
            actor_login=payload["user"].get("login", ""),
            created_at=payload["created_at"],
            classification=ProviderState.PENDING,
            role=EvidenceRole.INFORMATIONAL,
            detail="inline comment; outcome authority is the parent review's actionable count",
            bound_sha=commit_id,
            sha_explicit=commit_id is not None,
            raw_ref=raw_ref,
        ),
        None,
    )


def classify_issue_comment(
    payload: dict, ctx: AdmissionContext, raw_ref: str = ""
) -> ClassificationResult:
    """Classify a CodeRabbit-authored issue comment on the PR.

    A comment carries no SHA, so even a parseable "Actionable comments
    posted: 0" here cannot bind to the epoch head — it classifies as
    INCONCLUSIVE (clean text without head binding), never CLEAN.
    """
    rej = check_actor(Provider.CODERABBIT, payload.get("user"))
    if rej:
        return None, Rejection(rej.provider, rej.reason, rej.detail, payload.get("id"))
    rej = check_timing(
        Provider.CODERABBIT, ctx, payload.get("created_at"), payload.get("id")
    )
    if rej:
        return None, rej

    body = payload.get("body") or ""
    count = _actionable_count(body)
    role = EvidenceRole.TERMINAL

    if _RATE_LIMIT_RE.search(body):
        classification = ProviderState.RATE_LIMITED
        detail = "rate-limit text from provider"
    elif _FAILURE_RE.search(body):
        classification = ProviderState.UNAVAILABLE
        detail = "provider failure text"
    elif count is not None and count > 0:
        classification = ProviderState.FINDINGS
        detail = f"Actionable comments posted: {count} (comment carrier)"
    elif count == 0:
        classification = ProviderState.INCONCLUSIVE
        detail = (
            "clean-looking text without a head binding — a comment cannot "
            "prove which SHA it reviewed"
        )
    elif _ACK_RE.search(body):
        classification = ProviderState.PENDING
        role = EvidenceRole.ACK
        detail = "acknowledgement (review triggered), not a completion"
    elif _PLACEHOLDER_RE.search(body):
        classification = ProviderState.PENDING
        role = EvidenceRole.INFORMATIONAL
        detail = "manual-trigger placeholder comment"
    elif _WALKTHROUGH_RE.search(body):
        classification = ProviderState.PENDING
        role = EvidenceRole.INFORMATIONAL
        detail = "walkthrough summary (no outcome authority)"
    elif _FINISHED_RE.search(body):
        classification = ProviderState.INCONCLUSIVE
        detail = (
            "'Full review finished' reports command completion, not zero "
            "findings — never CLEAN on its own"
        )
    else:
        classification = ProviderState.MALFORMED_EVIDENCE
        detail = "unrecognized CodeRabbit issue-comment shape"

    return (
        Evidence(
            provider=Provider.CODERABBIT,
            carrier=Carrier.ISSUE_COMMENT,
            carrier_id=payload.get("id", 0),
            actor_id=payload["user"]["id"],
            actor_login=payload["user"].get("login", ""),
            created_at=payload["created_at"],
            classification=classification,
            role=role,
            detail=detail,
            bound_sha=None,
            sha_explicit=False,
            raw_ref=raw_ref,
        ),
        None,
    )
