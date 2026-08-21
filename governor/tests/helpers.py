"""Shared fixtures/factories for the governor test suite.

All payload factories produce GitHub REST/webhook-shaped dicts. Numeric
actor IDs mirror the real providers; SPOOF_* actors reproduce the login but
not the ID, which is exactly the attack the identity layer must reject.
"""

from __future__ import annotations

import itertools
import json
from datetime import datetime, timedelta, timezone

from governor.identity import (
    CODERABBIT_ACTOR_ID,
    CODERABBIT_ACTOR_LOGIN,
    CODEX_ACTOR_ID,
    CODEX_ACTOR_LOGIN,
)
from governor.engine import GovernorConfig, ShadowGovernor
from governor.model import PRSnapshot
from governor.store import Store
from governor.trigger import TransportAmbiguous, TransportDenied  # noqa: F401 - re-exported for tests

REPO_ID = 616000001
PR_NUMBER = 424
GOVERNOR_ACTOR_ID = 45852143  # the account the pilot posts trigger comments as

SHA1 = "a" * 40
SHA2 = "b" * 40
BASE = "0" * 40

T0 = datetime(2026, 8, 21, 10, 0, 0, tzinfo=timezone.utc)

_ids = itertools.count(9_000_001)


def ts(minutes: float = 0) -> str:
    return (T0 + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def next_id() -> int:
    return next(_ids)


def actor(actor_id: int, login: str) -> dict:
    return {"id": actor_id, "login": login, "type": "Bot"}


CODEX_ACTOR = actor(CODEX_ACTOR_ID, CODEX_ACTOR_LOGIN)
CODERABBIT_ACTOR = actor(CODERABBIT_ACTOR_ID, CODERABBIT_ACTOR_LOGIN)
#: Same login as the provider, wrong numeric ID — the spoof case.
SPOOF_CODEX_ACTOR = actor(666, CODEX_ACTOR_LOGIN)
SPOOF_CODERABBIT_ACTOR = actor(667, CODERABBIT_ACTOR_LOGIN)
GOVERNOR_ACTOR = {"id": GOVERNOR_ACTOR_ID, "login": "PhysShell", "type": "User"}


def issue_comment(user: dict, body: str, minutes: float, comment_id=None) -> dict:
    return {
        "id": comment_id or next_id(),
        "user": user,
        "body": body,
        "created_at": ts(minutes),
        "updated_at": ts(minutes),
    }


def review(
    user: dict,
    state: str,
    commit_id: str,
    minutes: float,
    body: str = "",
    review_id=None,
) -> dict:
    return {
        "id": review_id or next_id(),
        "user": user,
        "state": state,
        "commit_id": commit_id,
        "body": body,
        "submitted_at": ts(minutes),
    }


def review_comment(user: dict, commit_id: str, minutes: float, body: str = "x") -> dict:
    return {
        "id": next_id(),
        "user": user,
        "body": body,
        "commit_id": commit_id,
        "created_at": ts(minutes),
    }


def reaction(user: dict, content: str, minutes: float) -> dict:
    return {
        "id": next_id(),
        "user": user,
        "content": content,
        "created_at": ts(minutes),
    }


def snapshot(head=SHA1, base=BASE) -> PRSnapshot:
    return PRSnapshot(
        repository_id=REPO_ID, pr_number=PR_NUMBER, head_sha=head, base_sha=base
    )


class FakeTransport:
    """In-memory transport; can be told to fail per-provider body."""

    def __init__(self, clock_minutes: float = 0):
        self.posted = []  # list of (repo, pr, body, comment_id)
        self.fail_bodies = {}  # body -> exception class
        self.clock_minutes = clock_minutes

    def post_issue_comment(self, repository_id: int, pr_number: int, body: str) -> dict:
        exc = self.fail_bodies.get(body)
        if exc is not None:
            # The POST may or may not have landed; the caller must not know.
            self.posted.append((repository_id, pr_number, body, None))
            raise exc()
        comment_id = next_id()
        self.posted.append((repository_id, pr_number, body, comment_id))
        return {
            "id": comment_id,
            "created_at": ts(self.clock_minutes),
            "user": dict(GOVERNOR_ACTOR),
            "body": body,
        }

    def post_count(self, body: str) -> int:
        return sum(1 for (_, _, b, _) in self.posted if b == body)


class FakePRReader:
    def __init__(self, head=SHA1, base=BASE):
        self.head = head
        self.base = base

    def get_pr(self, repository_id: int, pr_number: int) -> PRSnapshot:
        return PRSnapshot(repository_id, pr_number, self.head, self.base)


def make_governor(transport=None, pr_reader=None):
    store = Store(":memory:")
    config = GovernorConfig(governor_actor_id=GOVERNOR_ACTOR_ID)
    return ShadowGovernor(store, config, transport=transport, pr_reader=pr_reader)


def webhook_body(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")
