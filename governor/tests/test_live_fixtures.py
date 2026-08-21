"""Replay of sanitized real PR #11 artifacts through the engine.

Every payload under ``fixtures/pr11_*.json`` was captured live on
2026-08-21 during the controlled pilot (see governor/pilot/observations/).
These tests ARE the empirically established provider contract: if a
provider changes its carrier shapes, these fixtures are what must be
re-captured and re-verified before trusting the adapters again.

Pilot chronology being replayed:

    03:14:34  PR #11 opened, head A = 1bc8038d…
    03:15:11  round-1 triggers posted (generation 1)
    03:16:53  Codex findings review, commit_id = A, 2 inline P1/P2 comments
    03:17:22  CodeRabbit review "Actionable comments posted: 2", commit_id = A
    03:18:3x  head B = d9796425… pushed (bait removed)
    03:19:31  round-2 triggers posted (generation 2, head B)
    03:19:44  CodeRabbit ack created (soft fair-usage warning)
    03:19:45  head C = ff74f6f3… pushed (deliberate mid-review change)
    03:20:01  CodeRabbit ack EDITED into hard "Review rate limited"
    03:21:11  Codex clean comment created, attests "Reviewed commit: ff74f6f34d"
"""

import json
import unittest
from pathlib import Path

from governor.engine import GovernorConfig, ShadowGovernor
from governor.model import Provider, ProviderState, Verdict
from governor.store import Store

FIXTURES = Path(__file__).parent / "fixtures"

HEAD_A = "1bc8038d0339bef67ad145bff85fb04b24e1e24b"
HEAD_B = "d979642546f29c2a3c032b4146687d40cceaf320"
HEAD_C = "ff74f6f34d10527ff357ebf75b43914722ad1588"
BASE = "047ff1a641e33e0bb8c6b9eea26bb80eea021e08"
#: Symbolic: the pilot identified the repo by (owner, name); the numeric id
#: is irrelevant to replay determinism.
REPO_ID = 1
PR = 11
GOVERNOR_ACTOR_ID = 45852143

RABBIT_REQ_1, RABBIT_REQ_1_AT = 5364756884, "2026-08-21T03:15:11Z"
CODEX_REQ_1, CODEX_REQ_1_AT = 5364757271, "2026-08-21T03:15:15Z"
RABBIT_REQ_2, RABBIT_REQ_2_AT = 5364783235, "2026-08-21T03:19:31Z"
CODEX_REQ_2, CODEX_REQ_2_AT = 5364783579, "2026-08-21T03:19:34Z"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def make_governor() -> ShadowGovernor:
    return ShadowGovernor(Store(":memory:"), GovernorConfig(GOVERNOR_ACTOR_ID))


def bind_round(store, head, base, created_at, rabbit_req, codex_req):
    epoch = store.create_epoch(REPO_ID, PR, head, base, created_at)
    for provider, (cid, cat) in (
        (Provider.CODERABBIT, rabbit_req),
        (Provider.CODEX, codex_req),
    ):
        run = store.create_run(epoch, provider)
        store.bind_request(run.run_id, cid, cat)
    return epoch


class Round1FindingsReplayTest(unittest.TestCase):
    def setUp(self):
        self.g = make_governor()
        bind_round(
            self.g.store,
            HEAD_A,
            BASE,
            "2026-08-21T03:15:00Z",
            (RABBIT_REQ_1, RABBIT_REQ_1_AT),
            (CODEX_REQ_1, CODEX_REQ_1_AT),
        )

    def test_real_findings_round_reduces_to_blocked(self):
        self.g.ingest_review(
            REPO_ID, PR, load("pr11_round1_coderabbit_review.json"),
            now="2026-08-21T03:17:30Z",
        )
        self.g.ingest_review(
            REPO_ID, PR, load("pr11_round1_codex_review.json"),
            now="2026-08-21T03:17:30Z",
            inline_comment_count=2,
        )
        verdict, res, _ = self.g.evaluate(REPO_ID, PR, HEAD_A, now="2026-08-21T03:18:00Z")
        self.assertEqual(res[Provider.CODERABBIT].state, ProviderState.FINDINGS)
        self.assertEqual(res[Provider.CODEX].state, ProviderState.FINDINGS)
        self.assertEqual(verdict.verdict, Verdict.BLOCKED)

    def test_codex_review_carries_consistent_sha_attestation(self):
        transitions = self.g.ingest_review(
            REPO_ID, PR, load("pr11_round1_codex_review.json"),
            now="2026-08-21T03:17:30Z",
            inline_comment_count=2,
        )
        self.assertTrue(any("FINDINGS" in t for t in transitions))


class Round2MidFlightReplayTest(unittest.TestCase):
    """Round 2 as it actually happened: requested on B, head moved to C
    11 seconds later, CodeRabbit hard-limited, Codex attested C."""

    def setUp(self):
        self.g = make_governor()
        bind_round(
            self.g.store,
            HEAD_B,
            BASE,
            "2026-08-21T03:19:25Z",
            (RABBIT_REQ_2, RABBIT_REQ_2_AT),
            (CODEX_REQ_2, CODEX_REQ_2_AT),
        )
        # 03:19:45 — head C pushed mid-review.
        self.g.on_synchronize(REPO_ID, PR, HEAD_C, BASE, now="2026-08-21T03:19:45Z")

    def test_soft_fair_usage_ack_is_pending_not_rate_limited(self):
        transitions = self.g.ingest_issue_comment(
            REPO_ID, PR, load("pr11_round2_coderabbit_ack_created.json"),
            now="2026-08-21T03:19:44Z",
        )
        self.assertTrue(any("PENDING" in t for t in transitions))

    def test_hard_refusal_arrives_only_as_edit_and_is_rate_limited(self):
        self.g.ingest_issue_comment(
            REPO_ID, PR, load("pr11_round2_coderabbit_ack_created.json"),
            now="2026-08-21T03:19:44Z",
        )
        transitions = self.g.ingest_issue_comment(
            REPO_ID, PR, load("pr11_round2_coderabbit_ack_edited.json"),
            now="2026-08-21T03:20:02Z",
            edited=True,
        )
        self.assertTrue(any("RATE_LIMITED" in t for t in transitions))

    def test_codex_clean_for_new_head_is_stale_for_the_requested_epoch(self):
        """The clean comment attests head C; the generation that requested it
        is bound to head B — for that epoch the evidence is STALE, and the
        current epoch (C) has no requested round, so C is never CLEAN."""
        transitions = self.g.ingest_issue_comment(
            REPO_ID, PR, load("pr11_round2_codex_clean_comment.json"),
            now="2026-08-21T03:21:11Z",
        )
        self.assertTrue(any("STALE" in t for t in transitions))
        verdict, res, epoch = self.g.evaluate(
            REPO_ID, PR, HEAD_C, now="2026-08-21T03:22:00Z"
        )
        self.assertEqual(epoch.head_sha, HEAD_C)
        self.assertNotEqual(verdict.verdict, Verdict.CLEAN)

    def test_full_round2_replay_never_cleans_anything(self):
        self.g.ingest_issue_comment(
            REPO_ID, PR, load("pr11_round2_coderabbit_ack_created.json"),
            now="2026-08-21T03:19:44Z",
        )
        self.g.ingest_issue_comment(
            REPO_ID, PR, load("pr11_round2_coderabbit_ack_edited.json"),
            now="2026-08-21T03:20:02Z",
            edited=True,
        )
        self.g.ingest_issue_comment(
            REPO_ID, PR, load("pr11_round2_codex_clean_comment.json"),
            now="2026-08-21T03:21:11Z",
        )
        verdict, _, _ = self.g.evaluate(REPO_ID, PR, HEAD_C, now="2026-08-21T03:22:00Z")
        self.assertEqual(verdict.verdict, Verdict.INCONCLUSIVE)


class CleanPathWithRealPayloadTest(unittest.TestCase):
    """The same real clean comment against an epoch that actually requested
    a round on the head it attests — the shape round 3 aims for."""

    def test_codex_clean_comment_cleans_a_matching_epoch(self):
        g = make_governor()
        bind_round(
            g.store,
            HEAD_C,
            BASE,
            "2026-08-21T03:19:25Z",
            (RABBIT_REQ_2, RABBIT_REQ_2_AT),
            (CODEX_REQ_2, CODEX_REQ_2_AT),
        )
        transitions = g.ingest_issue_comment(
            REPO_ID, PR, load("pr11_round2_codex_clean_comment.json"),
            now="2026-08-21T03:21:11Z",
        )
        self.assertTrue(any("CLEAN" in t for t in transitions))
        _, res, _ = g.evaluate(REPO_ID, PR, HEAD_C, now="2026-08-21T03:22:00Z")
        self.assertEqual(res[Provider.CODEX].state, ProviderState.CLEAN)

    def test_edited_clean_text_never_cleans(self):
        """Edit-smuggling guard: byte-identical clean body, arriving as an
        edit, must not produce CLEAN."""
        g = make_governor()
        bind_round(
            g.store,
            HEAD_C,
            BASE,
            "2026-08-21T03:19:25Z",
            (RABBIT_REQ_2, RABBIT_REQ_2_AT),
            (CODEX_REQ_2, CODEX_REQ_2_AT),
        )
        payload = load("pr11_round2_codex_clean_comment.json")
        payload["updated_at"] = "2026-08-21T03:25:00Z"
        g.ingest_issue_comment(
            REPO_ID, PR, payload, now="2026-08-21T03:25:00Z", edited=True
        )
        _, res, _ = g.evaluate(REPO_ID, PR, HEAD_C, now="2026-08-21T03:26:00Z")
        self.assertNotEqual(res[Provider.CODEX].state, ProviderState.CLEAN)


class TriggerBodyRealityTest(unittest.TestCase):
    def test_real_trigger_comment_reconciles(self):
        from governor.trigger import is_trigger_body

        payload = load("pr11_trigger_comment_codex.json")
        self.assertTrue(is_trigger_body(Provider.CODEX, payload["body"]))
        self.assertFalse(is_trigger_body(Provider.CODERABBIT, payload["body"]))


if __name__ == "__main__":
    unittest.main()
