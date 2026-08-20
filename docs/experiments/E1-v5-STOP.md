# E1-v5 — NO_FROZEN_BRANCH_WITNESS

**Outcome:** E1-v5 halts at Step 2 §10 step 6a. `M1` was not written, and no adjudicating
figure was produced.

**Cause:** an uncovered branch arm that **no candidate can cover, because it cannot execute at
all** — the `?? 0` fallback in a loop whose own condition guarantees the index is in range.
`A2` worked; the domain reached the arms it was built to reach. What stopped the run is a
collision between the frozen plan's rule *"one test per uncovered branch"* and arms that exist
to satisfy a type checker rather than to describe a reachable state.

This is a decision record. The full measurement is
[`records/step6a-branch-search.md`](../../experiments/e1/records/step6a-branch-search.md).

---

## 1. What the procedure returned

```text
budget                B = 4096
|D_program|           37
uncovered arms        45          from the 213 core tests alone
arm alignment         verified for every file

witnesses emitted     2
  LT-BR-U-CALL-001    src/call.ts:44:42 binary-expr#1     candidate 796
  LT-BR-U-DEC-001     src/dec.ts:22:25  binary-expr#1     candidate 1

NO_FROZEN_BRANCH_WITNESS
  src/jmp.ts:17:27    binary-expr#1
```

## 2. The arm

```ts
while (pc < code.length) {
  const op = code[pc] ?? 0;          // arm #1 is the `?? 0`
```

The arm is taken only when `code[pc]` is `undefined`; the loop condition guarantees it is not.
`noUncheckedIndexedAccess` types the index access as possibly-undefined, so the fallback is
written for the type checker. It is not reachable, and enlarging any domain cannot make it so.

**The same idiom one file away is reachable**, and that is what makes this a finding rather
than a curiosity. `src/dec.ts:22` is also `code[pc] ?? 0` and took a witness at the **first**
candidate, because `decode` is legitimately called past the end of code when a `PUSH` immediate
is truncated — `SEM-DEC-3`, a frozen postcondition. Identical source, identical arm type,
reachable in `U-DEC` and dead in `U-JMP`. Nothing in a coverage report distinguishes them.

## 3. What this stop is, and is not

**It is not the v3 stop again.** v3 stopped because the candidate generator could not produce
programs at all: `Frame.code` drew from a `bytes` domain whose members contained no opcode, so
30 dispatch arms were unreachable *from the domain*. Under `A2` that is fixed, and the two
witnesses above are the evidence — `U-DEC`'s arm fell on candidate 1, `U-CALL`'s on candidate
796, both well inside `B`.

**It is not a defect in `A2`.** The stopping arm is in `U-JMP`, its input record is
`(program, target)`, and no program can reach it.

**The procedure did not decide reachability, and §2 above is not a verdict it delivered.**
§8.2.2 is explicit that "whether the arm was *truly* unreachable or merely unreached within
`B` is not decided, and does not need to be" — that is what makes it terminate. §2 is an
observation about the source. The stop is identical either way.

**Predictions P1–P4 are not adjudicated by this run.** The search stopped at the third arm in
source order, before reaching any `U-RUN` dispatch arm, so P1 and P2 were never tested and P3
and P3′ never arose. They stand as written, unresolved, for a successor to test.

## 4. What was learned about §3.10, without it firing

The §3.10 evaluation-stop condition — a host-level exception yields no coverage verdict, so
the run stops and no next candidate is tried — **did not fire in this run**, because the
`NO_FROZEN_BRANCH_WITNESS` arm precedes `U-MEM` in frozen source order.

An earlier, incorrect execution of the same procedure surveyed all arms instead of halting at
the first exhausted one, and reached a `RangeError` in `U-MEM` at candidate 11. That run's
outcome is void — the tool was corrected to halt where §8.2.2 says to halt, and re-run — but
one thing it establishes is not void: **the §3.10 condition is reachable, early, in a unit
whose operand domain contains `2²⁵⁶ − 1`.** It is not a theoretical clause. A successor that
gets past `U-JMP` will meet it.

## 5. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no
defect was injected, and no calibration figure exists. This is the fourth stop across five
versions, and the sentence is owed each time: a growing pile of stop records is not a growing
pile of negative findings.

**Clean Baseline B stands**, inherited unchanged and unmeasured under v5, carrying the recorded
limitation that at least 4 case IDs incompletely realise 2 frozen postconditions.

## 6. Preserved chain

```text
8f5aaed   PR #5 — the stopped, never-frozen v4 closed into `main`
   │
2b640e7   the E1-v5 preregistration, reviewed
   │
f670258   FREEZE EVENT (E1-v5) — §4.1 (a)-(e) all PASS
   │
baf6eb3   M0-v5 and the D_program generator — no measurement
   │
   └────── step 6a: 2 witnesses, then NO_FROZEN_BRANCH_WITNESS, this record
```

## 7. Continuation

`E1-v6` inherits everything and must resolve one question the frozen plan does not currently
answer: **what the branch-completion rule does with an arm that cannot execute.**

Step 0 §3.1.3 rule 2 says one test per uncovered branch, and §8.2.2 turns an arm it cannot
witness into a stop. Neither anticipated arms that exist only because the type system demands a
total expression. Three shapes of answer are available, and the choice belongs to review, not
to the author:

```text
(a)  narrow what counts as an uncovered arm, by a criterion frozen in advance and
     applied without looking at which arms are red
(b)  keep every arm in scope and accept that the plan cannot be completed, making
     this stop the terminal state of the branch-completion rule
(c)  change the production code so the arm does not exist — which changes clean
     Baseline B, and so cannot be done under an inherited baseline
```

Whichever is chosen, `A2` carries forward untouched: it did what it was written to do, and
this stop is downstream of it rather than about it.
