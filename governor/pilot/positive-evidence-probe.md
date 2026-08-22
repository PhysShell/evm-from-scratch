# Positive evidence qualification probe (Stage A3a)

Disposable probe PR for the `ai-final-review` governance program.

- Purpose: run one fresh review round with **both** providers on a single
  unchanged head, then test whether the Governor can assemble a complete,
  current-head, request-lineage-bound positive evidence snapshot.
- **No green light is published.** The Governor shadow check stays
  `failure` by construction; `SUCCESS_CANDIDATE` exists only inside
  Governor state. Publishing success is a separate, gated stage.
- Neither provider state is ever recorded as CLEAN: what is captured is an
  advisory observation of what each provider said about this exact head.
- Merge: **NEVER**. Closed without merge after captures.
- Control plane: `PhysShell/review-governance`,
  branch `experiment/positive-evidence-qualification`.

post-round invalidation marker
