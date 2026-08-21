"""Non-enforcing shadow pilot of the AI final-review governor.

See docs/ai-final-review-pilot.md for architecture, empirically established
provider contracts, and the activation prerequisites. Nothing in this
package blocks a merge.
"""

__all__ = [
    "model",
    "identity",
    "store",
    "reducer",
    "trigger",
    "webhook",
    "check",
    "engine",
    "adapters",
]
