# CodeRabbit user-attributed trigger probe (Stage A1b-R)

Disposable probe PR for the `ai-final-review` governance program.

- Purpose: measure whether CodeRabbit processes `@coderabbitai full review`
  when the comment is authored through a **GitHub App user access token** —
  `user = PhysShell`, `performed_via_github_app = physshell-review-governor`.
  A1 measured CodeRabbit only on the installation-bot carrier (rejected)
  and the plain-human carrier (handled in 5 s); this third carrier is
  unexamined.
- Merge: **NEVER**. Closed without merge after captures.
- Scope: this file only. Pilot artifacts (E1/E5) and PRs #11 / #12 / #13 /
  #14 are untouched; PR #12 remains the frozen evidence baseline.
- Control plane: `PhysShell/review-governance`,
  branch `experiment/coderabbit-user-attributed-trigger`
  (`experiments/coderabbit-user-attributed-trigger/PROTOCOL.md`).
