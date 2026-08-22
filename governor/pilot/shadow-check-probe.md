# Governor shadow check probe (Stage A2b)

Disposable probe PR for the `ai-final-review` governance program.

- Purpose: let the Governor publish its own non-required Check Run
  (`ai/final-review-shadow`) bound to this PR exact full head SHA, then
  observe reconciliation after a deliberately missed synchronize webhook.
- **No provider commands are issued; no required check, no ruleset.**
  The Governor publishes no success in A2b by construction.
- Merge: **NEVER**. Closed without merge after captures.
- Control plane: `PhysShell/review-governance`,
  branch `experiment/governor-shadow-check`.

epoch marker: B
