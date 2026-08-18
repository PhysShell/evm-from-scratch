# E1-v3 — STOP_NO_FROZEN_BRANCH_WITNESS

**Outcome:** E1-v3 halts at Step 2 §10 step 6a. No `M1` was written, and no adjudicating
figure was produced.

**Cause:** the frozen candidate generator cannot construct a witness for 30 branch arms of
the `U-RUN` dispatch — not within the budget, and not for any budget. A defect in the frozen
specification, discovered by executing it.

This is a decision record. Step 2 §8.2.2 names the consequence exactly: *stop the run,
preserve the record, continue only as a new preregistration. A hand-written fixture to close
this gap is prohibited.*

---

## 1. What the procedure returned

```text
budget                 B = 4096
candidates enumerated  4096
distinct code bytes    0x42
frozen code domain     4 values, exhausted at index-sum 3

U-RUN dispatch arms          30
reachable from frozen code   0
NO_FROZEN_BRANCH_WITNESS     30
```

## 2. Why, and why the budget is irrelevant

`Frame.code` is typed `bytes` in Step 2 §2, so §8.2.1 supplies it from the frozen `bytes`
domain:

```text
bytes    empty, 0x42, 0x42×32, 0x42×33      (4)
         — empty, short, exactly one word, over one word
```

Those four values were chosen as representative *byte strings*. But `Frame.code` is not a
byte string in any useful sense — it is a **program**. A `case X:` arm of the interpreter's
dispatch executes only if opcode byte `X` appears at an instruction position in
`frame.code`, and `0x42` is not an opcode of the frozen subset. Every candidate therefore
either has empty code, so the loop is never entered, or all-`0x42` code, which reaches the
`default:` arm and halts exceptionally.

The domain is finite and was enumerated in full, so this is **exhaustive, not a sampling
result**: raising `B` cannot help, because the `code` domain is exhausted at index-sum 3,
which the enumeration reaches well inside the budget — the fourth and last `code` value first
appears at candidate 210 of 4096. Every one of

```text
STOP ADD SUB MUL DIV MOD LT GT EQ ISZERO POP JUMP JUMPI JUMPDEST PC
GAS ADDRESS CALLER MSTORE MLOAD MSIZE SLOAD SSTORE RETURN REVERT
RETURNDATASIZE RETURNDATACOPY CALL STATICCALL DELEGATECALL
```

is unreachable.

**A second reading stops just as hard.** §8.2.1 names domains explicitly for
`Frame.memory`, `Frame.returndata`, `Frame.pc`, `TxContext.to` and `TxContext.from`, but
never says in so many words which domain `Frame.code` draws from. If the answer is "the
`bytes` domain", the above applies. If the answer is "none is assigned", then the record
product §8.2.1 defines is undefined for `Frame`, and the generator does not specify a stream
at all. Either way the frozen procedure cannot proceed.

**Scoping it to the seam would not save it.** The dispatch arms for `CALL`, `STATICCALL` and
`DELEGATECALL` are among the 30, and those are unambiguously seam-adjacent — the seam is
inside `U-CALL`, which `U-RUN` dispatches to. Narrowing the region changes the count, not the
outcome.

## 3. Why this is a stop and not a small fix

The repair is obvious and would take minutes: give `Frame.code` a domain of small real
programs — one instruction per frozen opcode, say — and the arms become reachable.

That is exactly why it is a stop. The whole point of §8.2.2's rule is that at this moment,
mid-qualification, the tempting move is to write the fixture that closes the gap and carry
on. Doing so would replace a frozen, enumerable generator with an authored one, and the
branch-completion tests would stop being derived from a preregistration and start being
chosen by the person who saw which branches were red.

E1-v3's first measured run happened at `39b1b4b` (Baseline A), so its freeze is final under
Step 0 §0 and E1-v3 §3.3. The generator cannot be amended in place.

## 4. What the step-6a discovery run did, and did not, establish

The discovery run was executed over the **213 core tests alone** — `test/core/` only, seven
suites, 213 cases. `oracle-a`, `oracle-b`, the composition witnesses and `c2_control_suite`
were all excluded, because Step 0 §3.2.1 confines local evidence to the frozen local suite
and a branch covered by the oracle is not a branch covered locally.

**Its coverage figures are discovery output and are not reproduced here.** They were produced
to locate uncovered arms and may never be cited as baseline adequacy or as §5.3 condition-3
evidence. §10 splits 6a from 6b precisely so that this cannot happen by accident, and a stop
at 6a is not an occasion to start quoting them.

It found 49 uncovered arms, of which 22 are `U-RUN` switch arms. That count is a property of
the discovery run; the 30 unreachable dispatch arms above are a property of the frozen
domain, and the two numbers answer different questions.

## 5. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no
defect was injected, no calibration figure exists. This is the third E1 stop and the third
time worth saying plainly: a growing pile of stop records is not a growing pile of negative
findings.

**Clean Baseline B stands.** 213/213 core green, both oracle slices green, the frozen tests
never edited. It carries into the next version unchanged, exactly as Baseline A carried
through v2 and v3.

## 6. Preserved chain

```text
bd36306   freeze event (E1-v3)
   │
39b1b4b   M0-v3 — first measured run under v3, freeze final
   │
aeac233   v3 Baseline A measurement
   │
2964098   the 213 frozen tests, red
   │
20d87be   verifier strengthened to check the partition
   │
073074b   clean Baseline B — 213/213 green
   │
   └────── step 6a: NO_FROZEN_BRANCH_WITNESS, this record
```

## 7. Continuation

`E1-v4` inherits everything and amends one thing: the `code` field's domain in the candidate
generator. The amendment must be written and frozen **before** it is used, by the same
merge-event discipline E1-v3 established and which worked — the freeze predicate passed on
its first positive evaluation and has held since.

The amendment is outcome-independent in the sense that matters: it is fixed by what a
`Frame.code` *is*, not by which branches happened to be red. It should be specified as a
domain of programs derivable from the frozen opcode subset — not as the particular fixtures
that would cover today's 30 arms.
