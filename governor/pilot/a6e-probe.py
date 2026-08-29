"""Disposable probe for the A6e steady-state qualification.

Small, isolated and reviewable on purpose: it must be something a provider
can form an opinion about, chosen and recorded before any provider sees it.

It is never merged, and it is never edited to obtain a clean review — a
fixture adjusted until it passes measures the adjuster.
"""


def clamp_gas(requested: int, limit: int) -> int:
    """Clamp a gas request into [0, limit].

    A negative request is a caller error rather than a free refund, so it
    clamps to zero instead of propagating a negative charge.
    """
    if limit < 0:
        raise ValueError("gas limit cannot be negative")
    if requested < 0:
        return 0
    return min(requested, limit)
