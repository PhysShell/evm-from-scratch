# User authorization lifecycle probe (Stage A1c)

Disposable probe PR for the `ai-final-review` governance program.

- Purpose: carry benign attribution comments while the GitHub App user
  authorization is refreshed, revoked and re-established, so that the
  carrier (`user` + `performed_via_github_app`) can be compared across
  credential generations.
- **No provider commands are issued from this PR.** Codex and CodeRabbit
  take no part in A1c; any auto-activity on PR open is baseline noise and
  is never acted upon.
- Merge: **NEVER**. Closed without merge after captures.
- Scope: this file only. PRs #11 / #12 / #13 / #14 / #15 untouched;
  PR #12 remains the frozen evidence baseline.
- Control plane: `PhysShell/review-governance`,
  branch `experiment/user-authorization-lifecycle`
  (`experiments/user-authorization-lifecycle/PROTOCOL.md`).
