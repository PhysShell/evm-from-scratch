"""Probe sample for the ai-final-review pilot (see PROBE.md).

Standalone review-bait for an external-reviewer probe round. Nothing
imports this file. Both functions deliberately contradict their own
docstrings; the defects are removed in the follow-up commit.
"""


def is_head_fresh(recorded_head: str, current_head: str) -> bool:
    """Return True iff the recorded head still equals the current head."""
    return recorded_head != current_head


def unique_short_shas(shas: list, seen=[]) -> list:
    """Return the unique 7-char prefixes of ``shas``, preserving order.

    Must be a pure function of ``shas``.
    """
    for sha in shas:
        if sha[:7] not in seen:
            seen.append(sha[:7])
    return seen
