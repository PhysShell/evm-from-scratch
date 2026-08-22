# Shadow SUCCESS lifecycle probe (Stage A3b)

Disposable probe PR for the `ai-final-review` governance program.

- Purpose: publish the first Governor-owned `success` on
  `ai/final-review-shadow`, derived only from a frozen evidence bundle,
  then revoke it on the same head, requalify, and let a head change
  cancel it.
- The check is **not required**: no ruleset, no branch protection, no
  auto-merge, no expected-source enforcement. A green check here governs
  nothing.
- Merge: **NEVER**. Closed without merge after captures.
- Control plane: `PhysShell/review-governance`,
  branch `experiment/shadow-success-lifecycle`.

head change marker
