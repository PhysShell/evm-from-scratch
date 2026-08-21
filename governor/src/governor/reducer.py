"""Shadow verdict reducer.

The gate condition (shadow only — nothing is enforced):

    SHADOW_CLEAN  iff  codex == CLEAN
                  and  coderabbit == CLEAN
                  and  epoch.head_sha == current PR head_sha
                  and  epoch is the ACTIVE (latest-generation) epoch

Everything else is fail-closed:

    absence of evidence  != CLEAN
    timeout              != CLEAN
    skipped/unavailable  != CLEAN
    rate limited         != CLEAN
    malformed            != CLEAN
    stale-bound evidence != CLEAN
"""

from __future__ import annotations

from .model import (
    EpochState,
    ProviderState,
    ReviewEpoch,
    Verdict,
    VerdictResult,
)


def reduce_verdict(
    epoch: ReviewEpoch,
    current_head_sha: str,
    codex_state: ProviderState,
    coderabbit_state: ProviderState,
) -> VerdictResult:
    """Pure verdict function. No I/O, no clock.

    Precedence (deterministic):

    1. superseded epoch or head drift        -> STALE
    2. any provider FINDINGS (current head)  -> BLOCKED
    3. any provider evidence stale-bound     -> STALE
    4. both providers CLEAN                  -> CLEAN
    5. everything else                       -> INCONCLUSIVE
    """
    states = f"codex={codex_state.value} coderabbit={coderabbit_state.value}"

    if epoch.state != EpochState.ACTIVE:
        return VerdictResult(
            Verdict.STALE,
            f"epoch generation {epoch.generation} is {epoch.state.value}; "
            f"its round can never clean another head ({states})",
            codex_state,
            coderabbit_state,
        )
    if epoch.head_sha != current_head_sha:
        return VerdictResult(
            Verdict.STALE,
            f"epoch head {epoch.head_sha} != current head {current_head_sha}; "
            f"the whole external round must be repeated ({states})",
            codex_state,
            coderabbit_state,
        )
    if ProviderState.FINDINGS in (codex_state, coderabbit_state):
        return VerdictResult(
            Verdict.BLOCKED,
            f"provider findings on the current head ({states})",
            codex_state,
            coderabbit_state,
        )
    if ProviderState.STALE in (codex_state, coderabbit_state):
        return VerdictResult(
            Verdict.STALE,
            f"a provider's only evidence is bound to a superseded head ({states})",
            codex_state,
            coderabbit_state,
        )
    if (
        codex_state == ProviderState.CLEAN
        and coderabbit_state == ProviderState.CLEAN
    ):
        return VerdictResult(
            Verdict.CLEAN,
            f"both providers clean on head {epoch.head_sha} "
            f"generation {epoch.generation}",
            codex_state,
            coderabbit_state,
        )
    return VerdictResult(
        Verdict.INCONCLUSIVE,
        f"round not complete-and-clean ({states})",
        codex_state,
        coderabbit_state,
    )
