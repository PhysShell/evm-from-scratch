# ai-final-review pilot probe

This pull request is an **infrastructure probe**, not a change to any
experiment or implementation state. It exists to capture, on a real PR in
this repository, the observable GitHub contract of two external reviewers:

* CodeRabbit — triggered by `@coderabbitai full review`
* Codex — triggered by `@codex review`

Protocol:

1. Head A carries `probe_sample.py`, a tiny standalone file with two
   deliberate, objectively verifiable defects (an inverted comparison
   against its own docstring, and a mutable default argument). It is not
   imported by anything. Its purpose is to elicit a *findings* review round.
2. A full external round is triggered on head A; every provider artifact
   (comments, reviews, review comments, reaction counts, timestamps,
   `commit_id` fields) is captured.
3. A second commit removes the defective file, changing the head. This
   makes the head-A round stale by construction and captures how late
   provider results relate to a superseded head.
4. A second round is triggered on head B (harmless content only) to capture
   the *clean* terminal shape of both providers.

This PR is closed without merging once captures are complete. The captured,
sanitized artifacts and the resulting analysis live on the
`claude/ai-final-review-governor-pilot-vohn85` branch
(`governor/`, `docs/ai-final-review-pilot.md`).

## Round log

- Head A round captured findings artifacts from both providers.
- Head C was pushed deliberately while the head-B round was in flight, to
  capture how late provider results relate to a superseded head.
