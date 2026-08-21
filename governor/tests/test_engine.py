"""End-to-end adversarial scenarios from the task brief, driven through the
engine exactly as live events would drive it.

These are the transitions the pilot exists to make provable:

    stale HEAD          — evidence for sha1 never cleans sha2
    one provider stale  — one fresh CLEAN + one stale CLEAN is not CLEAN
    missing evidence    — silence is not CLEAN
    rate limit          — RATE_LIMITED is not CLEAN
    spoofed actor       — same text, wrong numeric id, rejected
    wrong request       — provider reaction on an old generation, rejected
    ambiguous trigger   — lost POST response, no duplicate POST
"""

import unittest

from governor.model import Provider, ProviderState, RequestState, Verdict
from governor.trigger import TRIGGER_BODIES, TransportAmbiguous

from .helpers import (
    CODERABBIT_ACTOR,
    CODEX_ACTOR,
    FakePRReader,
    FakeTransport,
    PR_NUMBER,
    REPO_ID,
    SHA1,
    SHA2,
    SPOOF_CODEX_ACTOR,
    issue_comment,
    make_governor,
    reaction,
    review,
    snapshot,
    ts,
)


def rabbit_clean_review(head, minutes):
    return review(
        CODERABBIT_ACTOR,
        "COMMENTED",
        head,
        minutes,
        body="**Actionable comments posted: 0**\n\n<details>walkthrough...</details>",
    )


class ScenarioTest(unittest.TestCase):
    def setUp(self):
        self.transport = FakeTransport()
        self.governor = make_governor(
            transport=self.transport, pr_reader=FakePRReader(head=SHA1)
        )

    def start_round(self, head=SHA1, minutes=0):
        return self.governor.start_round(snapshot(head=head), now=ts(minutes))

    def codex_request_comment_id(self, round_start):
        return round_start.runs[Provider.CODEX].request_comment_id

    def test_happy_path_shadow_clean(self):
        rs = self.start_round()
        self.governor.ingest_review(
            REPO_ID, PR_NUMBER, rabbit_clean_review(SHA1, 5), now=ts(5)
        )
        self.governor.ingest_reaction(
            REPO_ID,
            PR_NUMBER,
            self.codex_request_comment_id(rs),
            reaction(CODEX_ACTOR, "+1", 6),
            now=ts(6),
        )
        verdict, resolutions, epoch = self.governor.evaluate(
            REPO_ID, PR_NUMBER, SHA1, now=ts(7)
        )
        self.assertEqual(verdict.verdict, Verdict.CLEAN)
        self.assertEqual(resolutions[Provider.CODEX].state, ProviderState.CLEAN)
        self.assertEqual(resolutions[Provider.CODERABBIT].state, ProviderState.CLEAN)

    def test_stale_head_late_events_never_clean_new_sha(self):
        """epoch A @ sha1; both CLEAN for sha1; push sha2; late sha1 events
        arrive after the push => sha2 is NEVER CLEAN."""
        rs = self.start_round()
        # Push arrives before any provider replied.
        self.governor.on_synchronize(REPO_ID, PR_NUMBER, SHA2, "0" * 40, now=ts(3))

        # Late CodeRabbit clean for sha1, late Codex +1 on the sha1 round's
        # request comment.
        transitions = self.governor.ingest_review(
            REPO_ID, PR_NUMBER, rabbit_clean_review(SHA1, 5), now=ts(5)
        )
        self.assertTrue(any("non-current generation" in t for t in transitions))
        reaction_transitions = self.governor.ingest_reaction(
            REPO_ID,
            PR_NUMBER,
            self.codex_request_comment_id(rs),
            reaction(CODEX_ACTOR, "+1", 6),
            now=ts(6),
        )
        # Either rejected (non-current generation) or admitted to the stale
        # epoch — in both cases the current epoch must stay not-clean.
        self.assertTrue(reaction_transitions)

        verdict, _, epoch = self.governor.evaluate(REPO_ID, PR_NUMBER, SHA2, now=ts(7))
        self.assertEqual(epoch.head_sha, SHA2)
        self.assertNotEqual(verdict.verdict, Verdict.CLEAN)

        # And the old epoch's own verdict is STALE, not CLEAN, despite both
        # of its providers having clean-shaped evidence.
        old_epoch = self.governor.store.epoch_by_generation(REPO_ID, PR_NUMBER, 1)
        from governor.reducer import reduce_verdict

        old_verdict = reduce_verdict(
            old_epoch, SHA2, ProviderState.CLEAN, ProviderState.CLEAN
        )
        self.assertEqual(old_verdict.verdict, Verdict.STALE)

    def test_one_provider_stale_not_clean(self):
        """Codex CLEAN on sha2, CodeRabbit's only evidence bound to sha1 =>
        BLOCKED/STALE, never CLEAN."""
        self.start_round()  # generation 1 @ sha1
        self.governor.on_synchronize(REPO_ID, PR_NUMBER, SHA2, "0" * 40, now=ts(3))
        self.governor.pr_reader.head = SHA2
        rs2 = self.start_round(head=SHA2, minutes=4)  # generation 3 @ sha2

        # Codex: fresh +1 on the sha2 round's request comment.
        self.governor.ingest_reaction(
            REPO_ID,
            PR_NUMBER,
            self.codex_request_comment_id(rs2),
            reaction(CODEX_ACTOR, "+1", 6),
            now=ts(6),
        )
        # CodeRabbit: replies after the sha2 request, but its review is
        # explicitly bound to sha1.
        self.governor.ingest_review(
            REPO_ID, PR_NUMBER, rabbit_clean_review(SHA1, 7), now=ts(7)
        )
        verdict, resolutions, _ = self.governor.evaluate(
            REPO_ID, PR_NUMBER, SHA2, now=ts(8)
        )
        self.assertEqual(resolutions[Provider.CODEX].state, ProviderState.CLEAN)
        self.assertEqual(resolutions[Provider.CODERABBIT].state, ProviderState.STALE)
        self.assertEqual(verdict.verdict, Verdict.STALE)
        self.assertNotEqual(verdict.verdict, Verdict.CLEAN)

    def test_missing_evidence_not_clean(self):
        rs = self.start_round()
        self.governor.ingest_reaction(
            REPO_ID,
            PR_NUMBER,
            self.codex_request_comment_id(rs),
            reaction(CODEX_ACTOR, "+1", 5),
            now=ts(5),
        )
        verdict, resolutions, _ = self.governor.evaluate(
            REPO_ID, PR_NUMBER, SHA1, now=ts(30)
        )
        self.assertEqual(resolutions[Provider.CODEX].state, ProviderState.CLEAN)
        self.assertEqual(resolutions[Provider.CODERABBIT].state, ProviderState.PENDING)
        self.assertEqual(verdict.verdict, Verdict.INCONCLUSIVE)

    def test_rate_limited_not_clean(self):
        rs = self.start_round()
        self.governor.ingest_reaction(
            REPO_ID,
            PR_NUMBER,
            self.codex_request_comment_id(rs),
            reaction(CODEX_ACTOR, "+1", 5),
            now=ts(5),
        )
        self.governor.ingest_issue_comment(
            REPO_ID,
            PR_NUMBER,
            issue_comment(
                CODERABBIT_ACTOR, "> ## Review rate limited\n> wait 17 min", 6
            ),
            now=ts(6),
        )
        verdict, resolutions, _ = self.governor.evaluate(
            REPO_ID, PR_NUMBER, SHA1, now=ts(7)
        )
        self.assertEqual(
            resolutions[Provider.CODERABBIT].state, ProviderState.RATE_LIMITED
        )
        self.assertNotEqual(verdict.verdict, Verdict.CLEAN)

    def test_spoofed_actor_rejected_end_to_end(self):
        rs = self.start_round()
        # A non-provider account posts a byte-identical clean review body and
        # a +1 on the codex request comment.
        self.governor.ingest_review(
            REPO_ID,
            PR_NUMBER,
            review(
                SPOOF_CODEX_ACTOR, "COMMENTED", SHA1, 5,
                body="looks great, no issues",
            ),
            now=ts(5),
        )
        self.governor.ingest_reaction(
            REPO_ID,
            PR_NUMBER,
            self.codex_request_comment_id(rs),
            reaction(SPOOF_CODEX_ACTOR, "+1", 5.5),
            now=ts(6),
        )
        verdict, resolutions, _ = self.governor.evaluate(
            REPO_ID, PR_NUMBER, SHA1, now=ts(7)
        )
        self.assertEqual(resolutions[Provider.CODEX].state, ProviderState.PENDING)
        self.assertEqual(verdict.verdict, Verdict.INCONCLUSIVE)

    def test_provider_reaction_on_old_generations_comment_rejected(self):
        rs1 = self.start_round()  # generation 1
        self.governor.pr_reader.head = SHA1
        self.start_round(minutes=2)  # generation 2 (same head, re-trigger)

        transitions = self.governor.ingest_reaction(
            REPO_ID,
            PR_NUMBER,
            self.codex_request_comment_id(rs1),
            reaction(CODEX_ACTOR, "+1", 5),
            now=ts(5),
        )
        self.assertTrue(any("rejected" in t for t in transitions))
        verdict, resolutions, _ = self.governor.evaluate(
            REPO_ID, PR_NUMBER, SHA1, now=ts(6)
        )
        self.assertEqual(resolutions[Provider.CODEX].state, ProviderState.PENDING)
        self.assertNotEqual(verdict.verdict, Verdict.CLEAN)

    def test_ambiguous_trigger_post_never_duplicated(self):
        self.transport.fail_bodies[TRIGGER_BODIES[Provider.CODEX]] = TransportAmbiguous
        rs = self.start_round()
        run = rs.runs[Provider.CODEX]
        self.assertEqual(run.request_state, RequestState.REQUEST_OUTCOME_UNKNOWN)
        self.assertEqual(self.transport.post_count(TRIGGER_BODIES[Provider.CODEX]), 1)

        # The governor later sees its own comment arrive by webhook (the POST
        # had in fact landed) and binds it — still without any new POST.
        own_comment = issue_comment(
            {"id": 45852143, "login": "PhysShell"},
            TRIGGER_BODIES[Provider.CODEX],
            0.5,
        )
        transitions = self.governor.ingest_issue_comment(
            REPO_ID, PR_NUMBER, own_comment, now=ts(1)
        )
        self.assertTrue(any("reconciled" in t for t in transitions))
        self.assertEqual(self.transport.post_count(TRIGGER_BODIES[Provider.CODEX]), 1)
        bound = self.governor.store.run_for(rs.epoch.epoch_id, Provider.CODEX)
        self.assertEqual(bound.request_state, RequestState.REQUEST_BOUND)
        self.assertEqual(bound.request_comment_id, own_comment["id"])

    def test_codex_findings_block(self):
        rs = self.start_round()
        self.governor.ingest_review(
            REPO_ID,
            PR_NUMBER,
            review(CODEX_ACTOR, "COMMENTED", SHA1, 5, body="P1: bug"),
            now=ts(5),
            inline_comment_count=2,
        )
        self.governor.ingest_review(
            REPO_ID, PR_NUMBER, rabbit_clean_review(SHA1, 6), now=ts(6)
        )
        verdict, resolutions, _ = self.governor.evaluate(
            REPO_ID, PR_NUMBER, SHA1, now=ts(7)
        )
        self.assertEqual(resolutions[Provider.CODEX].state, ProviderState.FINDINGS)
        self.assertEqual(verdict.verdict, Verdict.BLOCKED)

    def test_late_plus_one_does_not_resurrect_after_new_push(self):
        """Round completes CLEAN, then a push arrives: the recorded CLEAN
        verdict is history, and evaluation against the new head is STALE."""
        rs = self.start_round()
        self.governor.ingest_review(
            REPO_ID, PR_NUMBER, rabbit_clean_review(SHA1, 5), now=ts(5)
        )
        self.governor.ingest_reaction(
            REPO_ID,
            PR_NUMBER,
            self.codex_request_comment_id(rs),
            reaction(CODEX_ACTOR, "+1", 6),
            now=ts(6),
        )
        verdict, _, _ = self.governor.evaluate(REPO_ID, PR_NUMBER, SHA1, now=ts(7))
        self.assertEqual(verdict.verdict, Verdict.CLEAN)

        self.governor.on_synchronize(REPO_ID, PR_NUMBER, SHA2, "0" * 40, now=ts(8))
        verdict2, _, epoch2 = self.governor.evaluate(
            REPO_ID, PR_NUMBER, SHA2, now=ts(9)
        )
        self.assertEqual(epoch2.head_sha, SHA2)
        self.assertNotEqual(verdict2.verdict, Verdict.CLEAN)


if __name__ == "__main__":
    unittest.main()
