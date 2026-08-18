# Findings against the E1-v3 artifacts, from external review

**Provenance:** a CodeRabbit full review of PR #4, 2026-08-18, run against
`bd363066..c054ef9`. Every finding below was re-verified against the source before being
accepted or rejected here; two of the bot's five nitpicks are not reproduced because they
are style preferences with no bearing on evidence.

**Why this file exists.** Three of the findings are real and land on artifacts that are
frozen. They cannot be repaired without breaking the invariant that makes the artifacts
evidence, so the only honest thing left is to write them down where anyone reading the
Step 5 record will also read this one.

---

## 1. Repaired

### `E1-v3-STOP.md` §2 misstated why the budget is irrelevant

The text claimed *"the fourth candidate already exhausts the `code` domain"*. That is false
under the §8.2.1 index-sum order, and it contradicted the tool output quoted two lines above
it, which says `exhausted at index-sum 3`.

```text
candidate 1   code index 0   (sum 0)
candidate 2   code index 0   (sum 1)
candidate 3   code index 0   (sum 1)
candidate 4   code index 0   (sum 1)      <- the claim was about this one
candidate 210 code index 3   (sum 3)      <- where the domain is actually exhausted
```

Corrected in place. **The conclusion is untouched**: 210 is well inside `B = 4096`, the
domain is finite and fully enumerated, and raising `B` still cannot help. Only the reason
given for it was wrong.

---

## 2. Real, frozen, and therefore recorded rather than fixed

Step 5's first invariant is that the 213 core tests were not edited — `git diff 2964098 --
test/core/ test/support/` is empty, and that emptiness is what makes the red → green
transition a transformation of production code alone. Editing a frozen test now would buy a
better test at the cost of the only property that made the suite evidence.

There is a second reason, and it is the stronger one. These tests were derived from a frozen
postcondition list *before* the implementation existed. Strengthening one now — after seeing
the implementation, and after an external tool pointed at it — converts a preregistered case
into an authored one. That is the same move Step 2 §8.2.2 forbids for branch fixtures, and it
is forbidden here for the same reason.

### 2.1 `LT-SEM-CALL-5` is vacuous

```ts
const before = stack.length;                                  // 7 for CALL, 6 otherwise
const ops = c.popOperands(kind, [...stack]);                   // a COPY is passed
expect(ops['gas']).toBe(MAX_UINT256);
expect(before - (kind === 'CALL' ? 7 : 6)).toBe(0);            // always 0, by construction
```

The final assertion compares a length the test itself just built against the constant it
built it from. It holds for every possible implementation of `popOperands` and cannot fail.
Worse, the operand stack is passed as a spread copy, so whether `popOperands` consumed
anything is never observed at all.

**What survives:** `ops['gas'] === MAX_UINT256`. `SEM-CALL-5` says the `gas` operand is
consumed and otherwise ignored; the case establishes that it is *read from the right
position*, and establishes nothing about consumption.

### 2.2 `LT-SEM-STO-4` does not exercise the halt it is named for

`SEM-STO-4` is the deliberate amputation of storage rollback: *an exceptional halt does not
undo storage writes already performed in that frame.* The case performs one `sstore` and
asserts the value landed. No halt occurs.

```ts
const w = world();
sto().sstore(w, frameWith({ storage_owner: AAA }), 0n, 0x42n);
expect(w.get(AAA)?.storage.get(0n)).toBe(0x42n);
```

As written it is a duplicate of `LT-SEM-STO-1`. The postcondition that motivated the
amputation — and that Step 2 §3.2 argues for at length — has no local witness.

### 2.3 `LT-SEM-STK-4` / `LT-SEM-STK-5` assert selected positions only

`DUPn` and `SWAPn` check the depth and the one or two entries the postcondition names. An
implementation that also corrupted an unrelated entry would pass. Weaker than it could be,
but not vacuous: both cases can fail.

### 2.4 What this does and does not do to the Step 5 claim

**"213/213 green" remains true and remains a count.** It was never a strength claim, and
§3.2.1 already bars the local suite from producing coverage or mutation evidence on its own.
What changes is that at least one of the 213 is now known to be unfalsifiable, so the count
overstates the suite by one case, and by two against the postcondition list.

**No adjudicating figure is contaminated.** The only mutation and coverage figures taken
under v3 belong to Baseline A, which is level A only; `SEM-CALL-5` and `SEM-STO-4` are both
level B. The step-6a discovery figures were never quoted and are not quoted here.

**It sharpens rather than weakens the experiment's own question.** E1 asks whether locally
strong evidence can miss a boundary defect. A local case that cannot fail is a reminder that
"strong" has to be measured, not counted — which is exactly what step 6b was going to
measure, and why §10 splits it from 6a.

---

## 3. Real defects, out of scope for repair on this revision

Both are genuine, both were reproduced, and neither can be fixed without inventing semantics
the frozen §3 does not contain.

### 3.1 Unbounded memory offsets escape the `ExceptionalHalt` contract

`ensure()` in `src/mem.ts` allocates `Math.ceil(end / 32) * 32` bytes with no upper bound. A
256-bit offset reaches `new Uint8Array(1.15e77)`, which throws a host `RangeError`. `execute`
converts only `ExceptionalHalt`, so the error escapes `run` — the model's unbounded memory
meeting a real machine.

**Independently reproduced** while checking the E1-v4 program domain, before this review
arrived: operand value `2²⁵⁶ − 1` throws `Invalid typed array length` on every terminal
variant.

**Not fixed here.** Frozen §3 states no addressable bound, so any guard would have to pick
one, and a picked constant is a semantic rule that no postcondition licenses. It also changes
`src/mem.ts`, and the clean Baseline B at `073074b` is the artifact E1-v4 inherits without
re-run.

### 3.2 Recursive dispatch has no call-depth bound

`executeCall` calls `execute` with no depth parameter, so a self-call or a call cycle throws
`RangeError: Maximum call stack size exceeded` — again outside the `ExceptionalHalt`
contract. `SEM-STK-7` bounds the *value* stack at 1024; nothing bounds the *call* stack.

**Unreachable under v3, reachable under v4.** It needs a callee whose code calls back, which
needs `World[a].code` to be a real program — which is precisely what the v3 candidate
generator could not produce and what amendment `E1-v4/A2` introduces. So A2 opens this path.

**Not fixed here,** for the same reason as §3.1: a depth limit is a semantic rule, and the
frozen §3 has none.

### 3.3 How E1-v4 handles both

`E1-v4` §3.10 already treats them, and this review is evidence that the section was needed:

> A candidate whose evaluation raises a host-level error outside the frozen semantics —
> anything that is not `ExceptionalHalt` — is recorded as NOT COVERING the arm. The search
> proceeds to the next candidate. The event is logged with the candidate index and the error
> class, and it is not evidence about the specimen.

That is a rule about the *search*, not a repair of the *semantics*. Both defects remain, and
closing either one requires a preregistered amendment — which E1-v4 does not make, because it
makes exactly one.

---

## 4. Rejected

| Finding | Why not |
|---|---|
| `popOperands` should return a discriminated type instead of `Record<string, bigint>` | The bot withdrew it itself: the frozen `levelb.test.ts` contract declares the same loose shape, so the type cannot move while the test is frozen. |
| `loadUnit` conflates a missing module with one that throws while loading | Correct in principle, and `test/support/units.ts` is inside the frozen tree. The step-4 red state it governs is already recorded and past. |
| `verify-plan.ts` should reset `section` outside `### 3.x` | Latent only. The bot confirms it changes no current output — the sole later `SEM-REL-3` row inherits `3.7` and is level B either way. Not worth a change to a tool whose behaviour the Step 4 and Step 5 records describe. |
| Docstring coverage 75% below an 80% threshold | A CodeRabbit default, not a project rule. |
