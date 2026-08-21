"""Webhook verification and delivery idempotency.

Order of protections matters and is pinned here:
signature first (an unverified delivery must not even consume its GUID),
then GUID dedup (redeliveries reuse the original GUID), then routing.
"""

import unittest

from governor.webhook import (
    DELIVERY_HEADER,
    EVENT_HEADER,
    SIGNATURE_HEADER,
    WebhookProcessor,
    compute_signature,
    verify_signature,
)

from .helpers import (
    BASE,
    PR_NUMBER,
    REPO_ID,
    SHA1,
    SHA2,
    make_governor,
    ts,
    webhook_body,
)

SECRET = b"pilot-webhook-secret"


def headers(body: bytes, guid: str, event: str, secret: bytes = SECRET) -> dict:
    return {
        SIGNATURE_HEADER: compute_signature(secret, body),
        DELIVERY_HEADER: guid,
        EVENT_HEADER: event,
    }


def sync_payload(new_head=SHA2):
    return {
        "action": "synchronize",
        "repository": {"id": REPO_ID},
        "pull_request": {
            "number": PR_NUMBER,
            "head": {"sha": new_head},
            "base": {"sha": BASE},
        },
    }


class SignatureTest(unittest.TestCase):
    def test_valid_signature_accepted(self):
        body = b'{"x": 1}'
        self.assertTrue(
            verify_signature(SECRET, body, compute_signature(SECRET, body))
        )

    def test_missing_or_malformed_signature_rejected(self):
        body = b"{}"
        self.assertFalse(verify_signature(SECRET, body, None))
        self.assertFalse(verify_signature(SECRET, body, ""))
        self.assertFalse(verify_signature(SECRET, body, "sha1=deadbeef"))

    def test_tampered_body_rejected(self):
        body = webhook_body(sync_payload())
        sig = compute_signature(SECRET, body)
        tampered = body.replace(SHA2.encode(), SHA1.encode())
        self.assertFalse(verify_signature(SECRET, tampered, sig))

    def test_wrong_secret_rejected(self):
        body = b"{}"
        sig = compute_signature(b"other-secret", body)
        self.assertFalse(verify_signature(SECRET, body, sig))


class ProcessorTest(unittest.TestCase):
    def setUp(self):
        self.governor = make_governor()
        self.processor = WebhookProcessor(
            self.governor, SECRET, clock=lambda: ts(0)
        )
        # Seed an epoch so synchronize has something to stale.
        self.governor.store.create_epoch(REPO_ID, PR_NUMBER, SHA1, BASE, ts(0))

    def test_bad_signature_applies_nothing_and_does_not_burn_the_guid(self):
        body = webhook_body(sync_payload())
        bad = headers(body, "guid-1", "pull_request", secret=b"wrong")
        result = self.processor.process(bad, body)
        self.assertFalse(result.accepted)
        # The genuine delivery with the same GUID must still process.
        good = headers(body, "guid-1", "pull_request")
        result2 = self.processor.process(good, body)
        self.assertTrue(result2.accepted)
        self.assertFalse(result2.duplicate)
        self.assertTrue(any("STALE" in t for t in result2.transitions))

    def test_duplicate_delivery_applies_one_transition_only(self):
        body = webhook_body(sync_payload())
        h = headers(body, "guid-dup", "pull_request")
        first = self.processor.process(h, body)
        self.assertTrue(any("STALE" in t for t in first.transitions))
        generations_after_first = self._generation_count()

        second = self.processor.process(h, body)
        self.assertTrue(second.accepted)
        self.assertTrue(second.duplicate)
        self.assertEqual(second.transitions, [])
        self.assertEqual(self._generation_count(), generations_after_first)

    def test_same_event_different_guid_is_a_new_delivery(self):
        body = webhook_body(sync_payload())
        self.processor.process(headers(body, "guid-a", "pull_request"), body)
        result = self.processor.process(headers(body, "guid-b", "pull_request"), body)
        self.assertTrue(result.accepted)
        self.assertFalse(result.duplicate)

    def test_invalid_json_rejected(self):
        body = b"not-json"
        result = self.processor.process(headers(body, "guid-j", "pull_request"), body)
        self.assertFalse(result.accepted)

    def test_synchronize_stales_old_epoch_and_creates_successor(self):
        body = webhook_body(sync_payload())
        result = self.processor.process(headers(body, "guid-s", "pull_request"), body)
        self.assertTrue(result.accepted)
        current = self.governor.store.current_epoch(REPO_ID, PR_NUMBER)
        self.assertEqual(current.head_sha, SHA2)
        self.assertEqual(current.generation, 2)
        old = self.governor.store.epoch_by_generation(REPO_ID, PR_NUMBER, 1)
        self.assertEqual(old.state.value, "STALE")

    def _generation_count(self) -> int:
        current = self.governor.store.current_epoch(REPO_ID, PR_NUMBER)
        return current.generation if current else 0


if __name__ == "__main__":
    unittest.main()
