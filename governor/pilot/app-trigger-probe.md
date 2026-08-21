# App trigger authority probe (Stage A1)

Disposable probe PR for the `ai-final-review` governance program.

- Purpose: measure whether review providers accept trigger commands whose
  issue comment is authored by the Governor GitHub App installation
  identity (`physshell-review-governor[bot]`), not a human/OAuth user.
- Merge: **NEVER**. This PR is closed without merge after captures.
- Scope: this file only. Pilot artifacts (E1/E5) and PR #11 / PR #12 are
  untouched; PR #12 remains the frozen evidence baseline.
- Control plane: `PhysShell/review-governance`,
  branch `experiment/app-trigger-authority`
  (`experiments/app-trigger-authority/PROTOCOL.md`).
