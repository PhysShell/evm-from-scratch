"""Shadow check-run payload builder."""

import unittest

from governor.check import CHECK_NAME, build_check_run_payload
from governor.model import (
    EpochState,
    ProviderResolution,
    ProviderState,
    ReviewEpoch,
    Verdict,
    VerdictResult,
)

from .helpers import BASE, PR_NUMBER, REPO_ID, SHA1, SHA2, ts


def epoch():
    return ReviewEpoch(
        epoch_id=1,
        repository_id=REPO_ID,
        pr_number=PR_NUMBER,
        head_sha=SHA1,
        base_sha=BASE,
        generation=3,
        state=EpochState.ACTIVE,
        requested_at=ts(0),
    )


def res(state, reason="r"):
    return ProviderResolution(state, reason, None)


class CheckPayloadTest(unittest.TestCase):
    def test_clean_maps_to_success(self):
        payload = build_check_run_payload(
            epoch(),
            SHA1,
            res(ProviderState.CLEAN),
            res(ProviderState.CLEAN),
            VerdictResult(Verdict.CLEAN, "both clean"),
        )
        self.assertEqual(payload["name"], CHECK_NAME)
        self.assertEqual(payload["conclusion"], "success")
        self.assertEqual(payload["head_sha"], SHA1)

    def test_blocked_maps_to_failure(self):
        payload = build_check_run_payload(
            epoch(),
            SHA1,
            res(ProviderState.FINDINGS),
            res(ProviderState.CLEAN),
            VerdictResult(Verdict.BLOCKED, "findings"),
        )
        self.assertEqual(payload["conclusion"], "failure")

    def test_stale_and_inconclusive_map_to_neutral(self):
        for verdict in (Verdict.STALE, Verdict.INCONCLUSIVE):
            payload = build_check_run_payload(
                epoch(),
                SHA2,
                res(ProviderState.PENDING),
                res(ProviderState.PENDING),
                VerdictResult(verdict, "x"),
            )
            self.assertEqual(payload["conclusion"], "neutral")

    def test_in_progress_round_reports_in_progress(self):
        payload = build_check_run_payload(
            epoch(),
            SHA1,
            res(ProviderState.PENDING),
            res(ProviderState.PENDING),
            VerdictResult(Verdict.INCONCLUSIVE, "waiting"),
            round_in_progress=True,
        )
        self.assertEqual(payload["status"], "in_progress")
        self.assertNotIn("conclusion", payload)

    def test_summary_shows_both_heads_and_both_providers(self):
        payload = build_check_run_payload(
            epoch(),
            SHA2,
            res(ProviderState.CLEAN, "codex reason"),
            res(ProviderState.STALE, "rabbit reason"),
            VerdictResult(Verdict.STALE, "head drift"),
        )
        summary = payload["output"]["summary"]
        self.assertIn(SHA1, summary)   # epoch HEAD
        self.assertIn(SHA2, summary)   # current HEAD
        self.assertIn("Codex:", summary)
        self.assertIn("CodeRabbit:", summary)
        self.assertIn("Shadow verdict: STALE", summary)
        self.assertIn("non-enforcing", summary)


if __name__ == "__main__":
    unittest.main()
