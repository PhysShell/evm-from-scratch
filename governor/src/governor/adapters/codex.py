"""Codex evidence adapter.

Trigger: an issue comment with the exact body ``@codex review``.

Documented behaviour (learn.chatgpt.com/docs/third-party/github, fetched
2026-08-21): Codex acknowledges with an "eyes" reaction and "posts a review"
— a standard pull-request review with inline comments, restricted to P0/P1
issues. The docs do **not** document the clean-case carrier, the posting bot
account, or behaviour across head changes.

Empirical priors (Joey-Tools/codex-review-gate v2 evidence-authority
contract; not yet re-observed in this repository — every item below is
EMPIRICALLY-UNVERIFIED here until the pilot captures it):

* actor: ``chatgpt-codex-connector[bot]`` id 199175422;
* terminal carriers: a pull-request review or a terminal issue comment;
* clean case: a ``+1`` reaction on the triggering comment;
* no-start case: one of two exact issue-comment bodies (NO_START_BODIES);
* an "eyes" reaction is liveness only and vetoes an earlier +1.

Everything unrecognized is MALFORMED_EVIDENCE — never CLEAN.
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
    RejectionReason,
)
from .common import AdmissionContext, ClassificationResult, check_actor, check_timing

TRIGGER_BODY = "@codex review"

#: Exact no-start bodies, from the prior-art contract (empirically-unverified
#: in this repository). Anything else is not accepted as "unavailable".
NO_START_BODIES = (
    "To use Codex here, [create an environment for this repo]"
    "(https://chatgpt.com/codex/cloud/settings/environments).",
    "To use Codex here, [create a Codex account and connect to github]"
    "(https://chatgpt.com/codex/cloud/settings/connectors).",
)

#: Conservative clean-body recognizer for a review payload with zero inline
#: comments. UNVERIFIED — the pilot must confirm whether Codex ever posts a
#: clean review payload at all (the expected clean carrier is the +1
#: reaction).
_CLEAN_BODY_RE = re.compile(
    r"(didn'?t find any (major )?issues|no (major |blocking )?issues found)",
    re.IGNORECASE,
)


def classify_review(
    payload: dict,
    ctx: AdmissionContext,
    inline_comment_count: Optional[int] = None,
    raw_ref: str = "",
) -> ClassificationResult:
    """Classify a submitted pull-request review authored by Codex.

    ``commit_id`` is GitHub's own field for "the SHA of the commit that
    needs a review"; it is set at review creation. It is the strongest
    machine-readable head binding available for this carrier, but it is not
    a provider attestation of what was analysed — a mismatch is disqualifying,
    a match is necessary rather than sufficient.
    """
    rej = check_actor(Provider.CODEX, payload.get("user"))
    if rej:
        return None, Rejection(rej.provider, rej.reason, rej.detail, payload.get("id"))
    created = payload.get("submitted_at") or payload.get("created_at")
    rej = check_timing(Provider.CODEX, ctx, created, payload.get("id"))
    if rej:
        return None, rej

    commit_id = payload.get("commit_id")
    state = (payload.get("state") or "").upper()
    body = payload.get("body") or ""

    if commit_id != ctx.epoch.head_sha:
        classification = ProviderState.STALE
        detail = (
            f"review commit_id {commit_id} does not match epoch head "
            f"{ctx.epoch.head_sha}"
        )
    elif state == "CHANGES_REQUESTED":
        classification = ProviderState.FINDINGS
        detail = "review state CHANGES_REQUESTED"
    elif inline_comment_count and inline_comment_count > 0:
        classification = ProviderState.FINDINGS
        detail = f"review carries {inline_comment_count} inline comment(s)"
    elif state == "APPROVED" and not inline_comment_count:
        classification = ProviderState.CLEAN
        detail = "APPROVED review with no inline comments (UNVERIFIED shape)"
    elif state == "COMMENTED" and not inline_comment_count and _CLEAN_BODY_RE.search(body):
        classification = ProviderState.CLEAN
        detail = "COMMENTED review, zero inline comments, clean body (UNVERIFIED shape)"
    else:
        classification = ProviderState.MALFORMED_EVIDENCE
        detail = (
            f"unrecognized review shape: state={state!r}, "
            f"inline_comment_count={inline_comment_count!r}"
        )

    return (
        Evidence(
            provider=Provider.CODEX,
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
    """Classify a Codex-authored inline review comment.

    Codex has no structured finding count; its inline comments *are* the
    findings, so each admitted one is terminal FINDINGS evidence. The
    comment's ``commit_id`` (the SHA it anchors to) provides the head
    binding; a mismatch classifies as STALE.
    """
    rej = check_actor(Provider.CODEX, payload.get("user"))
    if rej:
        return None, Rejection(rej.provider, rej.reason, rej.detail, payload.get("id"))
    rej = check_timing(Provider.CODEX, ctx, payload.get("created_at"), payload.get("id"))
    if rej:
        return None, rej

    commit_id = payload.get("commit_id")
    if commit_id is not None and commit_id != ctx.epoch.head_sha:
        classification = ProviderState.STALE
        detail = (
            f"inline comment anchored to {commit_id}, epoch head is "
            f"{ctx.epoch.head_sha}"
        )
    else:
        classification = ProviderState.FINDINGS
        detail = "inline review comment (Codex posts only P0/P1 findings)"

    return (
        Evidence(
            provider=Provider.CODEX,
            carrier=Carrier.REVIEW_COMMENT,
            carrier_id=payload.get("id", 0),
            actor_id=payload["user"]["id"],
            actor_login=payload["user"].get("login", ""),
            created_at=payload["created_at"],
            classification=classification,
            role=EvidenceRole.TERMINAL,
            detail=detail,
            bound_sha=commit_id,
            sha_explicit=commit_id is not None,
            raw_ref=raw_ref,
        ),
        None,
    )


def classify_issue_comment(
    payload: dict, ctx: AdmissionContext, raw_ref: str = ""
) -> ClassificationResult:
    """Classify a Codex-authored issue comment on the PR."""
    rej = check_actor(Provider.CODEX, payload.get("user"))
    if rej:
        return None, Rejection(rej.provider, rej.reason, rej.detail, payload.get("id"))
    rej = check_timing(Provider.CODEX, ctx, payload.get("created_at"), payload.get("id"))
    if rej:
        return None, rej

    body = (payload.get("body") or "").strip()
    if body in NO_START_BODIES:
        classification = ProviderState.UNAVAILABLE
        role = EvidenceRole.TERMINAL
        detail = "exact no-start body (provider cannot run here)"
    else:
        classification = ProviderState.MALFORMED_EVIDENCE
        role = EvidenceRole.TERMINAL
        detail = "unrecognized Codex issue-comment shape"

    return (
        Evidence(
            provider=Provider.CODEX,
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
