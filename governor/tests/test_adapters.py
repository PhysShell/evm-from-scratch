"""Adapter classification and per-provider resolution semantics.

These tests pin the *reducer-relevant* meaning of provider artifacts, not
their cosmetic parsing: spoofed actors, timing admission, SHA binding,
"completion is not cleanliness", and the reaction contract.
"""

import unittest

from governor.adapters import codex, coderabbit
from governor.adapters.common import (
    AdmissionContext,
    classify_reaction,
    resolve_provider_state,
)
from governor.model import (
    Carrier,
    EpochState,
    Provider,
    ProviderRun,
    ProviderState,
    RejectionReason,
    RequestState,
    ReviewEpoch,
)

from .helpers import (
    BASE,
    CODERABBIT_ACTOR,
    CODEX_ACTOR,
    PR_NUMBER,
    REPO_ID,
    SHA1,
    SHA2,
    SPOOF_CODERABBIT_ACTOR,
    SPOOF_CODEX_ACTOR,
    issue_comment,
    next_id,
    reaction,
    review,
    ts,
)


def make_ctx(provider: Provider, request_comment_id=777001, head=SHA1, current=True):
    epoch = ReviewEpoch(
        epoch_id=1,
        repository_id=REPO_ID,
        pr_number=PR_NUMBER,
        head_sha=head,
        base_sha=BASE,
        generation=1,
        state=EpochState.ACTIVE,
        requested_at=ts(0),
    )
    run = ProviderRun(
        run_id=1,
        epoch_id=1,
        provider=provider,
        generation=1,
        request_state=RequestState.REQUEST_BOUND,
        request_comment_id=request_comment_id,
        requested_at=ts(0),
    )
    return AdmissionContext(epoch=epoch, run=run, is_current_generation=current)


class SpoofedActorTest(unittest.TestCase):
    def test_spoofed_codex_review_rejected_by_numeric_id(self):
        ctx = make_ctx(Provider.CODEX)
        ev, rej = codex.classify_review(
            review(SPOOF_CODEX_ACTOR, "COMMENTED", SHA1, minutes=5), ctx
        )
        self.assertIsNone(ev)
        self.assertEqual(rej.reason, RejectionReason.ACTOR_MISMATCH)

    def test_spoofed_coderabbit_comment_rejected(self):
        ctx = make_ctx(Provider.CODERABBIT)
        ev, rej = coderabbit.classify_issue_comment(
            issue_comment(
                SPOOF_CODERABBIT_ACTOR, "**Actionable comments posted: 0**", 5
            ),
            ctx,
        )
        self.assertIsNone(ev)
        self.assertEqual(rej.reason, RejectionReason.ACTOR_MISMATCH)

    def test_spoofed_plus_one_reaction_rejected(self):
        ctx = make_ctx(Provider.CODEX)
        ev, rej = classify_reaction(
            Provider.CODEX, reaction(SPOOF_CODEX_ACTOR, "+1", 5), 777001, ctx
        )
        self.assertIsNone(ev)
        self.assertEqual(rej.reason, RejectionReason.ACTOR_MISMATCH)

    def test_string_actor_id_is_not_accepted(self):
        spoof = {"id": str(CODEX_ACTOR["id"]), "login": CODEX_ACTOR["login"]}
        ctx = make_ctx(Provider.CODEX)
        ev, rej = classify_reaction(
            Provider.CODEX, reaction(spoof, "+1", 5), 777001, ctx
        )
        self.assertIsNone(ev)
        self.assertEqual(rej.reason, RejectionReason.ACTOR_MISMATCH)


class TimingAdmissionTest(unittest.TestCase):
    def test_artifact_before_request_rejected(self):
        ctx = make_ctx(Provider.CODEX)
        ev, rej = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "+1", -1), 777001, ctx
        )
        self.assertIsNone(ev)
        self.assertEqual(rej.reason, RejectionReason.BEFORE_REQUEST)

    def test_artifact_at_exactly_request_time_rejected(self):
        """Equal server second is not 'strictly after' — fail closed."""
        ctx = make_ctx(Provider.CODEX)
        ev, rej = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "+1", 0), 777001, ctx
        )
        self.assertIsNone(ev)
        self.assertEqual(rej.reason, RejectionReason.BEFORE_REQUEST)


class ReactionContractTest(unittest.TestCase):
    def test_plus_one_on_current_request_is_clean_candidate(self):
        ctx = make_ctx(Provider.CODEX)
        ev, rej = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "+1", 5), 777001, ctx
        )
        self.assertIsNone(rej)
        self.assertEqual(ev.classification, ProviderState.CLEAN)
        self.assertFalse(ev.sha_explicit)

    def test_reaction_on_wrong_comment_rejected(self):
        ctx = make_ctx(Provider.CODEX, request_comment_id=777001)
        ev, rej = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "+1", 5), 555000, ctx
        )
        self.assertIsNone(ev)
        self.assertEqual(rej.reason, RejectionReason.WRONG_REQUEST_COMMENT)

    def test_reaction_on_old_generation_comment_rejected_for_current(self):
        ctx = make_ctx(Provider.CODEX, current=False)
        ev, rej = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "+1", 5), 777001, ctx
        )
        self.assertIsNone(ev)
        self.assertEqual(rej.reason, RejectionReason.NOT_CURRENT_GENERATION)

    def test_eyes_at_or_after_plus_one_vetoes_reaction_clean(self):
        ctx = make_ctx(Provider.CODEX)
        plus, _ = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "+1", 5), 777001, ctx
        )
        eyes, _ = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "eyes", 6), 777001, ctx
        )
        res = resolve_provider_state([plus, eyes])
        self.assertEqual(res.state, ProviderState.PENDING)

    def test_eyes_before_plus_one_does_not_veto(self):
        ctx = make_ctx(Provider.CODEX)
        eyes, _ = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "eyes", 2), 777001, ctx
        )
        plus, _ = classify_reaction(
            Provider.CODEX, reaction(CODEX_ACTOR, "+1", 5), 777001, ctx
        )
        res = resolve_provider_state([eyes, plus])
        self.assertEqual(res.state, ProviderState.CLEAN)


class CodexCarrierTest(unittest.TestCase):
    def test_review_with_inline_comments_is_findings(self):
        ctx = make_ctx(Provider.CODEX)
        ev, _ = codex.classify_review(
            review(CODEX_ACTOR, "COMMENTED", SHA1, 5), ctx, inline_comment_count=2
        )
        self.assertEqual(ev.classification, ProviderState.FINDINGS)
        self.assertTrue(ev.sha_explicit)
        self.assertEqual(ev.bound_sha, SHA1)

    def test_review_commit_id_mismatch_is_stale(self):
        ctx = make_ctx(Provider.CODEX, head=SHA2)
        ev, _ = codex.classify_review(
            review(CODEX_ACTOR, "COMMENTED", SHA1, 5), ctx, inline_comment_count=2
        )
        self.assertEqual(ev.classification, ProviderState.STALE)

    def test_no_start_bodies_are_unavailable(self):
        ctx = make_ctx(Provider.CODEX)
        for body in codex.NO_START_BODIES:
            ev, _ = codex.classify_issue_comment(
                issue_comment(CODEX_ACTOR, body, 5), ctx
            )
            self.assertEqual(ev.classification, ProviderState.UNAVAILABLE)

    def test_unrecognized_codex_comment_is_malformed_not_clean(self):
        ctx = make_ctx(Provider.CODEX)
        ev, _ = codex.classify_issue_comment(
            issue_comment(CODEX_ACTOR, "I love this PR, ship it!", 5), ctx
        )
        self.assertEqual(ev.classification, ProviderState.MALFORMED_EVIDENCE)


class CodeRabbitCarrierTest(unittest.TestCase):
    def test_actionable_zero_review_bound_to_head_is_clean(self):
        ctx = make_ctx(Provider.CODERABBIT)
        ev, _ = coderabbit.classify_review(
            review(
                CODERABBIT_ACTOR,
                "COMMENTED",
                SHA1,
                5,
                body="**Actionable comments posted: 0**\n\nreview details...",
            ),
            ctx,
        )
        self.assertEqual(ev.classification, ProviderState.CLEAN)

    def test_actionable_nonzero_review_is_findings(self):
        ctx = make_ctx(Provider.CODERABBIT)
        ev, _ = coderabbit.classify_review(
            review(
                CODERABBIT_ACTOR,
                "COMMENTED",
                SHA1,
                5,
                body="**Actionable comments posted: 3**",
            ),
            ctx,
        )
        self.assertEqual(ev.classification, ProviderState.FINDINGS)

    def test_review_commit_id_mismatch_is_stale_even_with_zero_count(self):
        ctx = make_ctx(Provider.CODERABBIT, head=SHA2)
        ev, _ = coderabbit.classify_review(
            review(
                CODERABBIT_ACTOR,
                "COMMENTED",
                SHA1,
                5,
                body="**Actionable comments posted: 0**",
            ),
            ctx,
        )
        self.assertEqual(ev.classification, ProviderState.STALE)

    def test_full_review_finished_alone_is_not_clean(self):
        """'Full review finished' reports command completion, not zero
        findings."""
        ctx = make_ctx(Provider.CODERABBIT)
        ev, _ = coderabbit.classify_issue_comment(
            issue_comment(CODERABBIT_ACTOR, "Full review finished.", 5), ctx
        )
        self.assertEqual(ev.classification, ProviderState.INCONCLUSIVE)

    def test_comment_carried_zero_count_cannot_bind_head_so_not_clean(self):
        ctx = make_ctx(Provider.CODERABBIT)
        ev, _ = coderabbit.classify_issue_comment(
            issue_comment(CODERABBIT_ACTOR, "**Actionable comments posted: 0**", 5),
            ctx,
        )
        self.assertEqual(ev.classification, ProviderState.INCONCLUSIVE)
        self.assertFalse(ev.sha_explicit)

    def test_rate_limited_text_normalizes_to_rate_limited(self):
        ctx = make_ctx(Provider.CODERABBIT)
        ev, _ = coderabbit.classify_issue_comment(
            issue_comment(
                CODERABBIT_ACTOR,
                "> [!WARNING]\n> ## Review rate limited\n> please wait 17 minutes",
                5,
            ),
            ctx,
        )
        self.assertEqual(ev.classification, ProviderState.RATE_LIMITED)

    def test_ack_is_not_terminal(self):
        ctx = make_ctx(Provider.CODERABBIT)
        ev, _ = coderabbit.classify_issue_comment(
            issue_comment(CODERABBIT_ACTOR, "✅ Actions performed\n\nFull review triggered.", 5),
            ctx,
        )
        res = resolve_provider_state([ev])
        self.assertEqual(res.state, ProviderState.PENDING)

    def test_verbatim_captured_ack_is_ack_not_terminal(self):
        """Verbatim ack body captured on PR #11 (comment 5364757871,
        2026-08-21T03:15:21Z) — note singular 'Action performed'."""
        body = (
            "\n\n`@PhysShell`: I will perform a full review of pull request "
            "`#11`.\n\n\nAction performed\n\nFull review triggered.\n\n"
        )
        ctx = make_ctx(Provider.CODERABBIT)
        ev, rej = coderabbit.classify_issue_comment(
            issue_comment(CODERABBIT_ACTOR, body, 5), ctx
        )
        self.assertIsNone(rej)
        from governor.model import EvidenceRole

        self.assertEqual(ev.role, EvidenceRole.ACK)
        res = resolve_provider_state([ev])
        self.assertEqual(res.state, ProviderState.PENDING)

    def test_inline_comment_is_not_independent_finding(self):
        ctx = make_ctx(Provider.CODERABBIT)
        from .helpers import review_comment

        ev, _ = coderabbit.classify_review_comment(
            review_comment(CODERABBIT_ACTOR, SHA1, 5), ctx
        )
        res = resolve_provider_state([ev])
        self.assertEqual(res.state, ProviderState.PENDING)


class ResolutionSemanticsTest(unittest.TestCase):
    def test_findings_sticky_within_generation(self):
        ctx = make_ctx(Provider.CODERABBIT)
        findings, _ = coderabbit.classify_review(
            review(
                CODERABBIT_ACTOR, "COMMENTED", SHA1, 5,
                body="**Actionable comments posted: 2**",
            ),
            ctx,
        )
        later_clean, _ = coderabbit.classify_review(
            review(
                CODERABBIT_ACTOR, "COMMENTED", SHA1, 9,
                body="**Actionable comments posted: 0**",
            ),
            ctx,
        )
        res = resolve_provider_state([findings, later_clean])
        self.assertEqual(res.state, ProviderState.FINDINGS)

    def test_same_second_conflicting_terminals_are_inconclusive(self):
        ctx = make_ctx(Provider.CODERABBIT)
        clean, _ = coderabbit.classify_review(
            review(
                CODERABBIT_ACTOR, "COMMENTED", SHA1, 5,
                body="**Actionable comments posted: 0**", review_id=100,
            ),
            ctx,
        )
        limited, _ = coderabbit.classify_issue_comment(
            issue_comment(CODERABBIT_ACTOR, "Review rate limited", 5, comment_id=101),
            ctx,
        )
        res = resolve_provider_state([clean, limited])
        self.assertEqual(res.state, ProviderState.INCONCLUSIVE)

    def test_absence_is_pending_never_clean(self):
        res = resolve_provider_state([])
        self.assertEqual(res.state, ProviderState.PENDING)

    def test_only_stale_bound_evidence_resolves_stale(self):
        ctx = make_ctx(Provider.CODERABBIT, head=SHA2)
        ev, _ = coderabbit.classify_review(
            review(
                CODERABBIT_ACTOR, "COMMENTED", SHA1, 5,
                body="**Actionable comments posted: 0**",
            ),
            ctx,
        )
        res = resolve_provider_state([ev])
        self.assertEqual(res.state, ProviderState.STALE)


if __name__ == "__main__":
    unittest.main()
