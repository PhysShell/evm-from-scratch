# E1-v2 — STOP_PROTOCOL_FREEZE_ORDER

**Outcome:** E1-v2 halts. Step 4 is not executed under v2.

**Cause:** the preregistration never reached the state it defines as frozen before its first
measurement. Not a semantic defect, not a defect in Baseline A, and not a result about
boundary blindness.

---

## 1. The defect

`E1-v2-preregistration.md` says of itself:

> **Frozen on merge**, under the same rule the v1 documents carried.

The inherited Step 0 §9 step 1 is more explicit still:

> 1. **freeze** — this document reviewed and **merged**;

`merged` is not decorative. It is the event the whole protocol keys on: everything after it
is fixed, and the first measured run is what makes that fixity final.

**It never happened.** At the moment of the v2 Baseline A measurement:

```text
origin/main   2ea705714ab31b39568a61865cffa96fd3b96ea7   (roadmap PR #1)
branch        08891c9853349adda35c356190f6b295bbee8659   16 commits ahead

docs/experiments/ on main:
    E1-boundary-blind-spots.md
    E2-plonky3-zkvm.md
    E3-testing-vs-proof.md
    E4-outcome-fidelity.md
    README.md
```

Neither `E1-step0-preregistration.md`, nor `E1-step2-semantics-and-plan.md`, nor
`E1-v2-preregistration.md` exists on `main` at all. The preregistrations were **committed**
before measurement — which is real provenance and is preserved — but committed is not
merged, and merged is what the documents demanded of themselves.

## 2. Why this cannot be repaired by merging now

The obvious move is to merge the branch and treat the condition as satisfied. It is not
available: the first measured run of v2 already happened, at `08891c9`. A merge performed
afterwards is a later event, and no ordering of commits can place it before a measurement
that has already occurred.

This is the same shape as the v1 stop, in a different layer: the tempting repair is small,
and taking it would leave a history asserting that a required precondition held when it did
not.

## 3. Scope

**v1's stop is unaffected.** It halted on an independent, semantic conflict over `GAS`
([E1-v1-STOP](./E1-v1-STOP.md)). The freeze-order defect applied to v1 as well, but v1 was
already stopped on other grounds, so nothing turns on it there.

**Baseline A is unaffected as an implementation.** It passes 49/49 against the level-A oracle
under both v1's and v2's reading, and it carries into v3 unchanged.

**Nothing is established or refuted about the research question.** No specimen was built, no
seam exists, no defect was injected, and no calibration figure was produced. `STOP` here is a
statement about protocol execution and nothing else — the distinction Step 0 §6.1 and P-038
§5.1 both insist on.

## 4. Preserved chain

Unmodified, unrebased, unsquashed:

```text
dfcf875   v1 STOP recorded, E1-v2 preregistration opened
   │
551b4f5   M0-v2 — no measurement; the recorded target revision
   │
08891c9   v2 Baseline A — the FIRST MEASURED RUN under v2
          49/49 oracle, replay 18/18, coverage, 231 mutants
```

## 5. Continuation

[`E1-v3`](./E1-v3-preregistration.md), whose freeze event is made unambiguous and, unlike its
predecessors, is actually performed before any measurement:

1. this history is merged into `main` by an ordinary merge — no squash, no rebase — so every
   evidence sha above survives;
2. the v3 preregistration is reviewed and merged into `main`. **That merge commit is the
   freeze event**;
3. `M0-v3` is permitted only on a descendant of that merge sha, and records it;
4. the unchanged Baseline A is measured again on that descendant;
5. only then, step 4.

The semantics and amendment `E1-v2/A1` carry into v3 unchanged. v3 exists because a freeze
event has to be an event, not an intention expressed in Markdown.
