# E1-v1 — STOP_SPECIFICATION_CONFLICT

**Outcome:** E1-v1 halts at Step 2 §10 step 3. Step 4 is not executed under v1.

**Cause:** a contradiction *between two frozen documents*, discovered at the first measured
run. Not a defect in the implementation, and not a result about boundary blindness.

This document is a decision record. Nothing it describes may be repaired in place — Step 0
§0 binds v1 from the moment of its first measurement, and that moment has passed.

---

## 1. The conflict

**Step 0 §1.1** lists the level-A opcode set. `GAS` is not in it:

```text
STOP
PUSH0, PUSH1..PUSH32
POP
ADD, SUB, MUL, DIV, MOD
LT, GT, EQ, ISZERO
DUP1..DUP16, SWAP1..SWAP16
JUMP, JUMPI, JUMPDEST, PC
```

**Step 0 §1.2** adds `GAS` to level B, as a stack producer with no accounting, and explains
why: the upstream `DELEGATECALL` fixture passes a gas argument, and dropping it would cost
the `address`/`storage_owner` seam its witness.

**Step 2 §3.1**, whose table is headed *Level A*, contains:

```text
| SEM-RUN-4 | U-RUN | 1 | GAS pushes MAX_UINT256 (Step 0 §1.2) |
```

The row cites `§1.2` — the level-**B** section — while sitting in the level-**A** table. The
document contradicts itself inside a single line, and it contradicts Step 0 across documents.

**M0 froze the consequence.** `LT-SEM-RUN-4` is one of the 213 core case IDs, and Step 2 §4
counts `SEM-RUN-4` among the "25 at level A".

## 2. Why it could not be satisfied

The two readings demand different artefacts, and the difference is measurable, not
cosmetic:

| | Step 0's reading | Step 2 §3.1's reading |
|---|---|---|
| `GAS` in Baseline A | no | yes |
| level-A oracle slice | 49 cases | 50 cases, including #84 `GAS` |
| Baseline A dispatches `GAS` | no | yes |

Verified against the corpus: **case #84 is absent from the level-A in-subset set and present
in the level-B one.** So the 49-case slice that M0 froze is Step 0's slice. There is no
implementation that satisfies both documents.

`affde50` implemented Step 0's reading: `run.ts` does not dispatch `GAS`, names it level B in
a comment, and halts exceptionally on any opcode outside the frozen level-A set. The 49/49
green result is therefore correct *for that reading* and tells us nothing about the other.

## 3. Why this is a stop and not a one-line fix

The repair is genuinely small and genuinely outcome-independent — move one row from §3.1 to
a level-B group and correct a categorical count. That is exactly what makes the stop rule
worth having.

Without it, the natural move is to shift the row, commit `docs: clarify`, and carry on. The
history would then assert that a consistent specification existed before the measurement. It
did not. The whole apparatus of Step 0 §0 — *nothing may be revised after the first measured
run* — exists for the case where the tempting fix is small, because the tempting fix is
always small.

Step 0 §0 and Step 2 §8.2.2 both name the consequence: stop, preserve, continue only as a
new `E1-v2`.

## 4. Preserved evidence chain

None of these commits may be amended, rebased or reverted. They are the record that the
conflict pre-dated its discovery.

```text
0346964508260965a5229b929d9b4d06a8914bf1   Step 0 and Step 2 frozen (ACCEPT/FREEZE)
        │
b694824611a2a3eba3e806de3f847406acf5a6f9   M0 protocol manifest — no measurement
        │                                   (direct parent of the run below)
affde50ea049681395002861672adab8a8ed74b2   Baseline A: the FIRST MEASURED RUN
                                            49/49 oracle, coverage, mutation, replay
```

Document blobs as frozen at the moment of measurement:

```text
c294d724ce50952db4642f9ef757a3f7a6bf33b6   E1-step0-preregistration.md
586bb92f66d9c6c889a9c2266832264d526a87b4   E1-step2-semantics-and-plan.md
d88cd9ee0b194b2aa35128aec57bddea9e984c7d   M0-protocol.json
```

## 5. What v1 established, and what it did not

**Established, and carried into v2 unchanged:**

- the level-A implementation is correct against Step 0's reading — 49/49;
- the toolchain functions end to end: harness, coverage, mutation over 231 mutants, manifest
  replay agreeing with M0 on 18/18 recomputed values;
- StrykerJS 10.0.0 genuinely performs per-test analysis — 11.64 tests per mutant against a
  50-test suite — which discharges the P-038 §3.3 warning that Step 2 §2 had only inherited.

**Not established, and not claimed:**

- nothing about D1–D4, the projection, the calibration slice, or boundary blindness. No
  specimen was built and no seam exists. This is a `STOP` for a specification defect, and it
  is **not** a negative result about the research hypothesis — the distinction P-038 §5.1
  and Step 0 §6.1 both insist on.

## 6. Continuation

[`E1-v2`](./E1-v2-preregistration.md) inherits the v1 documents by blob sha and carries
exactly one amendment. It is a new preregistration, not an edit.
