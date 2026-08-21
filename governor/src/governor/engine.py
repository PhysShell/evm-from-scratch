"""The shadow governor engine: routes admitted artifacts into runs, resolves
provider states, and computes shadow verdicts.

The engine owns no network. Live transports (or a human operating the pilot
by hand) call its ``ingest_*``/``start_round``/``evaluate`` methods with raw
GitHub objects; everything downstream is deterministic and offline-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Tuple

from .adapters import codex, coderabbit
from .adapters.common import AdmissionContext, resolve_provider_state
from .identity import CODERABBIT_ACTOR_ID, CODEX_ACTOR_ID
from .model import (
    PRSnapshot,
    Provider,
    ProviderResolution,
    ProviderRun,
    ProviderState,
    ReviewEpoch,
    VerdictResult,
    iso_now,
)
from .reducer import reduce_verdict
from .store import Store
from . import trigger as trigger_mod

DEFAULT_TRIGGER_LABEL = "ai-final-review"


@dataclass(frozen=True)
class GovernorConfig:
    #: Numeric GitHub ID of the account the governor posts trigger comments
    #: as. Used to reconcile ambiguous POSTs against comment listings.
    governor_actor_id: int
    trigger_label: str = DEFAULT_TRIGGER_LABEL


class PRReader(Protocol):
    def get_pr(self, repository_id: int, pr_number: int) -> PRSnapshot:
        """Fresh PR read: current head/base SHA."""
        ...


_ADAPTERS = {
    Provider.CODEX: codex,
    Provider.CODERABBIT: coderabbit,
}

_ACTOR_TO_PROVIDER = {
    CODEX_ACTOR_ID: Provider.CODEX,
    CODERABBIT_ACTOR_ID: Provider.CODERABBIT,
}


class ShadowGovernor:
    def __init__(
        self,
        store: Store,
        config: GovernorConfig,
        transport: Optional[trigger_mod.Transport] = None,
        pr_reader: Optional[PRReader] = None,
    ):
        self.store = store
        self.config = config
        self.transport = transport
        self.pr_reader = pr_reader

    # -- round lifecycle ---------------------------------------------------

    def start_round(self, snapshot: PRSnapshot, now: Optional[str] = None) -> trigger_mod.RoundStart:
        if self.transport is None:
            raise RuntimeError("no transport bound; cannot post trigger comments")
        return trigger_mod.start_round(self.store, self.transport, snapshot, now or iso_now())

    def on_labeled(
        self, repository_id: int, pr_number: int, label_name: str, now: str
    ) -> List[str]:
        if label_name != self.config.trigger_label:
            return [f"ignored: label {label_name!r}"]
        if self.transport is None or self.pr_reader is None:
            return [
                "trigger label observed but no transport/pr_reader bound; "
                "start_round must be invoked explicitly"
            ]
        # The label event's embedded PR snapshot may lag; anchor the round to
        # a fresh read.
        snapshot = self.pr_reader.get_pr(repository_id, pr_number)
        result = self.start_round(snapshot, now)
        return [
            f"round started: epoch {result.epoch.epoch_id} generation "
            f"{result.epoch.generation} head {result.epoch.head_sha}"
        ]

    def on_synchronize(
        self,
        repository_id: int,
        pr_number: int,
        new_head_sha: str,
        new_base_sha: str,
        now: str,
    ) -> List[str]:
        """Head moved: stale the old epoch, open a successor epoch.

        The successor has no provider runs — a new external round costs
        provider quota and is only started by the explicit trigger label.
        Until then the successor's providers are PENDING and its verdict is
        INCONCLUSIVE, which is exactly "not clean".
        """
        transitions: List[str] = []
        staled = self.store.mark_stale_on_new_head(
            repository_id, pr_number, new_head_sha
        )
        if staled is not None:
            transitions.append(
                f"epoch generation {staled.generation} (head {staled.head_sha}) -> STALE"
            )
        current = self.store.current_epoch(repository_id, pr_number)
        if current is None or current.head_sha != new_head_sha:
            successor = self.store.create_epoch(
                repository_id, pr_number, new_head_sha, new_base_sha, created_at=now
            )
            transitions.append(
                f"epoch generation {successor.generation} created for head "
                f"{new_head_sha} (no round requested yet)"
            )
        if not transitions:
            transitions.append("head unchanged; no transition")
        return transitions

    # -- evidence ingestion ------------------------------------------------

    def _find_run(
        self, repository_id: int, pr_number: int, provider: Provider
    ) -> Optional[Tuple[ReviewEpoch, ProviderRun, bool]]:
        """Locate the run new evidence for ``provider`` belongs to.

        Preference order: the current epoch's run; otherwise the newest
        earlier epoch that has a run for this provider (late replies land on
        the round that requested them, which keeps them audit-attached and
        keeps them *out* of the current epoch's verdict).
        """
        current = self.store.current_epoch(repository_id, pr_number)
        if current is None:
            return None
        run = self.store.run_for(current.epoch_id, provider)
        if run is not None:
            return current, run, True
        # Walk older generations for the newest one that has a run.
        gen = current.generation - 1
        while gen >= 1:
            epoch = self.store.epoch_by_generation(repository_id, pr_number, gen)
            if epoch is None:
                break
            run = self.store.run_for(epoch.epoch_id, provider)
            if run is not None:
                return epoch, run, False
            gen -= 1
        return None

    def _ingest(
        self,
        repository_id: int,
        pr_number: int,
        provider: Provider,
        classify_name: str,
        payload: dict,
        now: str,
        raw_ref: str = "",
        **kwargs,
    ) -> List[str]:
        located = self._find_run(repository_id, pr_number, provider)
        if located is None:
            return [
                f"unsolicited {provider.value} artifact: no run has ever been "
                "requested for this PR; recorded nowhere, contributes nothing"
            ]
        epoch, run, is_current = located
        ctx = AdmissionContext(epoch=epoch, run=run, is_current_generation=is_current)
        classify = getattr(_ADAPTERS[provider], classify_name)
        evidence, rejection = classify(payload, ctx, raw_ref=raw_ref, **kwargs)
        transitions: List[str] = []
        if rejection is not None:
            self.store.append_rejection(run.run_id, rejection)
            return [
                f"rejected {provider.value} artifact: {rejection.reason.value} "
                f"({rejection.detail})"
            ]
        self.store.append_evidence(run.run_id, evidence)
        resolution = resolve_provider_state(self.store.evidence_for(run.run_id))
        self.store.set_result_state(run.run_id, resolution.state)
        transitions.append(
            f"{provider.value} evidence admitted to generation {epoch.generation} "
            f"({evidence.carrier.value} {evidence.carrier_id}: "
            f"{evidence.classification.value}); provider state -> {resolution.state.value}"
        )
        if not is_current:
            transitions.append(
                f"note: evidence belongs to non-current generation "
                f"{epoch.generation} ({epoch.state.value}); the current epoch's "
                "verdict is unaffected"
            )
        return transitions

    def ingest_issue_comment(
        self,
        repository_id: int,
        pr_number: int,
        comment: dict,
        now: str,
        raw_ref: str = "",
        edited: bool = False,
    ) -> List[str]:
        actor_id = (comment.get("user") or {}).get("id")

        # Self-authored trigger comments reconcile ambiguous POSTs.
        if actor_id == self.config.governor_actor_id:
            return self._reconcile_own_comment(repository_id, pr_number, comment, now)

        provider = _ACTOR_TO_PROVIDER.get(actor_id)
        if provider is None:
            return ["ignored: comment from a non-provider, non-governor actor"]
        return self._ingest(
            repository_id,
            pr_number,
            provider,
            "classify_issue_comment",
            comment,
            now,
            raw_ref=raw_ref,
            edited=edited,
        )

    def ingest_review(
        self,
        repository_id: int,
        pr_number: int,
        review: dict,
        now: str,
        inline_comment_count: Optional[int] = None,
        raw_ref: str = "",
    ) -> List[str]:
        actor_id = (review.get("user") or {}).get("id")
        provider = _ACTOR_TO_PROVIDER.get(actor_id)
        if provider is None:
            return ["ignored: review from a non-provider actor"]
        return self._ingest(
            repository_id,
            pr_number,
            provider,
            "classify_review",
            review,
            now,
            raw_ref=raw_ref,
            inline_comment_count=inline_comment_count,
        )

    def ingest_review_comment(
        self, repository_id: int, pr_number: int, comment: dict, now: str, raw_ref: str = ""
    ) -> List[str]:
        actor_id = (comment.get("user") or {}).get("id")
        provider = _ACTOR_TO_PROVIDER.get(actor_id)
        if provider is None:
            return ["ignored: review comment from a non-provider actor"]
        return self._ingest(
            repository_id,
            pr_number,
            provider,
            "classify_review_comment",
            comment,
            now,
            raw_ref=raw_ref,
        )

    def ingest_reaction(
        self,
        repository_id: int,
        pr_number: int,
        parent_comment_id: int,
        reaction: dict,
        now: str,
        raw_ref: str = "",
    ) -> List[str]:
        """Reaction evidence (polled — GitHub has no reaction webhook).

        The reaction is evaluated against the run that owns the comment it
        sits on; a reaction on an older generation's request comment is
        rejected for the current generation by construction.
        """
        actor_id = (reaction.get("user") or {}).get("id")
        provider = _ACTOR_TO_PROVIDER.get(actor_id)
        if provider is None:
            return ["ignored: reaction from a non-provider actor"]

        current = self.store.current_epoch(repository_id, pr_number)
        if current is None:
            return ["ignored: no epochs exist for this PR"]

        # Find the run owning the parent comment (any generation).
        owner: Optional[Tuple[ReviewEpoch, ProviderRun]] = None
        owning_run = self.store.run_by_request_comment(
            repository_id, pr_number, provider, parent_comment_id
        )
        if owning_run is not None:
            owner = (self.store.get_epoch(owning_run.epoch_id), owning_run)

        if owner is None:
            # Reaction on something that is not one of our request comments.
            located = self._find_run(repository_id, pr_number, provider)
            if located is None:
                return ["ignored: reaction unrelated to any requested round"]
            epoch, run, is_current = located
            ctx = AdmissionContext(epoch, run, is_current_generation=is_current)
        else:
            epoch, run = owner
            ctx = AdmissionContext(
                epoch, run, is_current_generation=(epoch.epoch_id == current.epoch_id)
            )

        from .adapters.common import classify_reaction

        evidence, rejection = classify_reaction(
            provider, reaction, parent_comment_id, ctx, raw_ref=raw_ref
        )
        if rejection is not None:
            self.store.append_rejection(run.run_id, rejection)
            return [
                f"rejected {provider.value} reaction: {rejection.reason.value} "
                f"({rejection.detail})"
            ]
        self.store.append_evidence(run.run_id, evidence)
        resolution = resolve_provider_state(self.store.evidence_for(run.run_id))
        self.store.set_result_state(run.run_id, resolution.state)
        note = (
            ""
            if ctx.is_current_generation
            else " (non-current generation; current verdict unaffected)"
        )
        return [
            f"{provider.value} reaction admitted to generation {epoch.generation}: "
            f"{evidence.detail}; provider state -> {resolution.state.value}{note}"
        ]

    def _reconcile_own_comment(
        self, repository_id: int, pr_number: int, comment: dict, now: str
    ) -> List[str]:
        body = comment.get("body")
        for provider in trigger_mod.TRIGGER_BODIES:
            if not trigger_mod.is_trigger_body(provider, body):
                continue
            current = self.store.current_epoch(repository_id, pr_number)
            if current is None:
                return ["own trigger comment but no epoch exists; ignored"]
            run = self.store.run_for(current.epoch_id, provider)
            if run is None:
                return ["own trigger comment but no run for provider; ignored"]
            updated = trigger_mod.reconcile_unknown_request(
                self.store,
                run,
                self.config.governor_actor_id,
                [comment],
                listing_complete=False,
                now=now,
            )
            if updated.request_state != run.request_state:
                return [
                    f"{provider.value} request reconciled from delivery: "
                    f"comment {updated.request_comment_id} bound"
                ]
            return ["own trigger comment observed; no reconciliation needed"]
        return ["ignored: own comment that is not a trigger body"]

    # -- verdicts ----------------------------------------------------------

    def resolve_provider(
        self, epoch: ReviewEpoch, provider: Provider
    ) -> ProviderResolution:
        run = self.store.run_for(epoch.epoch_id, provider)
        if run is None:
            return ProviderResolution(
                ProviderState.PENDING,
                "no round was ever requested for this epoch",
                None,
            )
        resolution = resolve_provider_state(self.store.evidence_for(run.run_id))
        self.store.set_result_state(run.run_id, resolution.state)
        return resolution

    def evaluate(
        self,
        repository_id: int,
        pr_number: int,
        current_head_sha: str,
        now: Optional[str] = None,
    ) -> Tuple[VerdictResult, Dict[Provider, ProviderResolution], ReviewEpoch]:
        """Resolve both providers for the current epoch and reduce the verdict."""
        epoch = self.store.current_epoch(repository_id, pr_number)
        if epoch is None:
            raise RuntimeError("no epoch exists for this PR; nothing to evaluate")
        resolutions = {
            p: self.resolve_provider(epoch, p) for p in Provider
        }
        verdict = reduce_verdict(
            epoch,
            current_head_sha,
            resolutions[Provider.CODEX].state,
            resolutions[Provider.CODERABBIT].state,
        )
        self.store.record_verdict(
            epoch.epoch_id,
            verdict.codex_state,
            verdict.coderabbit_state,
            verdict.verdict,
            verdict.reason,
            computed_at=now or iso_now(),
        )
        return verdict, resolutions, epoch
