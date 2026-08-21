"""Admission and per-provider state resolution shared by both adapters.

Admission is the trust boundary: an artifact becomes evidence only if

* its actor's **numeric** GitHub ID equals the registered provider ID
  (login is diagnostic only — spoofable in every other respect);
* it was created **strictly after** the round's request server time
  (equal-second timestamps are rejected, fail-closed);
* reaction carriers sit on **this generation's** request comment — a correct
  provider reacting to an older generation's comment is rejected for the
  current generation.

Resolution is deterministic: latest admissible terminal artifact wins, with
two safety exceptions taken from empirically-motivated prior art
(Joey-Tools/codex-review-gate v2):

* a reaction-basis CLEAN never overrides a payload FINDINGS;
* a provider "eyes" (ack/liveness) reaction at-or-after the selected "+1"
  vetoes reaction-only CLEAN — the +1 may belong to a superseded run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..identity import PROVIDER_ACTORS, is_provider_actor
from ..model import (
    Carrier,
    Evidence,
    EvidenceRole,
    Provider,
    ProviderResolution,
    ProviderRun,
    ProviderState,
    Rejection,
    RejectionReason,
    ReviewEpoch,
    parse_ts,
)


@dataclass(frozen=True)
class AdmissionContext:
    epoch: ReviewEpoch
    run: ProviderRun
    #: False when the run belongs to a superseded/stale generation and the
    #: artifact is being tested against the *current* generation.
    is_current_generation: bool = True


ClassificationResult = Tuple[Optional[Evidence], Optional[Rejection]]


def check_actor(
    provider: Provider, user: Optional[dict]
) -> Optional[Rejection]:
    user = user or {}
    actor_id = user.get("id")
    if not is_provider_actor(provider, actor_id):
        return Rejection(
            provider=provider,
            reason=RejectionReason.ACTOR_MISMATCH,
            detail=(
                f"actor id {actor_id!r} (login {user.get('login')!r}) is not the "
                f"registered id {PROVIDER_ACTORS[provider].actor_id} for {provider.value}"
            ),
        )
    return None


def check_timing(
    provider: Provider,
    ctx: AdmissionContext,
    created_at: Optional[str],
    carrier_id: Optional[int],
) -> Optional[Rejection]:
    """Artifact must be created strictly after the request was created.

    Both timestamps are GitHub server times, so they live in one clock
    domain. When the run has no bound request time (request never confirmed),
    the epoch creation time is the only available lower bound.
    """
    baseline = ctx.run.requested_at or ctx.epoch.requested_at
    if created_at is None or baseline is None:
        return Rejection(
            provider=provider,
            reason=RejectionReason.BEFORE_REQUEST,
            detail="artifact or request is missing a server timestamp",
            carrier_id=carrier_id,
        )
    if parse_ts(created_at) <= parse_ts(baseline):
        return Rejection(
            provider=provider,
            reason=RejectionReason.BEFORE_REQUEST,
            detail=f"artifact at {created_at} is not strictly after request at {baseline}",
            carrier_id=carrier_id,
        )
    return None


def classify_reaction(
    provider: Provider,
    payload: dict,
    parent_comment_id: int,
    ctx: AdmissionContext,
    raw_ref: str = "",
) -> ClassificationResult:
    """Classify a reaction on an issue comment.

    Only reactions sitting on this generation's own request comment are
    admissible. ``+1`` is the (empirically to-be-confirmed) clean signal;
    ``eyes`` is liveness/ack only.

    Reactions carry no SHA. A reaction-basis CLEAN therefore binds through
    the request-comment join plus the verdict-level requirement that the
    epoch head still equals the current PR head. GitHub has **no webhook
    event for reactions**, so this carrier is only reachable by polling.
    """
    rej = check_actor(provider, payload.get("user"))
    if rej:
        return None, Rejection(rej.provider, rej.reason, rej.detail, payload.get("id"))
    if not ctx.is_current_generation:
        return None, Rejection(
            provider,
            RejectionReason.NOT_CURRENT_GENERATION,
            f"reaction {payload.get('id')} evaluated against a non-current generation",
            payload.get("id"),
        )
    if (
        ctx.run.request_comment_id is None
        or parent_comment_id != ctx.run.request_comment_id
    ):
        return None, Rejection(
            provider,
            RejectionReason.WRONG_REQUEST_COMMENT,
            (
                f"reaction sits on comment {parent_comment_id}, current generation's "
                f"request comment is {ctx.run.request_comment_id}"
            ),
            payload.get("id"),
        )
    rej = check_timing(provider, ctx, payload.get("created_at"), payload.get("id"))
    if rej:
        return None, rej

    content = payload.get("content")
    if content == "+1":
        classification, role, detail = (
            ProviderState.CLEAN,
            EvidenceRole.TERMINAL,
            "+1 reaction on this generation's request comment",
        )
    elif content == "eyes":
        classification, role, detail = (
            ProviderState.PENDING,
            EvidenceRole.ACK,
            "eyes",
        )
    else:
        classification, role, detail = (
            ProviderState.MALFORMED_EVIDENCE,
            EvidenceRole.TERMINAL,
            f"unexpected reaction content {content!r} from provider",
        )
    return (
        Evidence(
            provider=provider,
            carrier=Carrier.REACTION,
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


def resolve_provider_state(evidences: List[Evidence]) -> ProviderResolution:
    """Reduce one run's admitted evidence to a single provider state.

    Fail-closed by construction:

    * no admissible terminal evidence → PENDING (absence is never CLEAN);
    * only stale-bound evidence → STALE;
    * **findings are sticky within a generation**: once a finding artifact
      is admitted, no later artifact of the same generation can undo it.
      A re-review is always a new generation (new label round), so a
      "later clean" inside one generation is treated as a conflict, not a
      recovery;
    * two conflicting terminal artifacts in one server second → INCONCLUSIVE;
    * a reaction-basis CLEAN is vetoed by a provider "eyes" at-or-after it —
      the +1 may belong to a superseded provider run.
    """
    terminals = [e for e in evidences if e.role == EvidenceRole.TERMINAL]
    stale = [e for e in terminals if e.classification == ProviderState.STALE]
    live = [e for e in terminals if e.classification != ProviderState.STALE]

    if not live:
        if stale:
            latest_stale = max(stale, key=_order_key)
            return ProviderResolution(
                ProviderState.STALE,
                f"only evidence bound to a superseded head ({latest_stale.bound_sha})",
                latest_stale,
            )
        return ProviderResolution(
            ProviderState.PENDING, "no admissible terminal evidence", None
        )

    findings = [e for e in live if e.classification == ProviderState.FINDINGS]
    if findings:
        deciding = max(findings, key=_order_key)
        return ProviderResolution(
            ProviderState.FINDINGS,
            f"findings are sticky within a generation: {deciding.detail}",
            deciding,
        )

    live_sorted = sorted(live, key=_order_key)
    selected = live_sorted[-1]

    # Same-server-second terminal disagreement is not decidable — fail closed.
    if len(live_sorted) >= 2:
        runner_up = live_sorted[-2]
        if (
            parse_ts(runner_up.created_at) == parse_ts(selected.created_at)
            and runner_up.classification != selected.classification
        ):
            return ProviderResolution(
                ProviderState.INCONCLUSIVE,
                "two terminal artifacts share one server timestamp with "
                f"conflicting outcomes ({runner_up.classification.value} vs "
                f"{selected.classification.value})",
                None,
            )

    if (
        selected.classification == ProviderState.CLEAN
        and selected.carrier == Carrier.REACTION
    ):
        eyes = [
            e
            for e in evidences
            if e.role == EvidenceRole.ACK
            and e.carrier == Carrier.REACTION
            and e.detail == "eyes"
            and parse_ts(e.created_at) >= parse_ts(selected.created_at)
        ]
        if eyes:
            return ProviderResolution(
                ProviderState.PENDING,
                "eyes at-or-after the +1 vetoes reaction-only clean "
                "(a newer provider run may be in progress)",
                None,
            )

    return ProviderResolution(
        selected.classification,
        f"latest terminal evidence: {selected.detail}",
        selected,
    )


def _order_key(e: Evidence):
    return (parse_ts(e.created_at), e.carrier_id)
