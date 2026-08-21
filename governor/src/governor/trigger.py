"""Round trigger flow.

One explicit control action starts a round: the ``ai-final-review`` label.
On it the governor

1. re-reads the PR (fresh head/base — the label event's snapshot may lag);
2. creates the next-generation epoch for that exact head;
3. posts the two provider trigger comments;
4. records the created comment IDs as the generation's request bindings.

The POST itself is treated as an unreliable effect:

* intent is persisted (REQUEST_PENDING) *before* the POST;
* a confirmed 201 binds the comment id (REQUEST_BOUND);
* a lost response is REQUEST_OUTCOME_UNKNOWN — the comment may exist, so the
  round performs **no automatic retry**; only reconciliation against a
  complete comment listing may move it to BOUND (comment found) or FAILED
  (complete listing, window elapsed, no comment);
* a definite error response is REQUEST_FAILED (proven not created).

The fact that a POST succeeded is *not* proof the provider started — start
evidence only ever comes from provider-authored artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Optional, Protocol

from .model import (
    PRSnapshot,
    Provider,
    ProviderRun,
    RequestState,
    ReviewEpoch,
    parse_ts,
)
from .store import Store
from .adapters import codex, coderabbit

TRIGGER_BODIES: Dict[Provider, str] = {
    Provider.CODEX: codex.TRIGGER_BODY,
    Provider.CODERABBIT: coderabbit.TRIGGER_BODY,
}

#: How long reconciliation keeps waiting for an unconfirmed comment to show
#: up in listings before a complete listing may prove absence.
RECONCILE_WINDOW = timedelta(minutes=15)


class TransportAmbiguous(Exception):
    """The POST was sent but the response was lost (timeout, connection
    reset after send, 5xx with unknown side effect)."""


class TransportDenied(Exception):
    """A definite error response proving the comment was not created."""


class Transport(Protocol):
    def post_issue_comment(self, repository_id: int, pr_number: int, body: str) -> dict:
        """Create an issue comment; returns the created comment object
        (must include ``id`` and ``created_at``)."""
        ...


@dataclass
class RoundStart:
    epoch: ReviewEpoch
    runs: Dict[Provider, ProviderRun]


def start_round(
    store: Store, transport: Transport, snapshot: PRSnapshot, now: str
) -> RoundStart:
    """Create the next generation for the PR and post both triggers.

    Each provider's POST is independent: one binding and one ambiguous
    outcome leave a round with one BOUND and one OUTCOME_UNKNOWN run.
    """
    epoch = store.create_epoch(
        snapshot.repository_id,
        snapshot.pr_number,
        snapshot.head_sha,
        snapshot.base_sha,
        created_at=now,
    )
    runs: Dict[Provider, ProviderRun] = {}
    for provider in (Provider.CODERABBIT, Provider.CODEX):
        run = store.create_run(epoch, provider)
        body = TRIGGER_BODIES[provider]
        try:
            created = transport.post_issue_comment(
                snapshot.repository_id, snapshot.pr_number, body
            )
        except TransportAmbiguous:
            run = store.set_request_state(
                run.run_id, RequestState.REQUEST_OUTCOME_UNKNOWN, requested_at=now
            )
        except TransportDenied:
            run = store.set_request_state(run.run_id, RequestState.REQUEST_FAILED)
        else:
            run = store.bind_request(
                run.run_id, created["id"], created.get("created_at") or now
            )
        runs[provider] = run
    return RoundStart(epoch=epoch, runs=runs)


def reconcile_unknown_request(
    store: Store,
    run: ProviderRun,
    governor_actor_id: int,
    comments: List[dict],
    listing_complete: bool,
    now: str,
) -> ProviderRun:
    """Resolve a REQUEST_OUTCOME_UNKNOWN run against a comment listing.

    Binds when exactly one comment matches (governor actor, exact trigger
    body, created inside the reconcile window). Concludes FAILED only from a
    *complete* listing after the window has fully elapsed — a partial page
    can never prove absence. Anything else stays UNKNOWN. Never re-POSTs.
    """
    if run.request_state != RequestState.REQUEST_OUTCOME_UNKNOWN:
        return run
    body_expected = TRIGGER_BODIES[run.provider]
    window_start = parse_ts(run.requested_at)
    window_end = window_start + RECONCILE_WINDOW

    matches = [
        c
        for c in comments
        if (c.get("user") or {}).get("id") == governor_actor_id
        and (c.get("body") or "").strip() == body_expected
        and window_start <= parse_ts(c["created_at"]) <= window_end
    ]
    if len(matches) == 1:
        return store.bind_request(
            run.run_id, matches[0]["id"], matches[0]["created_at"]
        )
    if len(matches) > 1:
        # Two indistinguishable trigger comments: leave UNKNOWN, a human
        # must disambiguate. Auto-picking one could bind the wrong
        # generation's request.
        return run
    if listing_complete and parse_ts(now) > window_end:
        return store.set_request_state(run.run_id, RequestState.REQUEST_FAILED)
    return run
