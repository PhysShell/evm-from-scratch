"""Store transition semantics."""

import unittest

from governor.model import EpochState, Provider, ProviderState, Verdict
from governor.store import Store

from .helpers import BASE, PR_NUMBER, REPO_ID, SHA1, SHA2, ts


class EpochTransitionTest(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")

    def test_generations_are_monotonic_and_unique(self):
        e1 = self.store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(0))
        e2 = self.store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(1))
        self.assertEqual((e1.generation, e2.generation), (1, 2))

    def test_new_epoch_same_head_supersedes_previous(self):
        e1 = self.store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(0))
        self.store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(1))
        self.assertEqual(self.store.get_epoch(e1.epoch_id).state, EpochState.SUPERSEDED)

    def test_new_epoch_new_head_stales_previous(self):
        e1 = self.store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(0))
        self.store.create_epoch(REPO_ID, PR_NUMBER, SHA2, BASE, ts(1))
        self.assertEqual(self.store.get_epoch(e1.epoch_id).state, EpochState.STALE)

    def test_mark_stale_on_new_head_is_noop_for_same_head(self):
        self.store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(0))
        self.assertIsNone(self.store.mark_stale_on_new_head(REPO_ID, PR_NUMBER, SHA1))

    def test_mark_stale_on_new_head_stales_active_epoch(self):
        e1 = self.store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(0))
        staled = self.store.mark_stale_on_new_head(REPO_ID, PR_NUMBER, SHA2)
        self.assertEqual(staled.epoch_id, e1.epoch_id)
        self.assertEqual(staled.state, EpochState.STALE)


class DeliveryDedupTest(unittest.TestCase):
    def test_second_record_of_same_guid_returns_false(self):
        store = Store(":memory:")
        self.assertTrue(store.record_delivery("g-1", "pull_request", "labeled", ts(0)))
        self.assertFalse(store.record_delivery("g-1", "pull_request", "labeled", ts(1)))
        self.assertTrue(store.record_delivery("g-2", "pull_request", "labeled", ts(1)))


class VerdictRecordTest(unittest.TestCase):
    def test_verdict_rows_accumulate_as_audit_history(self):
        store = Store(":memory:")
        epoch = store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(0))
        store.record_verdict(
            epoch.epoch_id,
            ProviderState.PENDING,
            ProviderState.PENDING,
            Verdict.INCONCLUSIVE,
            "nothing yet",
            ts(1),
        )
        store.record_verdict(
            epoch.epoch_id,
            ProviderState.CLEAN,
            ProviderState.CLEAN,
            Verdict.CLEAN,
            "both clean",
            ts(2),
        )
        rows = store.verdicts_for(epoch.epoch_id)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["verdict"], "INCONCLUSIVE")
        self.assertEqual(rows[1]["verdict"], "CLEAN")


class RunPersistenceTest(unittest.TestCase):
    def test_run_roundtrip_and_result_state(self):
        store = Store(":memory:")
        epoch = store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(0))
        run = store.create_run(epoch, Provider.CODEX)
        store.bind_request(run.run_id, 999001, ts(0))
        got = store.run_for(epoch.epoch_id, Provider.CODEX)
        self.assertEqual(got.request_comment_id, 999001)
        store.set_result_state(run.run_id, ProviderState.CLEAN)
        self.assertEqual(store.get_run(run.run_id).result_state, ProviderState.CLEAN)


if __name__ == "__main__":
    unittest.main()
