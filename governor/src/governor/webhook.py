"""GitHub webhook verification, idempotency and routing.

Order of operations is load-bearing:

1. **Verify** ``X-Hub-Signature-256`` (HMAC-SHA256 of the raw body with the
   webhook secret, constant-time comparison). An unverified delivery
   changes nothing — it must not even consume its delivery GUID, or a
   forger could poison the idempotency table and suppress the real
   delivery.
2. **Deduplicate** on ``X-GitHub-Delivery``. GitHub redeliveries carry the
   *same* GUID as the original delivery (docs: "the X-GitHub-Delivery
   header will be the same as in the original delivery"), so a GUID seen
   before applies zero transitions.
3. **Route**. Events are observation triggers, not evidence: routing hands
   payload artifacts to the adapters, and only adapter-admitted artifacts
   become evidence.

Note: GitHub emits **no webhook event for reactions**. A reaction-carried
clean signal is only observable by polling the reactions REST endpoint;
`engine.ShadowGovernor.ingest_reaction` is that polling path's entry.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .model import iso_now

SIGNATURE_HEADER = "X-Hub-Signature-256"
DELIVERY_HEADER = "X-GitHub-Delivery"
EVENT_HEADER = "X-GitHub-Event"


def compute_signature(secret: bytes, body: bytes) -> str:
    return "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()


def verify_signature(secret: bytes, body: bytes, signature_header: Optional[str]) -> bool:
    """Constant-time verification of ``X-Hub-Signature-256``."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = compute_signature(secret, body)
    return hmac.compare_digest(expected, signature_header)


@dataclass
class DeliveryResult:
    accepted: bool
    reason: str
    duplicate: bool = False
    transitions: List[str] = field(default_factory=list)


class WebhookProcessor:
    """Verifies, deduplicates and routes deliveries into the governor."""

    def __init__(
        self,
        governor,
        secret: bytes,
        clock: Optional[Callable[[], str]] = None,
    ):
        self._governor = governor
        self._secret = secret
        self._clock = clock or iso_now

    def process(self, headers: dict, body: bytes) -> DeliveryResult:
        # Header lookup is case-insensitive like HTTP.
        h = {k.lower(): v for k, v in headers.items()}
        if not verify_signature(self._secret, body, h.get(SIGNATURE_HEADER.lower())):
            return DeliveryResult(False, "signature verification failed")

        delivery_guid = h.get(DELIVERY_HEADER.lower())
        event = h.get(EVENT_HEADER.lower())
        if not delivery_guid or not event:
            return DeliveryResult(False, "missing delivery GUID or event header")

        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return DeliveryResult(False, "payload is not valid JSON")

        action = payload.get("action")
        now = self._clock()
        fresh = self._governor.store.record_delivery(delivery_guid, event, action, now)
        if not fresh:
            return DeliveryResult(
                True,
                f"duplicate delivery {delivery_guid}: already processed, no transition",
                duplicate=True,
            )

        transitions = self._route(event, action, payload, now)
        return DeliveryResult(True, "processed", transitions=transitions)

    def _route(self, event: str, action: Optional[str], payload: dict, now: str) -> List[str]:
        g = self._governor
        if event == "pull_request" and action == "synchronize":
            return g.on_synchronize(
                repository_id=payload["repository"]["id"],
                pr_number=payload["pull_request"]["number"],
                new_head_sha=payload["pull_request"]["head"]["sha"],
                new_base_sha=payload["pull_request"]["base"]["sha"],
                now=now,
            )
        if event == "pull_request" and action == "labeled":
            return g.on_labeled(
                repository_id=payload["repository"]["id"],
                pr_number=payload["pull_request"]["number"],
                label_name=(payload.get("label") or {}).get("name", ""),
                now=now,
            )
        if event == "issue_comment" and action == "created":
            issue = payload.get("issue") or {}
            if "pull_request" not in issue:
                return ["ignored: comment on a non-PR issue"]
            return g.ingest_issue_comment(
                repository_id=payload["repository"]["id"],
                pr_number=issue["number"],
                comment=payload["comment"],
                now=now,
            )
        if event == "pull_request_review" and action == "submitted":
            return g.ingest_review(
                repository_id=payload["repository"]["id"],
                pr_number=payload["pull_request"]["number"],
                review=payload["review"],
                now=now,
            )
        if event == "pull_request_review_comment" and action == "created":
            return g.ingest_review_comment(
                repository_id=payload["repository"]["id"],
                pr_number=payload["pull_request"]["number"],
                comment=payload["comment"],
                now=now,
            )
        return [f"ignored: {event}/{action}"]
