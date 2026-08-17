# E1 — MiniEVM specimen

Laboratory code for the E1 boundary blind-spot experiment. **Never a dependency of
Own.NET, OwnAudit or anything else** — the experiments README is explicit that conclusions
and patterns transfer, accidental laboratory architecture does not.

Governed by, and meaningless without:

- [E1 Step 0 — preregistration](../../docs/experiments/E1-step0-preregistration.md)
- [E1 Step 2 — semantics, projection, test plan](../../docs/experiments/E1-step2-semantics-and-plan.md)

## Where things are

```text
manifest/M0-protocol.json   the protocol manifest, frozen BEFORE the first measured run
manifest/oracle-sets.json   resolved evm.json case indices for level A and level B
src/                        the MiniEVM units of Step 2 §1.1
test/                       the level-A oracle slice; the 213 core tests arrive at step 4
tools/                      manifest replay and oracle slicing
```

## Sequence position

Step 2 §10 step 3: Baseline A. Level-A units, green on the 49-case level-A oracle slice,
with harness, coverage, mutation and manifest replay demonstrated.

**The Baseline A measurement makes the E1-v1 freeze final.** A gap discovered after it is a
stop-and-preserve, continuing only as a new E1-v2 preregistration — never an in-place edit of
Step 0 or Step 2.

No seam code, no defect, and no assertion outside the frozen plan may appear at this step.
