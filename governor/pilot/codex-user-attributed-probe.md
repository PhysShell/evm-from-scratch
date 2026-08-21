# Codex user-attributed trigger probe (Stage A1b)

Disposable probe PR for the `ai-final-review` governance program.

- Purpose: measure whether a `@codex review` command authored through a
  **GitHub App user access token** (acting on behalf of `PhysShell`, App
  `physshell-review-governor`) can actually start a Codex review — the
  boundary that A1 showed the App *installation* identity cannot cross.
- Merge: **NEVER**. This PR is closed without merge after captures.
- Scope: this file only. Pilot artifacts (E1/E5) and PRs #11 / #12 / #13
  are untouched; PR #12 remains the frozen evidence baseline.
- Control plane: `PhysShell/review-governance`,
  branch `experiment/codex-user-attributed-trigger`
  (`experiments/codex-user-attributed-trigger/PROTOCOL.md`).
