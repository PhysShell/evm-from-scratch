"""Provider actor identity.

The numeric GitHub account ID is the primary identity; the login is recorded
for diagnostics only. A login can be imitated in comment text and (in
pathological renames) reassigned; the numeric ID of an installed App's bot
account cannot be forged by another commenter.

IDs below were observed directly:

* ``coderabbitai[bot]`` id 136622811 — observed in PhysShell/evm-from-scratch
  PR #2/#7/#8/#10 issue comments (this repository, 2026-08).
* ``chatgpt-codex-connector[bot]`` id 199175422 — not yet observed in this
  repository at pilot start; the ID comes from the task brief and from the
  Joey-Tools/codex-review-gate v2 evidence-authority contract
  (``provider_identity``). The pilot must confirm it on first contact.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Provider

CODEX_ACTOR_ID = 199175422
CODEX_ACTOR_LOGIN = "chatgpt-codex-connector[bot]"

CODERABBIT_ACTOR_ID = 136622811
CODERABBIT_ACTOR_LOGIN = "coderabbitai[bot]"


@dataclass(frozen=True)
class ProviderActor:
    provider: Provider
    actor_id: int
    diagnostic_login: str


PROVIDER_ACTORS = {
    Provider.CODEX: ProviderActor(Provider.CODEX, CODEX_ACTOR_ID, CODEX_ACTOR_LOGIN),
    Provider.CODERABBIT: ProviderActor(
        Provider.CODERABBIT, CODERABBIT_ACTOR_ID, CODERABBIT_ACTOR_LOGIN
    ),
}


def is_provider_actor(provider: Provider, actor_id: object) -> bool:
    """True iff ``actor_id`` is the registered numeric ID for ``provider``.

    The comparison is on the numeric ID only, and only for an actual int —
    a string that happens to look like the ID is not accepted.
    """
    expected = PROVIDER_ACTORS[provider].actor_id
    return isinstance(actor_id, int) and not isinstance(actor_id, bool) and actor_id == expected
