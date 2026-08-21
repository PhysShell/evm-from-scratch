"""Shadow check-run payload builder: ``ai/final-review-shadow``.

This module only *builds* the payload for
``POST /repos/{owner}/{repo}/check-runs``. Publishing it is a separate,
deliberately unimplemented-in-pilot step, because per GitHub's docs
"Write permission for the REST API to interact with checks is only
available to GitHub Apps" — the pilot's OAuth user identity cannot create
check runs at all. A production governor therefore requires its own GitHub
App installation; that is recorded as an activation prerequisite, not
worked around.

The check is informational and must never be added to a ruleset or branch
protection in this phase.
"""

from __future__ import annotations

from typing import Dict, Optional

from .model import (
    Evidence,
    ProviderResolution,
    ReviewEpoch,
    Verdict,
    VerdictResult,
)

CHECK_NAME = "ai/final-review-shadow"

_CONCLUSION = {
    Verdict.CLEAN: "success",
    Verdict.BLOCKED: "failure",
    # Shadow mode: an unfinished or unrepeatable round is displayed as
    # neutral — it must not look like a passing state, and action_required
    # is reserved for a future enforcing mode.
    Verdict.INCONCLUSIVE: "neutral",
    Verdict.STALE: "neutral",
}


def _provider_block(name: str, resolution: ProviderResolution) -> str:
    deciding: Optional[Evidence] = resolution.deciding
    carrier = deciding.carrier.value if deciding else "none"
    reviewed = (
        deciding.bound_sha
        if deciding is not None and deciding.sha_explicit
        else "not explicit in evidence"
    )
    return (
        f"{name}:\n"
        f"  state: {resolution.state.value}\n"
        f"  evidence carrier: {carrier}\n"
        f"  reviewed SHA: {reviewed}\n"
        f"  reason: {resolution.reason}\n"
    )


def build_check_run_payload(
    epoch: ReviewEpoch,
    current_head_sha: str,
    codex: ProviderResolution,
    coderabbit: ProviderResolution,
    verdict: VerdictResult,
    round_in_progress: bool = False,
) -> Dict:
    """Pure payload builder for the shadow check run."""
    summary = (
        f"epoch HEAD:   {epoch.head_sha} (generation {epoch.generation})\n"
        f"current HEAD: {current_head_sha}\n"
        f"\n"
        f"{_provider_block('Codex', codex)}"
        f"\n"
        f"{_provider_block('CodeRabbit', coderabbit)}"
        f"\n"
        f"Shadow verdict: {verdict.verdict.value}\n"
        f"  {verdict.reason}\n"
        f"\n"
        f"This check is a non-enforcing shadow pilot. It is not in any "
        f"ruleset and must not gate merges."
    )
    payload: Dict = {
        "name": CHECK_NAME,
        "head_sha": epoch.head_sha,
        "output": {
            "title": f"shadow verdict: {verdict.verdict.value}",
            "summary": summary,
        },
    }
    if round_in_progress and verdict.verdict == Verdict.INCONCLUSIVE:
        payload["status"] = "in_progress"
    else:
        payload["status"] = "completed"
        payload["conclusion"] = _CONCLUSION[verdict.verdict]
    return payload
