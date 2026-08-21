"""Trigger flow: ambiguous POST semantics and reconciliation.

The invariant: POST → lost response must never become POST → POST. An
attempted effect with an ambiguous outcome is never replayed; only a
reconciliation read may resolve it.
"""

import unittest

from governor.model import Provider, RequestState
from governor.store import Store
from governor.trigger import (
    TRIGGER_BODIES,
    TransportAmbiguous,
    TransportDenied,
    reconcile_unknown_request,
    start_round,
)

from .helpers import (
    FakeTransport,
    GOVERNOR_ACTOR,
    GOVERNOR_ACTOR_ID,
    snapshot,
    ts,
)


class StartRoundTest(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")

    def test_happy_path_binds_both_requests(self):
        transport = FakeTransport()
        result = start_round(self.store, transport, snapshot(), now=ts(0))
        for provider in Provider:
            run = result.runs[provider]
            self.assertEqual(run.request_state, RequestState.REQUEST_BOUND)
            self.assertIsNotNone(run.request_comment_id)
        self.assertEqual(transport.post_count(TRIGGER_BODIES[Provider.CODEX]), 1)
        self.assertEqual(transport.post_count(TRIGGER_BODIES[Provider.CODERABBIT]), 1)

    def test_ambiguous_post_is_unknown_and_never_reposted(self):
        transport = FakeTransport()
        transport.fail_bodies[TRIGGER_BODIES[Provider.CODEX]] = TransportAmbiguous
        result = start_round(self.store, transport, snapshot(), now=ts(0))
        run = result.runs[Provider.CODEX]
        self.assertEqual(run.request_state, RequestState.REQUEST_OUTCOME_UNKNOWN)
        # Exactly one POST attempt happened for the ambiguous body...
        self.assertEqual(transport.post_count(TRIGGER_BODIES[Provider.CODEX]), 1)
        # ...and the other provider's flow was unaffected.
        self.assertEqual(
            result.runs[Provider.CODERABBIT].request_state, RequestState.REQUEST_BOUND
        )
        # Reconciliation with an empty, incomplete listing changes nothing
        # and performs no POST.
        updated = reconcile_unknown_request(
            self.store, run, GOVERNOR_ACTOR_ID, [], listing_complete=False, now=ts(1)
        )
        self.assertEqual(updated.request_state, RequestState.REQUEST_OUTCOME_UNKNOWN)
        self.assertEqual(transport.post_count(TRIGGER_BODIES[Provider.CODEX]), 1)

    def test_denied_post_is_failed(self):
        transport = FakeTransport()
        transport.fail_bodies[TRIGGER_BODIES[Provider.CODERABBIT]] = TransportDenied
        result = start_round(self.store, transport, snapshot(), now=ts(0))
        self.assertEqual(
            result.runs[Provider.CODERABBIT].request_state, RequestState.REQUEST_FAILED
        )


class ReconcileTest(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")
        transport = FakeTransport()
        transport.fail_bodies[TRIGGER_BODIES[Provider.CODEX]] = TransportAmbiguous
        self.round = start_round(self.store, transport, snapshot(), now=ts(0))
        self.run = self.round.runs[Provider.CODEX]

    def _own_comment(self, minutes, comment_id, body=None):
        return {
            "id": comment_id,
            "user": dict(GOVERNOR_ACTOR),
            "body": body or TRIGGER_BODIES[Provider.CODEX],
            "created_at": ts(minutes),
        }

    def test_single_match_binds(self):
        updated = reconcile_unknown_request(
            self.store,
            self.run,
            GOVERNOR_ACTOR_ID,
            [self._own_comment(1, 424242)],
            listing_complete=True,
            now=ts(2),
        )
        self.assertEqual(updated.request_state, RequestState.REQUEST_BOUND)
        self.assertEqual(updated.request_comment_id, 424242)

    def test_multiple_matches_stay_unknown(self):
        updated = reconcile_unknown_request(
            self.store,
            self.run,
            GOVERNOR_ACTOR_ID,
            [self._own_comment(1, 424242), self._own_comment(2, 424243)],
            listing_complete=True,
            now=ts(3),
        )
        self.assertEqual(updated.request_state, RequestState.REQUEST_OUTCOME_UNKNOWN)

    def test_incomplete_listing_never_proves_absence(self):
        updated = reconcile_unknown_request(
            self.store,
            self.run,
            GOVERNOR_ACTOR_ID,
            [],
            listing_complete=False,
            now=ts(60),
        )
        self.assertEqual(updated.request_state, RequestState.REQUEST_OUTCOME_UNKNOWN)

    def test_complete_listing_after_window_proves_absence(self):
        updated = reconcile_unknown_request(
            self.store,
            self.run,
            GOVERNOR_ACTOR_ID,
            [],
            listing_complete=True,
            now=ts(60),
        )
        self.assertEqual(updated.request_state, RequestState.REQUEST_FAILED)

    def test_complete_listing_inside_window_stays_unknown(self):
        updated = reconcile_unknown_request(
            self.store,
            self.run,
            GOVERNOR_ACTOR_ID,
            [],
            listing_complete=True,
            now=ts(5),
        )
        self.assertEqual(updated.request_state, RequestState.REQUEST_OUTCOME_UNKNOWN)

    def test_wrong_author_or_body_never_binds(self):
        stranger = {"id": 31337, "login": "somebody"}
        comments = [
            {"id": 1, "user": stranger, "body": TRIGGER_BODIES[Provider.CODEX], "created_at": ts(1)},
            self._own_comment(1, 2, body="@codex review please"),
        ]
        updated = reconcile_unknown_request(
            self.store,
            self.run,
            GOVERNOR_ACTOR_ID,
            comments,
            listing_complete=True,
            now=ts(2),
        )
        self.assertEqual(updated.request_state, RequestState.REQUEST_OUTCOME_UNKNOWN)


if __name__ == "__main__":
    unittest.main()
