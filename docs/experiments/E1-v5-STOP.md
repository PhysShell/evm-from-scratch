# E1-v5 — STOP_PROTOCOL_STEP6A_NONCONFORMANT

**Outcome:** E1-v5 halts at Step 2 §10 step 6a. `M1` was not written and no adjudicating
figure was produced.

**What the outcome means.** The **v5 freeze itself remains valid**; step 6a happened, and
therefore finalised that freeze. But the step 6a *execution* is **not admissible as an
execution of frozen §8.2.1/§8.2.2**. No `LT-BR-*` ID, candidate index, first-stop identity, or
branch-search figure produced by that execution may be promoted to frozen-procedure evidence.

**Two independent reasons are preserved under that outcome**, and neither subsumes the other:

1. **The frozen procedure is underspecified** — no total inter-file arm order is defined.
   Preserved as its own finding, `STOP_PROTOCOL_ARM_ORDER_UNDERSPECIFIED` (§2).
2. **The executed search was nonconformant** with the parts of the generator that *were*
   defined (§3).

An earlier version of this record named reason 1 as the whole disposition. That was too
narrow: it presented a specification defect as the only blocker while the execution that
exposed it was itself not an execution of the specification.

---

## 1. What was executed, and under what status

The implementation iterated files in the order its coverage extractor produced them,
alphabetically by repository-relative path:

```text
call.ts -> dec.ts -> jmp.ts -> mem.ts -> opcodes.ts -> ret.ts -> run.ts -> sto.ts
```

Under that order, and only under it, the run reported:

```text
budget                B = 4096
|D_program|           37
uncovered arms        45          from the 213 core tests alone
arm identity          103 by source position, 20 by matched sibling, 0 disagree

LT-BR-U-CALL-001      src/call.ts:44:42 binary-expr#1     candidate 796
LT-BR-U-DEC-001       src/dec.ts:22:25  binary-expr#1     candidate 1
NO_FROZEN_BRANCH_WITNESS
                      src/jmp.ts:17:27  binary-expr#1
```

> **These figures are NON-ADMISSIBLE PROTOCOL EVIDENCE.**
>
> They are preserved as a historical observation of one tool in one environment. They are
> **not** §8.2.2 results. The `LT-BR-*` IDs above are not allocated; the candidate indices are
> not frozen indices; the first stop is not the frozen procedure's first stop. The same applies
> to the `103 / 20 / 0` alignment figures and to the candidate-11 `RangeError` in §4.

**No `LT-BR-*` ID is selectively salvaged.** Reconstructing the frozen stream happens to place
the U-CALL fixture inside the budget as well (§3.1), and that is *not* a reason to keep
`LT-BR-U-CALL-001`. An ID allocated by a nonconformant run is not made frozen evidence by the
observation that a conformant run might also have reached it.

## 2. Reason one — the frozen procedure does not determine its own result

§8.2.2 iterates uncovered arms "in frozen source order" and §8.2 allocates `LT-BR-*` IDs "in
ascending order of source position", but **no frozen text defines a total order between
files.** Three concrete admissible orders are under discussion, and they yield three distinct
results:

```text
executed alphabetical   call -> dec -> jmp -> ...   two witnesses emitted, then the jmp.ts
                                                    arm exhausts B
§1.3 unit order         U-DEC and U-JMP both precede U-CALL, so the run takes dec.ts's
                        witness, reaches jmp.ts and stops — and LT-BR-U-CALL-001 is never
                        emitted at all. The realised prefix of the ID allocation differs.
mem.ts before jmp.ts    U-MEM's operand domain contains 2²⁵⁶ − 1, which asks the host for an
                        allocation it cannot make; that is E1-v5 §3.10's evaluation stop, and
                        it fires at candidate 11. The run ends with a preserved candidate
                        index and error class instead of NO_FROZEN_BRANCH_WITNESS.
```

Three admissible orders, three different outcomes, and the frozen procedure selects none of
them.

**This is not repaired in v5.** Step 6a was the first measured run, so adding a file-order rule
now would choose, after seeing three candidate outcomes, which of them becomes the record —
the precise move the freeze exists to prevent, and a worse instance of the one v4 was refused
for.

## 3. Reason two — the executed search did not implement the defined generator

Where §8.2.1 and §1.3 *do* define the record, the tool departed from them. Four instances,
each verified against the frozen text and by execution:

### 3.1 `Frame.pc` omitted from the record

§8.2.1 states "`Frame.memory` and `Frame.returndata` draw from `bytes`; **`Frame.pc` from
`uint256`**", and, arguing for index-sum ordering, "**`Frame` has nine fields** and about
295 000 combinations". `src/domain.ts` carries the binding comment `Declaration order is the
§8.2.1 enumeration order`, with `pc` declared second of nine.

`tools/branch-search.ts` has an eight-entry `FRAME_FIELDS` and hard-codes `pc: 0`. Every
Frame-based unit — `U-RUN`, `U-CALL`, `U-STO`, `U-GRD`, `U-HLT`, `U-RET` — therefore enumerated
a stream that is not the frozen stream. Replaying both, for the recorded U-CALL fixture:

```text
index under the executed stream (pc omitted)      796
index under the reconstructed frozen stream       886
```

### 3.2 `U-HLT` invents an input dimension

Frozen §1.3 declares `U-HLT`'s inputs as **`frame, offset, len`**. The tool adds a `halt`
field, so `U-HLT`'s candidate stream is not the frozen stream either.

The same field is also self-inconsistent: `exercise` passes `RETURN`/`REVERT` while `describe`
reports `NORMAL`/`EXCEPTIONAL`, so a `U-HLT` witness would have recorded an input never
supplied. Renaming the domain would make the report honest while leaving the stream wrong —
the defect is the invented dimension, not the label.

For contrast, `U-RET`'s `halt` field **is** legitimate: §1.3 gives it `frame, a FrameResult`,
and `FrameResult.halt` genuinely ranges over `NORMAL`/`EXCEPTIONAL`.

### 3.3 The byte domain became runtime state

`src/mem.ts` `ensure()` returns early when the buffer already covers the write, and `mstore`
then writes **into that same buffer**. `D_BYTES[2]` is exactly one word, so it takes the early
return. The `U-MEM` record hands the domain member in directly as owned state, and `frameFrom`
does the same for `memory` and `returndata`. Executed against the real unit:

```text
bytes[2] before   66,66,66,66,66,66,66,66 …
bytes[2] after    0,0,0,0,0,0,0,0 …
same object       true
```

One candidate destroys a member of the frozen domain for every later candidate and every later
arm in the same process. A canonical finite domain is a constant of the procedure; here it was
mutable state, and enumeration became history-dependent.

### 3.4 Instrumentation provenance was not bound

`istanbul-lib-instrument` (6.0.3) and `source-map` (0.7.6) are present only transitively —
neither is declared in `package.json`, and neither appears in `M0-v5`'s `toolchain` set. The
instrumenter fixes arm enumeration order and the source-map consumer fixes arm positions, so
these two decide every ordinal that every witness and the stop are stated against.

The committed lockfile preserves what happened *ex post*, but `manifest-replay` checks only
names present in `m0.toolchain`. Those result-bearing versions were therefore not constrained
by `M0`, and could have changed between `M0` and measurement while replay stayed green.

## 4. Known implementation defect — a tooling gap can masquerade as a verdict

A missing `UnitRecord` and a missing instrumentation entry both fall through toward
`unwitnessed`, which the report prints under the `NO_FROZEN_BRANCH_WITNESS — Step 2 §8.2.2`
heading. §8.2.2 defines that outcome for an arm no candidate covers within `B`; a tooling
failure is not that.

Both branches are unreachable in this run, so nothing recorded changes because of it. It is
**recorded here as a known defect rather than repaired**, and `E1-v6` must fail closed instead.

The candidate-11 `RangeError` in `U-MEM` is preserved on the same footing as everything else in
§1 — a historical observation of this tool and environment, showing that the §3.10 condition is
reachable in a unit whose operand domain contains `2²⁵⁶ − 1`. It is not a §8.2.2 result.

## 5. What the `jmp.ts` arm is — preserved as a source observation

```ts
while (pc < code.length) {
  const op = code[pc] ?? 0;          // the arm is the `?? 0`
```

The arm executes only when `code[pc]` is `undefined`, and the loop condition guarantees it is
not. It exists because `noUncheckedIndexedAccess` types the index access as possibly-undefined,
so the fallback is written for the type checker rather than to describe a reachable state.

**The same idiom one file away is genuinely reachable.** `src/dec.ts:22` is also `code[pc] ?? 0`
and is legitimately called past the end of code when a `PUSH` immediate is truncated —
`SEM-DEC-3`, a frozen postcondition. Identical source, identical arm type, dead in `U-JMP` and
live in `U-DEC`, and nothing in a coverage report distinguishes them.

This is an observation about the source, readable without running anything, so it survives both
reasons above. What it is **not** is a verdict the procedure delivered: §8.2.2 is explicit that
"whether the arm was *truly* unreachable or merely unreached within `B` is not decided, and does
not need to be".

## 6. Arm identity — what was established, and what it now supports

Every reported result targets arms by ordinal, so it means nothing unless the k-th arm of a
file is the same arm in both instrumentations. That was established rather than assumed, and
the first attempt at establishing it was rejected:

```text
REJECTED     comparing per-file sequences of istanbul `type` strings. A permutation among
             adjacent same-typed arms passes unchanged, and src/jmp.ts alone opens
             `binary-expr, binary-expr, if, if`. Re-running the search does not test this,
             because the rerun goes through the same matcher.

ESTABLISHED  each arm's own generated-JS position mapped back through the transpiler's
             source map and compared with the TypeScript position the discovery run recorded
             for that ordinal:
                 103  matched by source position
                  20  positionless implicit-else arms, each identified by a sibling that
                      matched positionally — istanbul gives an `if`'s implicit else no
                      location on either side
                   0  disagreements
```

`tools/verify-arm-alignment.ts` performs it and the search refuses to run when it fails. Under
this disposition it establishes an internal correspondence within a nonconformant run — and,
per §3.4, it does so under instrumentation versions `M0` never bound.

## 7. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no
defect was injected, and no calibration figure exists. `M1` does not exist, and **E1-v5 §7** —
the preregistration's sequence, not §7 of this record — makes it a precondition for any
adjudicating figure.

**Predictions P1–P4 are unadjudicated.** The run stopped at the third file in its own order,
before any `U-RUN` dispatch arm, so P1 and P2 were never tested and P3/P3′ never arose.

**Amendment `A2` is neither validated nor falsified by step 6a.** `A2` remains frozen and
untouched, and neither defect above is about it. But its support may not be drawn from this
run: the two witnesses are non-admissible, so they are not evidence for anything. What stands
independently is binding rule 5's replay of `D_program` — and only the preregistered
program-domain shape and properties that replay actually checks.

**Clean Baseline B stands**, inherited unchanged and unmeasured under v5, carrying the recorded
limitation that at least 4 case IDs incompletely realise 2 frozen postconditions. Every defect
above is in the search tooling; none is in `src/`.

## 8. Preserved chain

```text
8f5aaed   PR #5 — the stopped, never-frozen v4 closed into `main`
   │
2b640e7   the E1-v5 preregistration, reviewed
   │
f670258   FREEZE EVENT (E1-v5) — §4.1 (a)-(e) all PASS, and still valid
   │
baf6eb3   M0-v5 and the D_program generator — no measurement
   │
   └────── step 6a: executed, finalising the freeze, and NOT admissible as an execution
           of frozen §8.2.1/§8.2.2
```

PR #8 closes this history. It merges as **history closure**, by ordinary merge preserving the
audit chain — **not** as a successful measured step 6a.

## 9. Continuation — what `E1-v6` must freeze before executing anything

```text
(a) a TOTAL ARM ORDER, determined by the specification alone — a rule over units, files and
    positions that two independent implementers would realise identically — and frozen
    without reference to which arms are currently red, since all three outcomes in §2 are
    already known.

(b) the exact PER-UNIT INPUT-RECORD CONSTRUCTION from §1.3 + §2, including `Frame.pc` and
    with no invented dimensions.

(c) FRESH OR IMMUTABLE candidate values, so enumeration is history-independent.

(d) EVERY RESULT-BEARING INSTRUMENTATION DEPENDENCY in the bound toolchain, and checked by
    replay — transitive presence is not binding.

(e) FAIL-CLOSED treatment of missing records, missing arm mappings and tooling gaps, so a
    tooling failure can never print as a frozen-procedure verdict.
```

Prefer **one canonical record-schema source** from which the generator is constructed, rather
than another handwritten table plus a checker for that table. Both defects in §3.1–§3.2 are
exactly what a handwritten second copy produces.

The question v6 already inherited stands, now third in line: **what the branch-completion rule
does with an arm that cannot execute.** Step 0 §3.1.3 rule 2 asks for one test per uncovered
branch; §8.2.2 turns an unwitnessable arm into a stop; neither anticipated arms that exist only
to make an expression total.
