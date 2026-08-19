# E1-v5 — preregistration

**Status:** a **new** preregistration, opened because
[E1-v4 stopped before its freeze](./E1-v4-STOP.md) with
`STOP_UNFREEZABLE_PREREGISTRATION`. It is not an edit of any earlier document; v1, v2 and v3
remain frozen and stopped, and v4 remains unfrozen, stopped and unmodified.

**Freeze event:** the merge commit that brings *this document* into `main`. Not this
document's own commit, not the merge that closed v4, and not any statement inside it. §4
defines the event by the same identity predicate v3 introduced, which held on its first
positive evaluation and has held since.

**It contains exactly one amendment**, `E1-v5/A2`, carried over unchanged in substance from
the stopped v4. Everything else is inheritance or a stated reading of frozen text.

**Its author knew the v4 dry-run results when writing it.** §3.12 says what that means and
what it forbids. Nothing in this document is derived from them.

---

## 0. Why v5 exists, and what v4 got wrong

E1-v4 was written to carry the amendment below, was reviewed, and was **refused before its
freeze event** on two counts. Both are recorded in [`E1-v4-STOP.md`](./E1-v4-STOP.md); both are
fixed here, and neither is fixed by rewording.

**v4 added a third outcome to a two-outcome procedure.** Its §3.10 said a candidate raising a
host-level error is *"recorded as NOT COVERING; the search proceeds to the next candidate"*.
That is a decision-rule change independent of the amendment it was attached to, and it can
change which fixture is emitted: coverage counters increment as a candidate runs, so a
candidate covering an arm at instruction 40 and throwing at instruction 300 **has** covered it,
and is "the first candidate that covers the arm" in §8.2.2's own sense. §3.10 here replaces
that rule with a reading that adds nothing.

**v4 observed outcomes and then wrote rules from them.** Its §3.12 disclosed a dry run of the
candidate domain executed against the inherited Baseline B, and that run's results determined
the existence and content of its §3.10, the retraction in its §3.9, and its prediction P3′.
Preregistration exists to prevent exactly that ordering. §3.12 here states what is known, where
it came from, and what may be done with it.

The substance — `A2`, a byte string is not an executable program — was not among the defects
and is carried over unchanged.

## 1. Why the amendment exists

E1-v3 executed its frozen branch-search procedure at Step 2 §10 step 6a and the procedure
returned `NO_FROZEN_BRANCH_WITNESS` for 30 arms of the `U-RUN` dispatch. The cause is a defect
in the frozen specification, and it is worth stating in one sentence because the whole of §2
follows from it:

> §8.2.1 assigns candidate domains **by type**, §2 types `Frame.code` as `bytes`, and the
> `bytes` domain's four members — `empty`, `0x42`, `0x42×32`, `0x42×33` — were chosen to be
> representative *byte strings*, which is not what an executable-code field needs to be
> representative of.

`0x42` is not an opcode of the frozen subset, so every candidate the generator can produce has
either empty code or all-`0x42` code that reaches `default:` and halts. The domain is finite
and was enumerated in full, so raising the budget cannot help.

The full record, including why the obvious repair was refused mid-run and why narrowing the
region would not have saved it, is [`E1-v3-STOP.md`](./E1-v3-STOP.md). It is not repeated
here.

**What is not reopened.** No measurement, no threshold, no defect from the Step 0 §6 catalog,
no part of the projection, no digest, and no case ID. v5 changes one clause of one section of
Step 2 and inherits the rest at the blobs `main` carries.

## 2. Inheritance

E1-v5 adopts, unchanged and by reference, these documents at the blobs merged into `main`:

```text
c294d724ce50952db4642f9ef757a3f7a6bf33b6   E1-step0-preregistration.md
586bb92f66d9c6c889a9c2266832264d526a87b4   E1-step2-semantics-and-plan.md
a42fa76f702cfa45664198eea809464d87a7b35f   E1-v2-preregistration.md
```

with amendment **`E1-v2/A1`** (`SEM-RUN-4` is a level-B postcondition) carried forward
verbatim, and every consequence it computed:

```text
postconditions      79      24 + 13 + 7 + 8 + 15 + 6 + 6
surviving           58
excluded            21
core case IDs      213      level split 166 A / 47 B
plan_core_digest         63b4d9f9e1b40a08d2bd3f862ce072fb036bc6401f4360823cc5bfc8d79aae02
c2_control_core_digest   c4273493fd9c001687c9b745df3e1f900a64a3fe746c8d91142298dd3587a051
oracle sets              49 level A / 71 level B in-subset / 6 witnesses / 65 level-B oracle
```

The E1-v3 preregistration is inherited for its §3 (the freeze-event predicate) and §3.2
(binding rules), which §4 below restates with new parameters rather than re-deriving.

---

## 3. Amendment `E1-v5/A2` — a byte string is not an executable program

This is the only amendment. It is one amendment and not three: the sort, the domain and the
field assignment are the premise, the consequence and the application of a single claim, and
freezing any one of them without the others leaves the generator broken in the same way.

### 3.0 The claim

`Frame.code` and `World[a].code` are not byte strings that happen to be executed. They are
**programs**: their meaning is given by §3's decode-and-dispatch semantics, and two values of
the same length are as unrelated as two values of different length. A representative domain
for such a field is representative of *the instructions it can execute*, never of its length
class.

### 3.1 The sort `program`, and the rule that assigns it

Step 2 §2's state model gains one sort. `program` has the same representation as `bytes` —
a finite sequence of octets — and a different domain in §8.2.1. Nothing else distinguishes
them, and no postcondition of §3 is changed by the distinction.

**Assignment rule, mechanical and checkable:**

> A field is of sort `program` **iff** some frozen §3 postcondition supplies its bytes to
> `U-DEC` for decoding. Every other bytes-typed field keeps the sort `bytes`.

The rule, not a list, does the binding. Applying it to §2 as frozen:

| Field | Decoded under | Sort |
|---|---|---|
| `Frame.code` | `SEM-DEC-1..4` decode at `pc`; `SEM-JMP-1` computes the jumpdest set from it; `SEM-RUN-3` bounds the loop by its length | **`program`** |
| `World[a].code` | `SEM-SEAM-P13` makes it the callee frame's `code`, which `U-RUN` then executes | **`program`** |
| `Frame.memory` | never decoded | `bytes` |
| `Frame.returndata` | never decoded | `bytes` |
| `FrameResult.returndata` | never decoded | `bytes` |

Both executable-code fields are bound, which is the point: an amendment that fixed
`Frame.code` and left `World[a].code` as a byte string would leave every callee in the corpus
executing `0x42`, and the seam — the object of the whole experiment — unreachable for exactly
the reason v3 stopped.

### 3.2 The instruction alphabet Σ

**Membership and order are both taken from Step 0 §1.1 and §1.2, as written.** Those two
sections are literal opcode lists and are the definition of the frozen subset; reading them in
order needs no interpretation, and no opcode outside them may enter Σ.

```text
§1.1   STOP, PUSH0, PUSH1..PUSH32, POP, ADD, SUB, MUL, DIV, MOD,
       LT, GT, EQ, ISZERO, DUP1..DUP16, SWAP1..SWAP16,
       JUMP, JUMPI, JUMPDEST, PC                                        80
§1.2   MSTORE, MLOAD, MSIZE, SLOAD, SSTORE, RETURN, REVERT,
       RETURNDATASIZE, RETURNDATACOPY, CALL, STATICCALL,
       DELEGATECALL, ADDRESS, CALLER, GAS                               15
                                                                    |Σ| = 95
```

### 3.3 Operand requirement `need(ι)`, from the frozen postconditions

Each instruction needs a stack state before the frozen semantics says anything about it, and
§3 states what: `SEM-CALL-1` gives `CALL` seven operands, `SEM-STK-4` gives `DUPn` a depth of
`n`, and so on. `need(ι)` is read off §3 and nowhere else.

```text
0   STOP  PUSH0  PUSH1..PUSH32  JUMPDEST  PC  MSIZE  GAS  ADDRESS  CALLER
    RETURNDATASIZE
1   POP  ISZERO  JUMP  MLOAD  SLOAD
2   ADD SUB MUL DIV MOD  LT GT EQ  JUMPI  MSTORE  SSTORE  RETURN  REVERT
3   RETURNDATACOPY
n   DUPn                                      SEM-STK-4, depth n
n+1 SWAPn                                     SEM-STK-5, depth n+1
6   STATICCALL  DELEGATECALL                  SEM-CALL-2, SEM-CALL-3
7   CALL                                      SEM-CALL-1
```

### 3.4 Operand values

Operands are supplied **by their declared type**, which is the same principle §8.2.1 already
uses — applied correctly this time, since it was applying it to `code` by type that produced
the v3 defect.

```text
the `address` operand of CALL / STATICCALL / DELEGATECALL
        §2 declares it `address` in CallOperands_*
        -> frozen §8.2.1 address domain:  ZERO, 0x…0aaa, 0x…0c42, 0x…0dad   (4)

every other operand
        -> frozen §8.2.1 uint256 domain:  0, 1, 2, 2²⁵⁶−1, 2²⁵⁵, 3
           followed by ⟨jd⟩                                                (7)
```

A program is rendered at a **single operand index `j`**, which selects from each operand's own
domain, cycling where the domain is shorter — cycling being §8.2.1's own device for the stack
domain. One shared index rather than a tuple per instruction: a generated program has 334
operand positions, so a per-operand product would exceed 10²⁸⁰ members, and §8.2.2's budget
reaches the first handful of a domain — a product that large is indistinguishable from its
first element.

**`⟨jd⟩` is a symbol, resolved at render time to the offset of the program's trailing
`JUMPDEST`.** It is in the domain because `SEM-JMP-2`'s `VALID_TARGET` case names a jump to a
member of the jumpdest set, and no numeral can name one: the set depends on the program. It is
appended *after* the six numerals rather than placed first because §8.1 rule 1 and §8.2.1
alike order numeric domains boundary-first, and `⟨jd⟩` is not a numeric boundary.

### 3.5 Canonical encoding

```text
push of value v      PUSH32 ++ v as 32 big-endian bytes
enc(PUSHn)           opcode byte ++ 0x42 repeated n times     §8.1 rule 4
enc(ι) otherwise     opcode byte
block(ι, j)          need(ι) pushes of ι's operand values at index j, ++ enc(ι)
```

Operands are pushed with `PUSH32` uniformly, never with the shortest `PUSHn` that fits. Two
reasons, and the second is the load-bearing one: a shortest-encoding rule is a choice, and
uniform width makes every block's length independent of `j`, so `⟨jd⟩` is computable in one
pass instead of by fixpoint.

### 3.6 The grammar, and where its depth comes from

```text
p(j, t)  =  block(ι, j)  for every ι in the PLAIN tier, in Σ order
         ++ block(t, j)                             one terminal instruction
         ++ JUMPDEST                                the ⟨jd⟩ anchor

PLAIN    =  Σ minus the terminal tier minus JUMPDEST                    89
TERMINAL =  ι such that a frozen §3 postcondition says ι halts or transfers
            control: STOP (SEM-RUN-2), JUMP (SEM-JMP-2), JUMPI (SEM-JMP-3),
            RETURN (SEM-HLT-1), REVERT (SEM-HLT-2), in Σ order            5
```

**The grammar's depth is `|Σ|` blocks — the size of the frozen alphabet — and its width is
`need(ι)` operands per block.** Both are read out of the frozen §3 and Step 0 §1.1–§1.2. In
particular neither is derived from, tuned to, or checked against
`experiments/e1/records/step6a-uncovered-arms.json`, which §6.1 forbids as an input.

**Why the terminal instruction is a dimension and not a block.** At most one instruction that
halts or transfers control can execute per program, and §3 names five. A domain that does not
vary the terminal before it varies anything else therefore cannot execute all of Σ, whatever
its other choices are. That argument is about the frozen semantics and holds with no knowledge
of which branches are red.

**Why the `JUMPDEST` anchor is last, and why there is exactly one.** It must exist, because
`⟨jd⟩` must resolve to something. It must not be at offset 0 or anywhere in the middle,
because a jump backwards re-executes the program and diverges. The final position is the only
one satisfying both. `JUMPDEST` is therefore emitted only there and is not in the PLAIN tier.

### 3.7 The domain `D_program` and its order

```text
index      0      ε                    the empty program
index    1..35    p(j, t)              j slowest, in §3.4 order
                                       t fastest, in Σ order
index     36      p_trunc              PUSH32 with no immediate bytes: the single
                                       byte 0x7f
                                                              |D_program| = 37
```

`ε` first: `SEM-RUN-3` — running past the end of code — has no other witness, and §8.2.1's
`bytes` domain also opens with the empty string.

`t` fastest: by the argument in §3.6. The consequence is that indices 1–5 are `p(0, ·)` — the
whole alphabet at operand value `0`, once per terminal — and they are the five members the
budget of §8.2.2 most reliably reaches.

`p_trunc` last, and it is the one member not generated by the grammar. `SEM-DEC-3` — `PUSHn`
with fewer than `n` bytes remaining is zero-padded — is a postcondition about the *shape of
the code*, not about any operand value, and a grammar that emits complete blocks cannot
express it. It is admitted for that stated structural reason. **If any other frozen case turns
out to be inexpressible in `D_program`, that is a `NO_FROZEN_BRANCH_WITNESS` stop under §8.2.2
and not an occasion to admit a thirty-eighth member.**

### 3.8 The `World` domain, as a consequence

§8.2.1's `World` domain enumerates six shapes, four of which write the literal `code 0x42`.
Under §3.1 that literal is a program-sorted field, so `World` becomes a two-field record:

```text
World  =  shape × code
shape  ∈  W0..W5 exactly as frozen in §8.2.1, with each occurrence of
          `code 0x42` replaced by the record's `code` component
code   ∈  D_program
```

`W0` has no accounts and `W1` is frozen with *empty* code — which is `ε`, a member of
`D_program` — so both ignore the `code` component and their candidates repeat. The redundancy
is stated rather than removed: §8.2.2 asks only whether a candidate covers an arm, so repeated
candidates cost budget and change no outcome, whereas special-casing the shapes would add a
rule with no semantic content.

### 3.9 Termination, by construction

§8.2.2 promises unconditional termination. Byte strings could not diverge; programs can, so
the promise has to be re-established rather than assumed.

**Claim — intra-frame, and only intra-frame.** Every `p(j, t)` dispatches at most `|Σ| + 1`
instructions **in the frame executing it**.

**Proof.** By `SEM-JMP-1` the jumpdest set is every offset holding `0x5B` that is not inside a
`PUSH` immediate. In `p(j, t)` the only `0x5B` outside a `PUSH` immediate is the trailing
anchor: opcode bytes come from Σ and only `JUMPDEST` is `0x5B`, and `JUMPDEST` is emitted
nowhere but the anchor. The jumpdest set is therefore the singleton `{|p| − 1}`, so every jump
that transfers control transfers it *forward*, to the last byte. No backward edge exists, and
`ε` and `p_trunc` contain no jump at all. ∎

**The claim stops at the frame boundary, and deliberately so.** A frame that reaches its
`CALL` block enters a callee, and the callee's dispatch count is not bounded by this proof.
Whether the *whole* evaluation terminates depends on `World[a].code`, which §3.1 has just made
a program — so under A2 a callee can call back, and frozen §3 bounds no call depth
(`SEM-STK-7` bounds the value stack, not the call stack). That divergence is real, it is
reachable, and it is **not** repaired here: it is registered as a foreseeable instance in §3.10 and
recorded as a specimen defect in
[`records/v3-review-findings.md`](../../experiments/e1/records/v3-review-findings.md) §3.2. A
proof that quietly claimed otherwise would be worse than no proof.

What the proof does buy is that no *single frame* spins, so a diverging candidate always
diverges **through the seam**, and reaches the host's call-stack limit rather than running
forever. Under §3.10 that surfaces as a named stop, with the candidate index and the arm
preserved. A hang would have surfaced as nothing at all.

The intra-frame claim is a property of the domain, so it is checkable: the step-6a tool asserts
the sole trailing jumpdest for every member of `D_program` before the search begins, and a
member violating it fails the run.

### 3.10 A candidate that cannot be evaluated is not a candidate outcome

Byte strings could not fail to evaluate. Programs can: a memory offset near `2²⁵⁶` asks the
host for an allocation it cannot make, and a callee that calls back exhausts the host's call
stack. Neither is an `ExceptionalHalt`, and neither is a fact about the specimen — both are the
model's unbounded resources meeting a real machine.

**This section adds no rule. It states what frozen §8.2.2 already implies.** Both of its
outcomes are predicated on a candidate *having* a coverage verdict:

```text
first candidate that COVERS the arm      -> emit LT-BR-<unit>-<nnn>
no candidate COVERS it within B          -> NO_FROZEN_BRANCH_WITNESS, stop
```

A host-level exception yields no such verdict. It is **not** "not covering" — "not covering" is
a determination about the candidate's execution, and here the execution did not complete well
enough to determine anything. Neither branch of §8.2.2 applies, the procedure has no defined
continuation, and a procedure with no defined continuation halts.

```text
If candidate evaluation cannot produce the semantic coverage verdict frozen §8.2.2
requires, the branch-search procedure cannot continue. The run STOPs, preserving the
candidate index, the arm, and the error class as protocol evidence.

NO NEXT CANDIDATE IS TRIED.
```

**Why this is a reading and not the amendment v4 was refused for.** v4's rule chose an outcome
for a case the frozen text does not cover — "not covering" — and thereby let the search run on
and emit a *different* fixture than §8.2.2 selects, since a candidate that covers an arm and
then throws has genuinely covered it. This one declines to choose. It neither completes the
procedure nor extends it; it recognises that the procedure has run out of definition and stops,
which is what §8.2.2 does with every other condition it does not define.

**Two classes are foreseeable from the frozen text alone**, and are named so that a stop
naming one of them is legible rather than surprising:

```text
allocation failure    frozen §3 puts no bound on a memory offset, and §8.2.1's uint256
                      domain contains 2²⁵⁶−1. Nothing in the semantics prevents an
                      operand that no machine can allocate for.

call-stack exhaustion frozen §3 bounds no call depth — SEM-STK-7 bounds the VALUE
                      stack at 1024, and nothing bounds the CALL stack — while A2
                      makes World[a].code a program that can name its own account.
```

Both are read off the frozen documents: the first from §3's silence on addressable bounds
together with §8.2.1's domain, the second from §3's silence on call depth together with §3.1
here. Neither is repaired, and neither may be: a memory bound and a depth limit are semantic
rules that no postcondition licenses, and adding one would be a second amendment (§6.2). They
are specimen defects recorded in
[`records/v3-review-findings.md`](../../experiments/e1/records/v3-review-findings.md) §3.

**A stop under this section is a protocol result, not a failure of the specimen**, and it is
reported as one: it says the frozen procedure met a state it does not define, not that the
MiniEVM is wrong.

### 3.11 What A2 does not change

```text
unchanged   every postcondition of §3, and every case ID of the 213
unchanged   plan_core_digest, c2_control_core_digest
unchanged   the level A/B split, 166 / 47
unchanged   the observation projection, §5.1 and §5.2
unchanged   the primitive domains bool, halt, call kind, address,
            address|ABSENT, uint256, bytes, stack depth
unchanged   the record order of §8.2.1: index sum, ties by §2 field order
unchanged   the budget B = 4096, and every clause of §8.2.2
unchanged   the Step 0 §6 catalog, the thresholds, the decision rule
```

**In particular `B` is not raised and the index-sum order is not touched.** §5.2 predicts what
that costs, before the run rather than after it.

### 3.12 What is already known, and what may be done with it

**This document was written by someone who had already seen `D_program` executed.** Under v4,
before any freeze, the domain was rendered and run against the inherited clean Baseline B. That
run is the reason v4 was refused, and pretending it did not happen is not available.

So it is disclosed rather than repeated:

```text
prior calibration — E1-v4, pre-freeze, NOT a measurement under this or any freeze
    35 generated members rendered; lengths 11 641 – 11 707 bytes
    stack depth at halt 357 of 1024
    <= 3 ms per member
    the trailing anchor was the sole jumpdest of every member
    10 members raised a host allocation error
```

**What that permits.** Being quoted, in those words, as prior calibration — as it is here.
Nothing else.

**What it forbids, and this is the operative half.** No rule in this document may rest on it,
and none does. Each of the three places where v4 leaned on the dry run has been re-derived from
frozen text, and each derivation stands or falls without the numbers above:

```text
§3.10's two foreseeable classes   from §3's silence on addressable bounds and on call
                                  depth, plus §8.2.1's uint256 domain and §3.1's binding
                                  of World[a].code — not from "10 members threw"

§3.9's intra-frame bound          from SEM-JMP-1, by the structure of a generated
                                  program — not from "no member looped"

§3.9's refusal to extend the      from §3 bounding no call depth — not from "a callee
bound across the seam             re-entered"

P3 and P3'                        from the address domain, the World shapes and the
                                  index-sum order, all frozen — not from an observed run
```

**No new dry run was performed for v5, and none may be.** The well-formedness properties are
checked *after* the freeze, by `M0-v5` under binding rule 5 (§4.2) — which is where
verification belongs and where v4 put it wrong by checking first. Any figure this document
would have gained from running the domain again is a figure it is not entitled to.

**A successor quoting the block above must carry this paragraph with it.** Prior calibration
that loses its provenance becomes a measurement, and that is the whole of what went wrong in
v4.

## 4. The freeze event

The construction is E1-v3 §3.1 with new parameters. It is copied rather than re-derived
because it worked: it passed on its first positive evaluation, and it rejected `fbef84cd` on
clauses (b)(d)(e), `e5abd895` on (a)(d)(e), and a forged base on the literal check.

### 4.1 Identity predicate

```text
freeze_base_sha := 8f5aaeda667b2fecd7963f53806811b24cc36607
                   the merge commit that brings the stopped, never-frozen E1-v4
                   history into `main` — PR #5. That merge is NOT a freeze event;
                   it closes v4 and supplies the reviewed base this document is
                   opened from.

FREEZE_PATH     := docs/experiments/E1-v5-preregistration.md

freeze_merge_sha := the unique commit satisfying ALL of:

  (a)  it has exactly two parents
  (b)  freeze_merge_sha^1 == freeze_base_sha
  (c)  FREEZE_PATH is ABSENT at freeze_merge_sha^1
  (d)  FREEZE_PATH is PRESENT at freeze_merge_sha^2
  (e)  blob(freeze_merge_sha:FREEZE_PATH)
         == blob(freeze_merge_sha^2:FREEZE_PATH)
```

**Two merges, and only the second one freezes anything.** The first puts a finished history
into `main` so that (b) has a reviewed base to name and (c) has a commit at which this
document is absent. The second is the freeze event. Doing it in one merge would make the base
and the freeze the same commit, and (c) could not then be stated.

**The v4 preregistration reaches `main` through that first merge, unfrozen.** Its presence
there is not a freeze and confers nothing: it carries a banner saying so, and
[`E1-v4-STOP.md`](./E1-v4-STOP.md) records why. Only `FREEZE_PATH` above is frozen by the
second merge.

**`freeze_base_sha` is a fixed literal.** If `main` moves before this preregistration is
merged, (b) stops holding and the freeze fails rather than re-anchoring itself. That is the
intended behaviour: the reviewed context would have changed, and the right response is to look
at it again — never to repoint the literal at whatever `main` now happens to be.

### 4.2 Binding rules

```text
1.  M0-v5 may exist only on a commit that is a DESCENDANT of freeze_merge_sha.

2.  M0-v5 MUST declare freeze_merge_sha, freeze_base_sha and freeze_path.
    Replay checks the DECLARED base and path against frozen literals held in
    the tool, and evaluates the §4.1 predicate using the LITERALS — never the
    values the manifest supplies.

3.  The measured target is the revision actually checked out. Replay derives
    it as `git rev-parse HEAD`; it is NOT read from M0-v5.

4.  Manifest replay MUST verify the §4.1 predicate (a)-(e) AND the ordering
    `git merge-base --is-ancestor <freeze_merge_sha> <HEAD>`. A replay that
    cannot establish every clause fails, and the run is not admissible.

5.  M0-v5 MUST additionally recompute D_program from §3.2-§3.7 and record its
    member count and digest, and MUST assert the §3.9 sole-trailing-jumpdest
    property for every member.
```

Rule 5 is new. `D_program` is now a decision-rule input exactly as the digests are, so it is
replayed from the specification rather than trusted.

### 4.3 What the freeze fixes, and when

Unchanged from Step 0 §0: nothing in the frozen documents may be revised after the **first
measured run** of the artefact they govern. Under v5 that first measured run is **step 6a**
(§7), because Steps 3–5 are inherited rather than repeated (§5.1). A revision required after
it produces `E1-v6`.

---

## 5. Inheritance of the completed steps, and predictions

### 5.1 Steps 3, 4 and 5 are inherited, not re-run

```text
39b1b4b   M0-v3 protocol manifest
aeac233   Step 3   Baseline A, measured under a freeze that occurred
2964098   Step 4   the 213 frozen core tests, red
20d87be            verify-plan derives the level split
073074b   Step 5   clean Baseline B — 213/213 green, both oracle slices green
```

They are inherited **because A2 cannot affect them.** A2 changes the candidate generator of
§8.2.1, which is read by the branch search of §8.2.2 and by nothing else; the 213 core tests
draw their inputs from §8.1, which is untouched. Re-running them would produce the same
figures under a protocol whose only difference is a document those figures do not depend on —
ceremony, and ceremony that would blur which measurement belongs to which freeze.

`073074b` is the inherited clean baseline. Before step 6a a **non-measurement integrity
replay** is permitted and expected: run the 213 core tests, both oracle slices and
`manifest-replay`, to confirm the working tree still is what `073074b` says it is. It produces
no figure, appends to no manifest, and is recorded as a check rather than as a measurement.

**What is inherited along with them.** External review of the v3 line found that two frozen
postconditions are realised incompletely by their cases, and the finding is carried forward
rather than repaired — editing a frozen test after seeing the implementation converts a
preregistered case into an authored one, which is the move §8.2.2 forbids:

```text
213/213 green          execution / pass count, and nothing more
  3 case IDs           LT-SEM-CALL-5/{CALL,STATICCALL,DELEGATECALL}
                       establish gas extraction, not "consumed"
  1 case ID            LT-SEM-STO-4 — frozen §3.2 assigns SEM-STO-4 to U-RUN,
                       the case exercises U-STO and performs no halt
  => at least 4 case IDs incompletely realise 2 frozen postconditions
```

The second is a **projection / test-realisation mismatch**, and it is a gap in the plan rather
than in one test: §5.1 asserts every §3.2 postcondition survives, a case ID was allocated on
that basis, and `verify-plan.ts` checks IDs, level split, uniqueness and outcomes — but never
that a case realises its postcondition's *unit*. "At least" is literal; the remaining 209 have
not been audited for the same defect.

**A2 does not repair it and may not.** Closing it means either editing frozen tests or adding
a pairing check whose verdicts would land mid-inheritance, and either one is a second
amendment (§6.2). It bears on step 6b, where local-suite strength is what gets measured, and
that is where it must be read — see
[`records/v3-review-findings.md`](../../experiments/e1/records/v3-review-findings.md) §2.

### 5.2 Predictions, registered before the run

These are falsifiable and are written down now so that the step-6a record can be compared
against them rather than narrated after the fact.

**P1 — the 30 dispatch arms get witnesses.** Members 1–5 of `D_program` execute all 89 PLAIN
instructions and one terminal each, so every arm of the `U-RUN` dispatch should be covered by
a candidate at `code` index ≤ 5.

**P2 — the budget reaches only the first handful of `D_program`.** Under the unchanged
index-sum order with `B = 4096`, `code` index 6 first appears at candidate 4018 of the
nine-field `Frame` record and is out of reach entirely for the eleven-field `Frame × World`
record, where index 5 first appears at candidate 3944. So members 6–36 — every operand value
other than `0`, and `p_trunc` — are effectively unreachable for `Frame.code`.

**P3 — arms requiring a callee to execute non-empty code may not get witnesses.** They need
the `address` operand and the `World` shape to name the same account. At operand index `0`
the address is `ZERO`, which no `World` shape carries; the first index that names `0x…0aaa`
is 1, and by P2 that is out of reach. If those arms are among the uncovered, the run stops.

**P3′ — and if the address does match, the candidate may diverge instead.** The coincidence
that lets a callee execute a real program is the same one that lets it call back: the callee's
own `CALL` block carries an address operand from the same domain, so `World[a].code` naming
`a` again recurses without bound (§3.9). Under §3.10 that does **not** cost the arm a witness
and move on — it stops the run, naming the candidate index, the arm and the error class.

P3 and P3′ are opposite failure modes of the same field-agreement condition, and they have
different consequences under this preregistration, which is precisely why they are separated
before the run: **P3 ends in `NO_FROZEN_BRANCH_WITNESS`, P3′ ends in an evaluation stop.** An
account of a stopped run that confused the two would be describing a different defect than the
one that occurred.

**P4 is stated to be refutable:** if step 6a stops again, the cause will be P2 — the
enumeration order and budget starving a field that is first in the record — and not the code
domain. **That would be a defect in §8.2.1's record rule, not in A2**, and it would be an
`E1-v6` matter. It is written here, before the run, precisely so that it cannot be claimed
afterwards as a prediction that was always obvious.

None of P1–P4 licenses a repair mid-run. §8.2.2 governs, and its consequence is a stop.

---

## 6. Prohibitions

### 6.1 `step6a-uncovered-arms.json` is not an input to `D_program`

The v3 discovery record lists 49 uncovered arms. It is the **search's** input — §8.2.2 iterates
over uncovered arms — and it is **not** an input to the construction of `D_program`.

```text
Σ            from Step 0 §1.1 and §1.2
need(ι)      from frozen §3
operands     from frozen §8.2.1 domains, by §2 declared type
grammar      from frozen §3's halt/transfer postconditions
depth        |Σ| blocks — the size of the frozen alphabet
order        stated in §3.7 with its reason
```

Mechanically: the generator module reads no file and imports nothing from `records/`. A
`D_program` that changes when the arms file changes violates this section and invalidates the
run.

### 6.2 One amendment

A2 is the only amendment E1-v5 makes. A second one — raising `B`, reordering the record,
adding a domain member to close a gap the search finds — is an `E1-v6`, by the same rule that
produced v2, v3, v4 and this document.

### 6.3 The stop discipline is unchanged

`NO_FROZEN_BRANCH_WITNESS` still stops the run, still preserves the record, and still
continues only as a new preregistration. A hand-written fixture invented to close a gap is
still prohibited outright. v4 and v5 both exist because that rule was obeyed once already.

**And the same discipline now covers the near side of a freeze.** v4 was refused for writing a
decision rule from observations taken before it was frozen. A preregistration that has seen its
own dry run is not repaired by editing the rule; it is replaced, and the observations are
disclosed as prior calibration (§3.12) rather than laundered.

---

## 7. Sequence

Step 2 §10 governs. Steps 1–2 are discharged by the inherited documents; steps 3–5 are
inherited under §5.1.

```text
0.  freeze          this document reviewed and merged into `main`.
                    That merge commit is freeze_merge_sha.
6a. M0-v5, then domain realisation from scratch under A2:
                    branch search over the 213-core-test uncovered arms,
                    both final domains frozen, the §9.1 set-difference check,
                    and M1 appended if and only if the search succeeds.
                    THIS measurement makes the E1-v5 freeze final.
6b. qualification
7.  proxy
8.  injections
```

**Step 6a starts from scratch.** The v3 discovery run is not reused: its coverage was taken
under the v3 generator, and a domain realisation carrying figures from a superseded generator
would be exactly the kind of quiet inheritance §8.2.2 exists to prevent. The 213-core-only
rule stands unchanged — `oracle-a`, `oracle-b`, the composition witnesses and
`c2_control_suite` are excluded from discovery coverage, as Step 0 §3.2.1 requires.

**No adjudicating figure may be produced before `M1` exists,** and `M1` exists only if the
branch search succeeds. If it does not, the outcome is a v5 stop record and nothing else.

---

## 8. Version chain, for the record

```text
E1-v1   STOP_SPECIFICATION_CONFLICT     Step 0 §1.1 vs Step 2 §3.1 over GAS
E1-v2   STOP_PROTOCOL_FREEZE_ORDER      declared freeze event never occurred
E1-v3   NO_FROZEN_BRANCH_WITNESS        the frozen generator cannot witness the
                                        dispatch arms of the interpreter
E1-v4   STOP_UNFREEZABLE_PREREGISTRATION  a second decision-rule amendment, and rules
                                        written from pre-freeze observations —
                                        stopped BEFORE its freeze, never frozen
E1-v5   this document
```

All four stops are preserved and unmodified — Step 0 §9 and experiments README principle 4.
All four are statements about the specification and its protocol. **None is a result about
boundary blindness**, and none may be cited as one: no specimen has been built, no defect has
been injected, and no calibration figure has been produced. Four stop records are not four
findings, and the fifth version is not four-fifths of an answer.

The fourth is worth distinguishing from the first three all the same. v1, v2 and v3 each froze
a protocol and then discovered it was defective, so each cost a real run. v4 was caught on the
near side of its freeze and cost nothing but the draft — which is the cheap failure, and the
one the review discipline exists to produce.
