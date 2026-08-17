# Step 3 record — Baseline A, under E1-v2

Executes Step 2 §10 step 3 under [E1-v2](../../../docs/experiments/E1-v2-preregistration.md),
after [E1-v1 stopped](../../../docs/experiments/E1-v1-STOP.md) with
`STOP_SPECIFICATION_CONFLICT`.

**This measurement makes the E1-v2 freeze final.** A gap found after it is stop-and-preserve
continuing as `E1-v3`, never an in-place edit.

## Provenance

```text
target_revision_sha   551b4f5b8c1f0cd0b32e2ea932185f5a298d913c
                      the commit CONTAINING M0-v2, which the run was measured
                      against — not this record's commit (Step 0 §8)

manifest              manifest/M0-v2-protocol.json
                      E1_MANIFEST defaults to it; the v1 manifest stays
                      readable under the same variable, for audit
```

Superseded chain, preserved unmodified: `0346964` documents frozen → `b694824` M0 →
`affde50` v1's first measured run.

## What was measured

The Baseline A implementation is **unchanged from `affde50`**. It implements Step 0's reading
of the level split, which is the reading v2 adopts, so it was correct as written. What is
redone is the *measurement*, because v1's figures were taken under a manifest recording a
contradictory specification.

| | Result |
|---|---|
| level-A oracle slice | **49/49 pass** (50/50 including the M0 length guard) |
| manifest replay vs M0-v2 | **18/18 recomputed values agree** |
| coverage (Istanbul) | statements 95.65%, branches 85.13%, functions 100%, lines 95.62% |
| mutation (StrykerJS 10.0.0) | 231 mutants adjudicated |

```text
Killed        144
Survived       15
Timeout        13
NoCoverage     11
CompileError   48

killed / (killed + survived) = 144 / 159 = 90.57%
```

Identical to v1's figures, which is expected and worth stating plainly: the same code ran the
same tests. The amendment moved a postcondition between levels in a document; it changed no
executable line.

### Still not qualification evidence

Unchanged from the v1 record, and worth repeating rather than assuming inherited: these
figures come from the **oracle suite**, which Step 0 §3.2.1 bars from producing coverage,
mutation or local-detection evidence. The §3.3 thresholds apply to the frozen local suite
over `seam_adjacent_region` at step 6b; the 213 core tests arrive at step 4 and the seam at
step 5.

## Per-test semantics — re-verified, not inherited

The P-038 §3.3 warning was discharged for StrykerJS 10.0.0 under v1. Re-confirmed on this
run rather than carried over on the strength of the earlier one:

- `coverageAnalysis` is explicitly `perTest`;
- the run reports **11.64 tests per mutant** against a 50-test suite. A silent degradation
  to `all` would read 50.

## Amendment E1-v2/A1, confirmed against the artefacts

```text
SEM-RUN-4  level A -> level B          GAS is a level-B opcode (Step 0 §1.2)

postconditions      79   unchanged     24+13+7+8+15+6+6
surviving           58   unchanged
excluded            21   unchanged
core case IDs      213   unchanged     level split 167/46 -> 166/47
plan_core_digest         unchanged     63b4d9f9…aae02
c2_control_core_digest   unchanged     c4273493…a051
oracle sets              unchanged     49 / 71 / 6 witnesses / 65
```

Manifest replay recomputes both digests from M0-v2's own ID listing and the oracle sets from
`evm.json`, so "unchanged" above is a checked claim rather than a copied one.

The implementation agrees with the amended filing: `run.ts` does not dispatch `GAS`, and
corpus case #84 `GAS` is absent from the level-A slice and present in the level-B slice.
Under v1 that agreement contradicted Step 2 §3.1; under v2 it is what both documents say.

## Next

Step 4: write all 213 core case IDs from Step 2 §8. The 47 level-B ones will fail — the units
do not exist until step 5 — and that is expected and recorded, not a defect.
