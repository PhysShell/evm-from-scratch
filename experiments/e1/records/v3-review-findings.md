# Findings against the E1-v3 artifacts, from external review

**Provenance:** a CodeRabbit full review of PR #4, 2026-08-18, run against
`bd363066..c054ef9`. Every finding below was re-verified against the source before being
accepted or rejected here; two of the bot's five nitpicks are not reproduced because they
are style preferences with no bearing on evidence.

**Why this file exists.** Three of the findings are real and land on artifacts that are
frozen. They cannot be repaired without breaking the invariant that makes the artifacts
evidence, so the only honest thing left is to write them down where anyone reading the
Step 5 record will also read this one.

**Revised after owner review, 2026-08-18.** The first draft of §2 got its own accounting
wrong in two ways: it called `LT-SEM-CALL-5` vacuous when only its closing assertion is, and
it counted `SEM-CALL-5` as one case when §3.3 gives it three; and it described `LT-SEM-STO-4`
as a weak duplicate of `LT-SEM-STO-1` when the sharper fact is that frozen §3.2 assigns
`SEM-STO-4` to `U-RUN` and the case exercises `U-STO`. §2.1, §2.2 and §2.4 are rewritten
accordingly, and the superseded wording is named where it stood rather than quietly dropped.
No production code and no frozen test was touched by that revision, or by this file at all.

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

### 2.1 `LT-SEM-CALL-5` witnesses extraction, not consumption — 3 case IDs

```ts
const before = stack.length;                                  // 7 for CALL, 6 otherwise
const ops = c.popOperands(kind, [...stack]);                   // a COPY is passed
expect(ops['gas']).toBe(MAX_UINT256);
expect(before - (kind === 'CALL' ? 7 : 6)).toBe(0);            // always 0, by construction
```

**This is three case IDs, not one.** §3.3 gives `SEM-CALL-5` the case set *all three kinds*,
and the §8 plan lists `LT-SEM-CALL-5/CALL`, `/DELEGATECALL` and `/STATICCALL` accordingly. The
test is an `it.each(KINDS)`, so the defect below is present in each of the three.

**The case is not vacuous, and an earlier draft of this record wrongly called it that.** The
first assertion is falsifiable: an implementation that read `gas` from the wrong stack position
fails it, and that is a real property of `popOperands`.

The *final* assertion is the tautological one. It compares a length the test itself just built
against the constant it built it from, so it holds for every possible implementation and cannot
fail. And because the operand stack is passed as a spread copy, whether `popOperands` consumed
anything is never observed at all.

**What the three cases establish:** `gas` is extracted from the right position.
**What they do not establish:** that it is *consumed* — which is the word `SEM-CALL-5` uses.

**The sharpest form of the problem is in the projection, not the test.** §5.1 admits
`SEM-CALL-1..8` as surviving with an explicit reason:

> operand arity, pop order and consumption are decidable from `U-CALL`'s own stack before and
> after, with no reference to the double's behaviour.

The before-and-after of `U-CALL`'s own stack is exactly the observation the spread copy throws
away. The case forgoes the very observation that justified admitting its postcondition to the
surviving set.

### 2.2 `LT-SEM-STO-4` realises no `U-RUN` postcondition — a projection/realisation mismatch

`SEM-STO-4` is the deliberate amputation of storage rollback: *an exceptional halt does not
undo storage writes already performed in that frame.* The case performs one `sstore` and
asserts the value landed. No halt occurs.

**And the unit is wrong, which is the more serious half.** Frozen §3.2 assigns `SEM-STO-4` to
**`U-RUN`** — it is a statement about what a frame's interpreter loop does when it halts
exceptionally, which is why §3.2 places it there and not with `SEM-STO-1..3`. The case sits in
the `U-STO` block and calls `sto().sstore()` only. It therefore does not exercise the wrong
*scenario* of the right unit; it exercises a different unit altogether.

```ts
const w = world();
sto().sstore(w, frameWith({ storage_owner: AAA }), 0n, 0x42n);
expect(w.get(AAA)?.storage.get(0n)).toBe(0x42n);
```

As written it is a duplicate of `LT-SEM-STO-1`. The postcondition that motivated the
amputation — and that Step 2 §3.2 argues for at length — has no local witness.

**So this is a frozen projection / test-realisation mismatch, and it is the first one found.**
§5.1 states flatly that *every* postcondition of §3.1, §3.2, §3.3, §3.5 and §3.6 survives the
observation projection. `SEM-STO-4` is in §3.2, so §5.1 asserts it is locally decidable — and
the plan allocated it a case ID on that basis. What the plan did not check, and what nothing in
the tooling checks today, is that the case allocated to a surviving postcondition **realises
that postcondition's unit**. `verify-plan.ts` checks the case IDs, their level split, their
uniqueness and their outcomes; it does not check unit/postcondition pairing.

That gap is a finding about the plan, not only about one test, and it is recorded here as one.

### 2.3 `LT-SEM-STK-4` / `LT-SEM-STK-5` assert selected positions only

`DUPn` and `SWAPn` check the depth and the one or two entries the postcondition names. An
implementation that also corrupted an unrelated entry would pass. Weaker than it could be,
but not vacuous: both cases can fail.

### 2.4 What this does and does not do to the Step 5 claim

**"213/213 green" remains true and remains a count.** It was never a strength claim, and
§3.2.1 already bars the local suite from producing coverage or mutation evidence on its own.

The accounting, stated exactly:

```text
213/213 green
    = execution / pass count, and nothing more

known limitations
    3 case IDs   LT-SEM-CALL-5/{CALL,STATICCALL,DELEGATECALL}
                 establish gas extraction, not "consumed"
    1 case ID    LT-SEM-STO-4
                 does not witness its U-RUN postcondition at all

    => at least 4 case IDs incompletely realise 2 frozen postconditions
```

**An earlier draft of this record said the count "overstates the suite by one unfalsifiable
case, and by two against the postcondition list". That was wrong in both numbers and in kind**
— it treated `SEM-CALL-5` as one case rather than three, and it described `LT-SEM-STO-4` as a
weak duplicate rather than as a case pointing at the wrong unit. The figures above supersede it.
"At least" is meant literally: the pairing gap in §2.2 was found by inspection, and nothing has
audited the remaining 209 for it.

**No adjudicating figure is contaminated, for a stronger reason than level.** Level-B
qualification never happened at all — §10 puts it at 6b, and E1-v3 stopped at 6a. There is no
Level-B mutation score, no Level-B coverage figure and no calibration result for these cases to
contaminate. Separately, the only figures that do exist under v3 belong to Baseline A, which is
level A only, while `SEM-CALL-5` and `SEM-STO-4` are both level B. The step-6a discovery figures
were never quoted and are not quoted here.

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
