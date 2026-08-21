# AI final-review governor — shadow pilot

Non-enforcing pilot of a centralized final-review gate: before a human/agent
FINAL ACCEPT, a fresh external round (CodeRabbit full review + Codex review)
must exist for the **current** PR head. This package computes that verdict in
shadow mode only — it blocks nothing, and its check (`ai/final-review-shadow`)
must not be added to any ruleset.

* Architecture, empirically established provider contracts, open UNKNOWNs and
  activation prerequisites: [`docs/ai-final-review-pilot.md`](../docs/ai-final-review-pilot.md)
* Run the offline test suite (stdlib only, no network):

  ```sh
  python3 governor/run_tests.py
  ```

Layout:

```
src/governor/
  model.py        shared vocabulary: epochs, provider states, verdicts
  identity.py     provider actors, numeric-ID-primary
  store.py        SQLite state; deterministic transitions
  reducer.py      fail-closed shadow verdict
  trigger.py      label-driven round start; ambiguous-POST semantics
  webhook.py      signature verification, delivery idempotency, routing
  check.py        ai/final-review-shadow check-run payload builder
  engine.py       evidence routing and evaluation
  adapters/       Codex and CodeRabbit evidence normalization
tests/            adversarial suite (stale head, spoofed actor, dup delivery, ...)
pilot/            live-pilot captures (sanitized) and observation log
```
