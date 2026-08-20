# E1-v5 — STOP_PROTOCOL_ARM_ORDER_UNDERSPECIFIED

**Outcome:** E1-v5 halts at Step 2 §10 step 6a. `M1` was not written and no adjudicating
figure was produced.

**Cause:** the frozen procedure does not determine its own result. §8.2.2 iterates uncovered
arms "in frozen source order" and §8.2 allocates `LT-BR-*` IDs "in ascending order of source
position", but **no frozen text defines a total order between files.** Different admissible
file orders produce different first stops and different realised `LT-BR-*` prefixes, so what
step 6a returns is a property of the implementation's choice rather than of the specification.

An earlier draft of this record named the outcome `NO_FROZEN_BRANCH_WITNESS`. That was wrong —
not because the observation was wrong, but because it presented one admissible order's result
as *the* result. Review caught it, and the correction is the whole content of this version.

---

## 1. What was actually executed, and under which order

The implementation iterated files in the order its coverage extractor produced them,
alphabetically by repository-relative path:

```text
call.ts -> dec.ts -> jmp.ts -> mem.ts -> opcodes.ts -> ret.ts -> run.ts -> sto.ts
```

Under that order, and only under it, the run returned:

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

**These are observations under the implementation-selected order. They are not the uniquely
determined §8.2.2 result, because there is no such thing under the frozen text.**

## 2. Why the order is result-bearing, in two concrete ways

**Under the §1.3 unit order the `LT-BR` prefix is different.** §1.3 lists the units as
`U-ENTRY, U-DEC, U-STK, U-ARI, U-CMP, U-JMP, U-MEM, U-STO, U-GRD, U-HLT, U-CALL, U-RET, U-RUN`.
`U-DEC` and `U-JMP` both precede `U-CALL`, so the run would take `dec.ts`'s witness, reach
`jmp.ts`, and stop there — and **`LT-BR-U-CALL-001` would never be emitted at all**. The
realised prefix of the frozen ID allocation depends on a choice the specification does not make.

**Under any order placing `mem.ts` before `jmp.ts` the stop is a different kind of stop.** The
`U-MEM` record's operand domain contains `2²⁵⁶ − 1`, which asks the host for an allocation it
cannot make; that is E1-v5 §3.10's evaluation stop, and it fires at candidate 11. So the run
would end with a preserved candidate index and error class rather than with
`NO_FROZEN_BRANCH_WITNESS` on an unwitnessable arm.

Two admissible orders, three different outcomes. The frozen procedure selects none of them.

## 3. What the jmp.ts arm is — preserved, because it is worth preserving

```ts
while (pc < code.length) {
  const op = code[pc] ?? 0;          // the arm is the `?? 0`
```

The arm executes only when `code[pc]` is `undefined`, and the loop condition guarantees it is
not. It exists because `noUncheckedIndexedAccess` types the index access as
possibly-undefined, so the fallback is written for the type checker rather than to describe a
reachable state.

**The same idiom one file away is genuinely reachable.** `src/dec.ts:22` is also
`code[pc] ?? 0` and took a witness on the *first* candidate, because `decode` is legitimately
called past the end of code when a `PUSH` immediate is truncated — `SEM-DEC-3`, a frozen
postcondition. Identical source, identical arm type, dead in `U-JMP` and live in `U-DEC`, and
nothing in a coverage report distinguishes them.

That observation survives the disposition change: it is a fact about the specimen under any
file order, since it concerns one arm rather than the sequence they are visited in. What does
*not* survive is the claim that this arm is where the frozen procedure stops.

**§8.2.2 did not decide reachability and neither does this record.** The frozen text is
explicit that "whether the arm was *truly* unreachable or merely unreached within `B` is not
decided, and does not need to be". The paragraph above is an observation about the source.

## 4. What is established about arm identity

Every result above targets arms by ordinal, so it means nothing unless the k-th arm of a file
is the same arm in both instrumentations. That is now established rather than assumed, and the
first attempt at establishing it was rejected:

```text
REJECTED   comparing per-file sequences of istanbul `type` strings. A permutation among
           adjacent same-typed arms passes unchanged, and src/jmp.ts alone opens
           `binary-expr, binary-expr, if, if`. Re-running the search does not test this,
           because the rerun goes through the same matcher.

ESTABLISHED  each arm's own generated-JS position mapped back through the transpiler's
           source map and compared with the TypeScript position the discovery run recorded
           for that ordinal:
               103 arms matched by source position
                20 positionless implicit-else arms, each identified by a sibling that
                   matched positionally — istanbul gives an `if`'s implicit else no
                   location on either side
                 0 disagreements
```

`tools/verify-arm-alignment.ts` performs it, and the search now refuses to run when it fails.

## 5. Why this cannot be repaired inside v5

Step 0 §0 fixes the governing documents at the first measured run, and step 6a *was* that run.
Adding a file-order rule now would choose, after seeing three candidate outcomes, which of them
becomes the record — the precise move the freeze exists to prevent, and a worse instance of it
than the one v4 was refused for.

So the execution is preserved as executed, and only its normative status changes.

## 6. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no
defect was injected, and no calibration figure exists. `M1` does not exist, and §7 makes it a
precondition for any adjudicating figure.

**Predictions P1–P4 are unadjudicated.** The run stopped at the third file in its own order,
before any `U-RUN` dispatch arm, so P1 and P2 were never tested and P3/P3′ never arose.

**Clean Baseline B stands**, inherited unchanged and unmeasured under v5, carrying the recorded
limitation that at least 4 case IDs incompletely realise 2 frozen postconditions.

## 7. Preserved chain

```text
8f5aaed   PR #5 — the stopped, never-frozen v4 closed into `main`
   │
2b640e7   the E1-v5 preregistration, reviewed
   │
f670258   FREEZE EVENT (E1-v5) — §4.1 (a)-(e) all PASS
   │
baf6eb3   M0-v5 and the D_program generator — no measurement
   │
   └────── step 6a: executed, observed, and stopped on its own underspecification
```

## 8. Continuation

`E1-v6` must **freeze a total order over arms before running anything.** The order has to be
determined by the specification alone — a rule over units, files and positions that two
independent implementers would realise identically — and it must be frozen without reference to
which arms are currently red, since all three outcomes above are already known.

The question v6 inherits from the earlier draft of this record stands unchanged and is now
second in line: **what the branch-completion rule does with an arm that cannot execute.**
Step 0 §3.1.3 rule 2 asks for one test per uncovered branch; §8.2.2 turns an unwitnessable arm
into a stop; neither anticipated arms that exist only to make an expression total.

`A2` carries forward untouched. It did what it was written to do — the domain produced
programs, and the two witnesses are the evidence — and both defects here are downstream of it
rather than about it.
