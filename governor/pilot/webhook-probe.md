# Webhook control-plane probe (Stage A2a)

Disposable probe PR for the `ai-final-review` governance program.

- Purpose: carry a benign `pull_request.synchronize` so the Governor
  receiver can be observed marking the previous ReviewEpoch STALE.
- **No provider commands are issued.** No Check Run is created; that is A2b.
- Merge: **NEVER**. Closed without merge after captures.
- Control plane: `PhysShell/review-governance`,
  branch `experiment/webhook-control-plane`.

epoch marker: 3
