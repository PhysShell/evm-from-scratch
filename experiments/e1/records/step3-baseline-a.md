# Step 3 record — Baseline A

Executes E1 Step 2 §10 step 3. **This measurement makes the E1-v1 freeze final**: a gap
found after it is a stop-and-preserve continuing as a new `E1-v2`, never an in-place edit of
Step 0 or Step 2.

M0 was written and committed before any figure below existed (`b694824`).

## What was built

The level-A units of Step 2 §1.1 — `U-DEC`, `U-STK`, `U-ARI`, `U-CMP`, `U-JMP`, `U-RUN` —
against the §3.1 postconditions. No seam code, no `U-CALL`, no defect, and no assertion
outside the frozen plan, all of which step 3 forbids.

An opcode outside the frozen level-A set halts exceptionally rather than being treated as
unimplemented. That is the honest reading of "outside the subset": level B has not been
built, so there is nothing to be missing.

## Oracle

```text
level-A oracle slice        49/49 pass
harness guard               1/1   (M0 froze exactly 49 cases)
                            50/50 total
```

The case indices are read from `M0-protocol.json` rather than recomputed in the test, so a
drift between what M0 froze and what a run measures fails loudly instead of quietly
substituting a different denominator.

## Toolchain demonstrations

All four required by step 3 function:

| | |
|---|---|
| harness | Jest 30.4.2 + ts-jest 29.4.12, 50 tests |
| coverage | Istanbul via Jest — statements 95.65%, branches 85.13%, functions 100%, lines 95.62% |
| mutation | StrykerJS 10.0.0 — 231 mutants generated and adjudicated |
| manifest replay | 18/18 recomputed values agree with M0 |

### These figures are NOT qualification evidence

They were produced by the **oracle suite**, and Step 0 §3.2.1 bars the oracle from producing
coverage, mutation or local-detection evidence — its one job is "is the baseline correct".
The §3.3 thresholds apply to the **frozen local suite** over `seam_adjacent_region`, measured
at step 6b, and neither exists yet: the 213 core tests arrive at step 4 and the seam at
step 5.

Recording the distinction here rather than leaving it implicit is deliberate. A coverage
number that exists in a repository is one careless sentence away from being quoted as
baseline adequacy, and this one would be the wrong number measured by the wrong suite against
a region that does not yet exist.

## Mutation detail

```text
total mutants     231
  Killed          144
  Survived         15
  Timeout          13
  NoCoverage       11
  CompileError     48

killed / (killed + survived) = 144 / 159 = 90.57%
```

`CompileError` mutants are the `typescript-checker` rejecting mutants that do not typecheck;
they are excluded from the ratio, as Step 0 §3.3.1 requires of every unassessed class.

## Per-test semantics — the P-038 §3.3 warning, discharged

P-038 §3.3 warns that Stryker's per-test semantics must be re-verified against the version
used. The warning names **Stryker.NET**; StrykerJS is a different implementation, so Step 2
§2 inherited it rather than discharging it. Verified here for **StrykerJS 10.0.0**:

- `coverageAnalysis` is set explicitly to `perTest` in `stryker.config.json`, never left
  implicit;
- the dry run reports `jest test runner with "perTest" coverage analysis`;
- the run reports **11.64 tests per mutant on average** against a 50-test suite, which is
  the observable proof that per-test filtering is actually happening. Had `perTest` been
  silently degrading to `all`, the average would have been 50.

## Frozen artefacts unchanged

Manifest replay confirms, from primary sources rather than from the record: the three
governing documents by blob sha, the oracle case indices recomputed from `evm.json` including
the nested callee-code check, `plan_core_digest` and `c2_control_core_digest` recomputed from
M0's own ID listing, the two domains differing by exactly the C2 assertion, and all eight
toolchain versions from the lockfile.

## Next

Step 4: write the 213 core case IDs from Step 2 §8. The level-B ones will fail — the units
do not exist until step 5 — and that is expected and recorded, not a defect.
