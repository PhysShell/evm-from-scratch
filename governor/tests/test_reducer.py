"""Verdict reducer semantics.

The property under test is the task's central invariant:

    SHADOW_CLEAN iff codex == CLEAN and coderabbit == CLEAN
                 and epoch.head_sha == current head
                 and the epoch is the ACTIVE latest generation

and everything else — absence, timeout, rate limit, malformed, stale —
is fail-closed.
"""

import unittest

from governor.model import EpochState, ProviderState, ReviewEpoch, Verdict
from governor.reducer import reduce_verdict

from .helpers import BASE, REPO_ID, PR_NUMBER, SHA1, SHA2, ts


def epoch(state=EpochState.ACTIVE, head=SHA1, generation=1) -> ReviewEpoch:
    return ReviewEpoch(
        epoch_id=1,
        repository_id=REPO_ID,
        pr_number=PR_NUMBER,
        head_sha=head,
        base_sha=BASE,
        generation=generation,
        state=state,
        requested_at=ts(0),
    )


class ReduceVerdictTest(unittest.TestCase):
    def test_both_clean_on_current_head_is_clean(self):
        v = reduce_verdict(epoch(), SHA1, ProviderState.CLEAN, ProviderState.CLEAN)
        self.assertEqual(v.verdict, Verdict.CLEAN)

    def test_exhaustive_fail_closed_matrix(self):
        """No combination other than CLEAN+CLEAN may yield CLEAN."""
        for codex in ProviderState:
            for rabbit in ProviderState:
                v = reduce_verdict(epoch(), SHA1, codex, rabbit)
                if codex == ProviderState.CLEAN and rabbit == ProviderState.CLEAN:
                    self.assertEqual(v.verdict, Verdict.CLEAN)
                else:
                    self.assertNotEqual(
                        v.verdict,
                        Verdict.CLEAN,
                        f"codex={codex} coderabbit={rabbit} must not be CLEAN",
                    )

    def test_head_drift_is_stale_even_if_both_clean(self):
        v = reduce_verdict(epoch(head=SHA1), SHA2, ProviderState.CLEAN, ProviderState.CLEAN)
        self.assertEqual(v.verdict, Verdict.STALE)

    def test_stale_epoch_state_is_stale_even_if_both_clean(self):
        for state in (EpochState.STALE, EpochState.SUPERSEDED):
            v = reduce_verdict(
                epoch(state=state), SHA1, ProviderState.CLEAN, ProviderState.CLEAN
            )
            self.assertEqual(v.verdict, Verdict.STALE)

    def test_findings_block(self):
        v = reduce_verdict(epoch(), SHA1, ProviderState.FINDINGS, ProviderState.CLEAN)
        self.assertEqual(v.verdict, Verdict.BLOCKED)
        v = reduce_verdict(epoch(), SHA1, ProviderState.CLEAN, ProviderState.FINDINGS)
        self.assertEqual(v.verdict, Verdict.BLOCKED)

    def test_findings_beat_stale_provider(self):
        """A finding on the current head blocks even when the other provider
        only has stale-bound evidence."""
        v = reduce_verdict(epoch(), SHA1, ProviderState.FINDINGS, ProviderState.STALE)
        self.assertEqual(v.verdict, Verdict.BLOCKED)

    def test_one_provider_stale_is_stale_not_clean(self):
        v = reduce_verdict(epoch(), SHA1, ProviderState.CLEAN, ProviderState.STALE)
        self.assertEqual(v.verdict, Verdict.STALE)

    def test_rate_limited_is_not_clean(self):
        v = reduce_verdict(epoch(), SHA1, ProviderState.CLEAN, ProviderState.RATE_LIMITED)
        self.assertEqual(v.verdict, Verdict.INCONCLUSIVE)

    def test_missing_evidence_is_not_clean(self):
        v = reduce_verdict(epoch(), SHA1, ProviderState.CLEAN, ProviderState.PENDING)
        self.assertEqual(v.verdict, Verdict.INCONCLUSIVE)

    def test_malformed_is_not_clean(self):
        v = reduce_verdict(
            epoch(), SHA1, ProviderState.MALFORMED_EVIDENCE, ProviderState.CLEAN
        )
        self.assertEqual(v.verdict, Verdict.INCONCLUSIVE)

    def test_unavailable_is_not_clean(self):
        v = reduce_verdict(epoch(), SHA1, ProviderState.UNAVAILABLE, ProviderState.CLEAN)
        self.assertEqual(v.verdict, Verdict.INCONCLUSIVE)


if __name__ == "__main__":
    unittest.main()
