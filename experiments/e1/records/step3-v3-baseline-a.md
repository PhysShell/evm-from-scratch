# Step 3 record — Baseline A, under E1-v3

Executes Step 2 §10 step 3 under
[E1-v3](../../../docs/experiments/E1-v3-preregistration.md), the first version of this
experiment whose freeze event actually occurred before its measurement.

**This measurement makes the E1-v3 freeze final.** A gap found after it is stop-and-preserve
continuing as `E1-v4`, never an in-place edit.

## Provenance

```text
freeze_merge_sha      bd363066c9000867d54c81f60bdd0a5b9883e025
                      merge of PR #3, reviewed at head 9ad1031 by the repository owner

target_revision_sha   39b1b4b8113e9900a69579cdbb13f896e9b1c63b
                      the commit containing M0-v3, and the revision this run was taken on.
                      Derived by replay from `git rev-parse HEAD` at run time, not read
                      from the manifest — M0-v3 lives inside this commit and a field in it
                      would describe its own container (E1-v3 §3.2 rule 3).

manifest              manifest/M0-v3-protocol.json
```

## The freeze predicate, verified positively for the first time

E1-v3 §3.1 was written and exercised only against impostors: the merge of PR #2, an earlier
PR head, and a manifest declaring a forged base. All were rejected. This is its first
**passing** evaluation, on the merge that really is the freeze event:

```text
freeze event bd363066c900 — E1-v3 §3.1
ok    manifest freeze_base_sha matches the frozen literal
ok    manifest freeze_path matches the frozen literal
ok    freeze (a) is a two-parent merge
ok    freeze (b) first parent is the frozen base
ok    freeze (c) path absent at ^1
ok    freeze (d) path present at ^2
ok    freeze (e) merged blob is the landed blob
     measured target (HEAD) 39b1b4b8113e
ok    freeze ordering: HEAD is a descendant of the freeze
```

`bd363066^2` is `9ad1031` — precisely the head the owner reviewed. That equality is what
clauses (d) and (e) exist to pin: the document `main` now carries is the document that was
reviewed, not something a merge resolution could have substituted.

## What was measured

The Baseline A implementation is **unchanged** from `affde50`, where it was first written.
It has now been measured three times with identical results; only the protocol under which
the measurement was taken has changed, which is the entire content of v2 and v3.

| | Result |
|---|---|
| level-A oracle slice | **49/49 pass** (50/50 including the M0 length guard) |
| manifest replay | **all checks pass**, including the freeze predicate |
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

### Still not qualification evidence

Third time stated, because it does not become inherited by repetition: these figures come
from the **oracle suite**, which Step 0 §3.2.1 bars from producing coverage, mutation or
local-detection evidence. The §3.3 thresholds apply to the frozen local suite over
`seam_adjacent_region` at step 6b. The 213 core tests arrive at step 4; the seam at step 5.

## Per-test semantics

Re-confirmed on this run, not carried over: `coverageAnalysis` explicitly `perTest`, and
**11.64 tests per mutant** against a 50-test suite. A silent degradation to `all` would read
50. This is the P-038 §3.3 warning discharged for StrykerJS 10.0.0.

## Version chain

```text
E1-v1   STOP_SPECIFICATION_CONFLICT     Step 0 §1.1 vs Step 2 §3.1 over GAS
E1-v2   STOP_PROTOCOL_FREEZE_ORDER      the declared freeze event never occurred
E1-v3   freeze event bd363066, measurement 39b1b4b — in force
```

Both stops are preserved and replayable: `E1_MANIFEST` selects `M0-protocol.json` or
`M0-v2-protocol.json`, which declare no `freeze_merge_sha` and skip the predicate with an
explicit note.

Neither stop is a result about boundary blindness, and this record is not one either. No
specimen has been built, no seam exists, no defect has been injected, and no calibration
figure has been produced.

## Next

Step 4: write all 213 core case IDs from Step 2 §8 — 166 level-A, which should pass, and 47
level-B, which will fail because the units do not exist until step 5. That failure is
expected and recorded, not a defect.
