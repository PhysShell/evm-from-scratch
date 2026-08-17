# E1 Step 0 — preregistration

**Status:** frozen on merge. Nothing in this document may be revised after the first
measured run of the artefact it governs. Revisions before that point are ordinary
review; revisions after it produce an `E1-v2`, never an edit in place.

**Governs:** [E1 — Boundary blind-spot corpus](./E1-boundary-blind-spots.md).

**Discipline:** [experiments README](./README.md) principle 2 — freeze defect classes,
inclusion criteria, measurements and decision rules before running the experiment they
govern. This document is that freeze. It contains no implementation and authorises none
beyond §9.

---

## 0. What E1 is, and what it is not

E1 is a controlled boundary-defect corpus. It asks the general question stated in the E1
document: can a defect at a semantic boundary survive strong local assurance evidence on
both sides and still fail a composition witness?

**E1 as a whole is not an execution of P-038 §5.1.** P-038's calibration gate carries an
obligation E1's general question does not:

> Build a LeakyOracle-style repository where a boundary-class defect is real, the suite is
> green and mock-heavy, line coverage is high, and mutation score is high. **The static
> detector must identify the constructed case.**

E1 measures whether the phenomenon exists. §5.1 additionally requires that P-038's own
static proxy **fires** on the constructed case. A specimen can satisfy E1 and fail §5.1;
that outcome is informative and is not a failure of E1.

The two are therefore separated structurally:

```text
                 E1 controlled boundary corpus
                      /                \
                     /                  \
                    v                    v
        E1 general study        P-038 §5.1 calibration slice
        (all specimens)         (specimens in §5, and only those)
                                + frozen proxy, exact version
                                + detector must fire
```

§5.1 is reported as satisfied **only** for specimens admitted to the calibration slice
under §5, and only under the proxy version recorded with the result. No general E1 result
may be cited as P-038 §5.1 satisfaction, and no §5.1 slice result may be cited as evidence
of prevalence in production software (P-038 §5.2 owns external validity, and it is blocked
on a producer that does not yet exist).

---

## 1. Frozen semantic subset

The specimen is a MiniEVM over a deliberately small frozen semantics, built in two levels.
Level B is the object of study; level A exists so that a failure at B cannot be confused
with a broken harness.

### 1.1 Baseline A — correctness foundation (no boundary)

Opcodes:

```text
STOP
PUSH0, PUSH1..PUSH32
POP
ADD, SUB, MUL, DIV, MOD
LT, GT, EQ, ISZERO
DUP1..DUP16, SWAP1..SWAP16
JUMP, JUMPI, JUMPDEST, PC
```

Level A carries **no cross-component seam**. Its only purpose is to establish that the
interpreter is correct against the frozen semantics, and that the harness, coverage
instrumentation, mutation engine and manifest replay all function. **No calibration
specimen may be drawn from level A.**

### 1.2 Baseline B — exactly one composition boundary

Level B adds the minimum required for a single real seam, and nothing else:

```text
MSTORE, MLOAD, MSIZE          (memory, needed to observe returndata)
SLOAD, SSTORE                 (storage, needed to observe the static-write guard)
RETURN, REVERT                (callee termination)
RETURNDATASIZE, RETURNDATACOPY
CALL, STATICCALL, DELEGATECALL
ADDRESS, CALLER
GAS                           (placeholder only — see below)
```

`GAS` is included **as a stack producer with no accounting behind it**:

```text
GAS := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff   (MAX_UINT256)
```

The value is not our choice. Upstream case **#84 `GAS`** asserts exactly this and states its
reason — *"in this version of the tests, GAS is not supported yet and is always expected to
return MAX_UINT256"* — so the constant is dictated by the oracle we are already bound to, and
#84 pins it as a regression. Recording it here rather than "a frozen constant, chosen at
implementation" removes the opportunity to tune the number after a first attempt at #146.

`GAS` is here only because the upstream `DELEGATECALL` fixture passes a gas argument, and
dropping that fixture would cost the `address` / `storage_owner` seam its witness. Gas
*semantics* remain excluded (§1.3); a defect involving gas is out of scope.

**The seam** is the caller frame → callee frame transition, modelled as an explicit frame
construction with a frozen set of boundary-carried fields:

| Field | Meaning at the seam |
|---|---|
| `address` | the address the callee executes *as* |
| `caller` | the address the callee sees as its immediate caller |
| `static` | whether state writes are prohibited inside the callee |
| `storage_owner` | the account whose storage the callee reads and writes |
| `returndata` | bytes the callee publishes back to the caller |
| `success` | whether the callee halted normally or exceptionally |

This field set is frozen. A defect is a *boundary* defect for E1 purposes only if its
causal region is the production of, propagation of, or guarding on one of these six fields.

### 1.3 Explicitly excluded from the frozen subset

Gas accounting of any kind (see the `GAS` placeholder above), `CREATE`/`CREATE2`, `SELFDESTRUCT`, logs,
`SHA3`, precompiles, the account/balance model beyond `storage_owner`, `EXTCODE*`, block
and tx context opcodes beyond `ADDRESS`/`CALLER`, call depth limits, and value transfer.

`CALL` is modelled **without value transfer and without gas**. This is a deliberate
amputation: the seam under study is field propagation, and the rest of the call machinery
would turn a controlled specimen into an EVM project. A defect requiring any excluded
feature is out of scope for E1 rather than a reason to widen the subset.

### 1.4 Baseline correctness oracle

The oracle is the repository's pre-existing `evm.json` — **152 cases authored upstream,
before this experiment existed and without knowledge of it.** This independence is the
reason it is the oracle rather than a suite we write.

- **Oracle set** = every `evm.json` case that is in-subset, where in-subset means **both**
  the case's own `asm` **and** the `code.asm` of every account in its `state` use only
  opcodes from the level in question. The nested-code check is load-bearing, not pedantry:
  the seam fixtures carry callee bytecode in `state`, and a case whose callee leaves the
  subset is not runnable however small its outer code looks.
- Resolved against the corpus at the baseline revision, this yields **49** cases for level A
  and **71** for level B, of which 6 are composition witnesses (§4), leaving **65** oracle
  cases at level B. These counts are recorded here as the value at freeze time; the
  authoritative case-index list goes in the freeze manifest (§8).
- The clean baseline is **correct** iff it passes 100% of the oracle set.
- Any oracle case the baseline cannot pass must be removed from the oracle set **before**
  any defect is injected, with a recorded reason. Removing an oracle case after seeing an
  injection result is prohibited.
- The oracle set is **not** the local test suite (§3) and **not** the composition witness
  (§4). All three are disjoint in role; the oracle may overlap the witness in cases, and
  where it does, the witness case is excluded from the oracle's green-suite requirement so
  that "baseline correct" and "defect detected" are never the same measurement.

---

## 2. Toolchain

Frozen choices. Exact version strings are pinned at implementation start and recorded in
the freeze manifest; a version change after the first measured run invalidates the run.

| Role | Choice |
|---|---|
| Language | TypeScript |
| Test runner | Jest |
| Coverage | Istanbul (via Jest), line + branch |
| Mutation engine | StrykerJS |
| Proxy implementation | TypeScript Compiler API |

**Why TypeScript.** Hypothesis H2 is about *mutation representability* — whether an
ordinary operator can express the defect at all. Answering that requires an **enumerable,
documented operator catalog**, which is a property of the engine, not of the language.
StrykerJS publishes exactly such a catalog; `cargo-mutants` works at whole-function-return
granularity, too coarse for a causal-region claim; Python engines have a weaker or less
explicitly documented operator set. Secondary: the repository's TypeScript template already
ships Jest and a fail-fast environment, so the harness is not built from nothing.

**Caveat carried from P-038 §3.3.** P-038 warns that Stryker's per-test semantics must be
re-verified against the version used. That warning names **Stryker.NET**; StrykerJS is a
different implementation. The warning is inherited rather than discharged: before the first
measured run, StrykerJS's per-test coverage-analysis semantics must be verified on level A
and the finding recorded. `coverageAnalysis` must be set explicitly, never left implicit.

**Open to veto.** Of everything frozen here this is the choice most worth overturning
before implementation begins, and the cheapest to overturn — it costs a re-pin of §2 and
nothing else, provided no measured run has occurred.

---

## 3. Local assurance evidence

"Local" means: evidence obtained about one side of the seam while the other side is
substituted. This is the analogue of §5.1's *mock-heavy* requirement, and it is mandatory,
not incidental — a specimen whose local tests exercise the real far side is not a §5.1
specimen at all.

### 3.1 Local test construction (mechanical independence)

An instruction not to read §6 would be worthless. The catalog is frozen in this same
document, it names the four corrupted fields in plain text, and no procedure can verify that
a person has forgotten something. Git history proves the order in which files were written;
it proves nothing about what their author knew. So the independence here is **structural**:
the local test set is a *function of the frozen semantics*, leaving the author no free
choice that the catalog could bias.

An earlier draft of this section went straight from "complete normative semantics" to "one
local test per postcondition". That was self-defeating, and the review that caught it was
right: if the semantics must document a postcondition for `static` on the consuming side,
and every postcondition must have a local test asserting it, then a specimen whose `static`
guard is broken **must** fail locally. The same argument disposes of `address` and `caller`.
The anti-tuning device was strong enough to abolish the phenomenon it was built to protect —
the local suite would have been a complete end-to-end oracle wearing a mock's clothing, and
`local suite green` would have been unreachable for every boundary defect in §6.

The repair is not a weaker semantics. It is a **projection** between two things the earlier
draft conflated:

```text
full normative semantics            complete — all six boundary fields,
        |                           both sides, including the relational
        |                           postconditions that tie them together
        |
        |  local_observation_projection   (mechanical, frozen, §3.1.2)
        v
local observable contract           only what a component can be held to
        |                           through its own interface with the far
        |                           side substituted
        v
frozen local test plan              one test per projected postcondition
```

#### 3.1.1 Full normative semantics

Complete, and frozen before any code. It enumerates for every production function its
postconditions, **including a postcondition for each of the six boundary-carried fields
(§1.2) on both the producing and the consuming side, and the relational postconditions that
bind the two sides together** ("the `caller` the callee observes is the address of the frame
that initiated the call").

The completeness requirement survives intact. It is what stops blindness from being authored
by omission: a semantics that quietly said nothing about `static` would make the projection
below vacuous, and the resulting gap would be ours rather than the seam's.

#### 3.1.2 The local observation projection

Frozen before implementation and **defined without reference to §6**. Two inputs:

**(a) The declared local test boundary.** For each production function, the interface through
which it is exercised in isolation: its inputs, the substituted far side, and its *own*
observable outputs — returned values, and effects on the stack, memory and storage it owns.
The declared boundary states, as its load-bearing clause:

> A local test asserts through the unit's own observable interface. It does not assert on
> the internal fields of a value handed to a substituted collaborator.

**(b) The survival rule.** Stated positively, over the observation set:

```text
P survives local_observation_projection
  iff every value needed to decide P is observable through the declared
      local interface of that unit, with the far side substituted.

Explicitly NOT locally observable:
  - internal fields of a value handed to a substituted collaborator;
  - the actual state or behaviour of the substituted collaborator;
  - relations requiring observations from both real sides at once.

Every producer<->consumer relational postcondition is therefore excluded,
but relationality is SUFFICIENT for exclusion, never NECESSARY.
```

An earlier draft made relationality the *iff*, and that did not license the paper check it
was written to support. Take D1's producing-side postcondition, "`STATICCALL` constructs a
callee frame with `static = true`". It quantifies over the producer alone — no real consumer
appears in it — so under an `iff`-relational rule it would **survive** the projection, get a
local test, and be caught locally. §6.1 nonetheless declared it unobservable, correctly, but
by appeal to clause (a) rather than to the stated rule. The normative rule and the paper
check were using different criteria, and only the observation-set form covers both.

Under the rule as now stated the two agree:

| Postcondition | Decidable from the unit's own interface? | Survives |
|---|---|---|
| `STATICCALL` ⇒ constructed frame has `static = true` | no — the frame's only outward manifestation is an argument to the substituted callee | **no** |
| `frame.static` ⇒ `SSTORE` refused | yes — asserted against a correct stub frame, through the callee's own storage effects | **yes** |

So the callee-side guard keeps its local test and stays honestly verified, while the
producer-side construction has no local assertion available to it. D1 breaks only the
producer, and the local suite is green — not by omission, but because the declared boundary
affords no observation of that value.

The rule is a property of the postcondition's *form* and the boundary's *topology*,
decidable from §3.1.1 plus the frozen boundary of §3.1.2(a) — its two inputs, and only
those. It does not consult the defect catalog. An assertion is
therefore absent from the local suite because the boundary hides it, never because an author
declined to write it.

#### 3.1.3 The frozen local test plan

Enumerated exhaustively from the projection before any test is written:

1. **postcondition tests** — for each function `F` and each postcondition `P` of `F` **that
   survives the projection**, exactly one test asserting `P`. Inputs come from the frozen
   deterministic input-selection rule recorded in the plan, never from author preference.
2. **branch completion** — for each branch in `F` left uncovered by step 1, exactly one test,
   its input obtained by the frozen search order over the input enumeration. Not "whatever
   the author found convenient".
3. **seam doubles** — at the seam the far side is always a test double, built by the frozen
   rule: a caller-side test's callee is a stub, a callee-side test receives a stub frame it
   did not build.

The assertion set is thus determined by the semantics, the projection and the plan — all
frozen before implementation. Knowledge of §6 buys nothing: the author may have D1–D4
printed on a t-shirt and still have no room to shape which assertions exist.

Git ordering — local-suite commits preceding the first injection commit — is retained as a
**secondary audit** that the plan was followed in sequence. It is corroboration, not the
guarantee.

#### 3.1.4 This projection is the experiment's scope condition

The declared boundary of §3.1.2(a) is a real choice with real consequences, and it is the
single assumption on which every §5.1 result rests. A project whose local tests *do* assert
on the arguments handed to their mocks has a different local contract, and boundary defects
would be far more visible to it.

That is not a flaw to be hidden; it is the condition under which the finding holds, and it
**must be stated whenever a result is reported**: *under a local-testing discipline that
asserts through a unit's own interface rather than on collaborator arguments.* A result
quoted without that clause overclaims.

It also sharpens the open question of §5.1.1. With the projection frozen and mechanical,
"the author forgot to write the assertion" is impossible by construction — so if the proxy's
`likely_unwitnessed` corresponds to anything, it corresponds to the topology case, which is
the one P-038 is interested in.

If the frozen plan turns out to be unimplementable as specified, that is a Step 0 defect: it
is fixed by a new preregistration before measurement, never by an author decision at the
keyboard.

### 3.2 Seam-adjacent region

Every measurement below is **local to the seam**, never repository-wide. For each seam the
freeze manifest names an explicit `seam_adjacent_region`: the production functions
containing (a) caller-side construction of the boundary-carried fields and (b) callee-side
consumption of and guarding on them. Repository-wide coverage and repository-wide mutation
score are recorded for context and are **not** admissible as the §3.3 thresholds.

#### 3.2.1 Test domain — which tests may produce the evidence

`seam_adjacent_region` says which *production code* is measured. It says nothing about
which *tests* do the measuring, and that second question decides whether the whole
experiment means anything.

**Every §3.3 coverage and mutation measurement, on both revisions, runs against the frozen
local suite alone.** The oracle set (§1.4) and the composition witnesses W1–W6 (§4) are
**excluded from the test domain of these measurements.**

Without that exclusion the default is fatal: a Jest run over everything would let W1–W6
cover the seam and kill the seam mutants, and the resulting figure would be reported as
strong *local* adequacy. It would be nothing of the kind — the composition witness would
have manufactured the very evidence the experiment holds constant, and P-038's entire
distinction between local point evidence and a composition witness would collapse inside
our own measurement.

Each suite has exactly one job, and no second one:

| Suite | Answers | Never used for |
|---|---|---|
| oracle set (§1.4) | is the baseline correct? | coverage, mutation, local detection |
| **calibration local suite** (§3.1.3) | local coverage, mutation, local detection for D1–D4, C1a, C1b | correctness, composition, anything C2 |
| **`c2_control_suite`** (§3.2.2) | C2 only | every D-specimen measurement, and §5.1 |
| witnesses W1–W6 (§4) | the composition counterfactual | coverage, mutation, local detection |

#### 3.2.2 `c2_control_suite` — why C2 needs a domain of its own

C2 is D1 plus exactly one assertion that the §3.1.2 projection withholds. If that assertion
were added to *the* frozen local suite, the suite would carry it for every specimen — and D1,
whose whole construction is that no local assertion reaches the corrupted value, would go red
under its own control. The control would destroy the specimen it exists to contrast with.

There are therefore two frozen domains, both fixed before implementation:

```text
calibration local suite    the projected plan of §3.1.3, unmodified
                           digest: calibration_local_test_set_digest
                           used by: D1, D2, D3, D4, C1a, C1b

c2_control_suite           the same projected plan
                           + exactly one preregistered assertion that the
                             projection excluded — a COLLABORATOR-ARGUMENT
                             assertion, not a relational one
                           digest: c2_control_test_set_digest
                           used by: C2, and nothing else
```

The distinction is load-bearing and an earlier draft of this section got it wrong. C2 is the
positive control with a **local** oracle: it must break the §3.1.2(a) clause in exactly one
named place while remaining a local test. Restoring a *relational* invariant instead would
require a real producer and a real consumer, making C2 a composition test — a small duplicate
of its own witness — and it would no longer demonstrate that the seam is visible locally when
the oracle is present. The concrete instantiation is
[Step 2 §9](./E1-step2-semantics-and-plan.md#9-c2_control_suite): a spy on the substituted
collaborator, asserting the captured frame's field.

What is frozen is the **relation between the domains**, not merely the two initial lists —
the calibration domain grows by branch-completion tests, and C2's must grow with it or the
contrast decays. See Step 2 §9.1 for the set-difference check that enforces it.

`c2_control_suite` **never** contributes to any D-specimen's coverage, mutation score, or
local-detection verdict, and never to a §5.1 calibration result. The separation is by
distinct digest rather than by convention, so a later run cannot quietly hand the extended
suite to the mutation engine alongside D1.

C1a and C1b need no extension: they are ordinary local faults that the projected plan already
observes, and they run on the calibration suite unchanged.

The freeze manifest records both suites' exact test-ID lists and both digests, so the domain
of any recorded measurement can be verified after the fact rather than trusted.

### 3.3 Thresholds, and the revision they are measured on

| Measurement | Threshold over `seam_adjacent_region`, specimen's own test domain only (§3.2.1) |
|---|---|
| Line coverage | ≥ 95% |
| Branch coverage | ≥ 90% |
| Mutation score | ≥ 90%, computed as killed / (killed + survived) |

These thresholds are evaluated **twice, on two different revisions, for two different
purposes**:

- **on the clean baseline — harness qualification.** Establishes that the stand is capable
  of strong local evidence at all. Necessary, and not by itself the §5.1 evidence.
- **on the injected specimen — the §5.1 evidence.** P-038 §5.1 asks for a specimen in which
  *the bug exists* while the suite is green, coverage is high and mutation adequacy is high.
  That is a property of the defective program, so it must be measured there.

A clean revision that was mutation-adequate says nothing about a defective one. Injection
can add a line, add a branch, or introduce an unkillable mutant, and once it has, "this
specimen is mutation-adequate" is no longer supported by the baseline number. The distinction
matters most for **D1**: the entire interest of an absence defect is that the *defective*
program still carries strong mutation evidence despite having no causal construct present.
Quoting the baseline figure there would assert precisely the thing worth measuring.

Both sets of figures are recorded (§7). Only the injected-specimen figures may be cited as
P-038 §5.1 evidence.

#### 3.3.1 Unassessed mutants

A mutation score is only as honest as its denominator. With `killed 9 / survived 1 /
NoCoverage 100`, the ratio reads 90% while a hundred mutants sit unexamined.

Within `seam_adjacent_region`, mutants produced by the specimen's own test domain alone
(§3.2.1 — the calibration local suite for every D-specimen and C1a/C1b, `c2_control_suite`
for C2 and nothing else),
on whichever revision is being qualified — baseline or injected, symmetrically:

```text
NoCoverage           must be 0
                     otherwise the specimen may not claim local mutation
                     adequacy — §5.3 condition 3 on the baseline, or
                     condition 6 on the injected revision, fails

Timeout | Ignored | CompileError
                     unassessed — the operator's fate is unknown

  inside the causal region     -> the condition fails as "unassessed"
  elsewhere in seam_adjacent   -> the condition fails as "inadequate"
  outside seam_adjacent        -> recorded as context, no effect on the verdict
```

This section **classifies**; it does not adjudicate. The verdict that follows from a
classification is decided solely by the ordered algorithm in §5.3.1 — where an unassessed
causal region yields `INCONCLUSIVE_UNASSESSED` on either revision, and any other
inadequacy yields `INVALID`. Keeping classification and adjudication apart is what
stops a single specimen from matching two outcome clauses at once.

Requiring `NoCoverage == 0` over the seam-adjacent region rather than merely reporting it
is the deliberate strengthening: a region with uncovered mutants has not demonstrated the
local adequacy this experiment exists to hold constant.

---

## 4. Composition witness

The composition witness for a seam is a fixture that executes **both sides for real** — no
doubles — and asserts on an outcome observable only after composition.

The witnesses are drawn from the upstream corpus, which already contains them:

| Witness | `evm.json` case | Boundary field | Observes |
|---|---|---|---|
| W1 | #140 `CALL` | `returndata`, `success` | callee `RETURN` reaches caller memory |
| W2 | #142 `CALL (reverts)` | `success` | callee `REVERT` is caller-visible as failure, outer run still succeeds |
| W3 | #141 `CALL (returns address)` | `caller` | callee's `CALLER` is the **immediate** caller, returned to and read by the caller |
| W4 | #146 `DELEGATECALL` | `address`, `storage_owner` | callee's `ADDRESS` is the **caller's** address, and `SSTORE` lands in the caller's storage |
| W5 | #147 `STATICCALL` | `returndata`, `success` | a static call that writes nothing still returns data |
| W6 | #148 `STATICCALL (reverts on write)` | `static` | `SSTORE` inside a static callee fails |

Using upstream fixtures is deliberate, and the claim it supports should be stated at its
real strength and no higher: **the fixtures** were authored upstream to teach EVM semantics,
with no knowledge of this experiment, so their content cannot have been shaped around the
mechanism we hope to demonstrate. **The selection** of these particular six was made by us,
knowing the intended seam. That selection is legitimate because it is frozen here, before
any injection exists — but it is frozen choice, not independence, and must not be described
as the latter.

A witness "fails" for a specimen iff its asserted stack/success outcome differs from the
upstream expectation. Witness cases are excluded from the §1.4 oracle green-suite
requirement (see §1.4) and from the §3 local suite.

### 4.1 The counterfactual: a witness must pass before it may fail

Each defect in §6 has an **assigned witness**. For a specimen's witness failure to mean
anything, that same witness must be **green on the exact clean baseline revision** the
specimen was injected into.

Without it the design admits a specimen whose assigned witness was already broken —
unimplemented, or failing for an unrelated reason — so that:

```text
clean baseline:   oracle 65/65 green,  W6 already failing
inject D1:                             W6 fails
=>  "defect detected"                  though injection may have changed nothing
```

The witness would be reporting the state of the baseline, not the effect of the injection.
Both arms of the counterfactual are therefore required, on the same revision pair:

```text
assigned witness PASSES on the clean baseline revision
assigned witness FAILS  on the injected revision
```

This is why the witnesses are excluded from the §1.4 oracle set but not from testing: they
are not part of the "baseline is correct" measurement, and they must still be green before
any injection is attributed to them.

---

## 5. P-038 §5.1 calibration slice

### 5.1 The proxy — `e1-static-test-proxy/v0`

P-038 §3.1 requires an operational predicate, frozen before use, implemented exactly as
frozen, and **able to abstain**. `indeterminate` is first-class and must never be folded
into either side.

The proxy is **static**: it reads production and test sources. It executes nothing, and it
makes no runtime claim. It is evaluated per (seam site `s`, boundary-carried field `f`):

```text
likely_witnessed
    some test in the local suite contains an assertion whose asserted
    expression is derived, by intraprocedural def-use within that test body,
    from a value that carries f across s

likely_unwitnessed
    no such assertion exists in any local test,
    AND f is statically reachable at s in production code

indeterminate
    f is not statically resolvable at s;
    or the asserted expression flows through a construct the scanner does
    not model — helper indirection beyond depth 1, dynamic property access,
    iteration over a dynamically built collection;
    or f is not statically reachable at s
```

The scanner's modelled-construct set is frozen with this version id. **Any change to the
predicate, the modelled-construct set, or the depth bound produces `v1` and does not edit
`v0`.** Results already recorded under `v0` remain in the record under `v0`.

#### 5.1.1 Open question — is the proxy circular? (gate before step 5)

The proxy asks whether an assertion exists that is derived from a carried field. The §3.1
plan determines which assertions exist. Those two facts sit uncomfortably close together,
and the risk is a proxy that does no work:

```text
frozen local-test plan   ->   which assertions exist
                                      |
                          proxy  ->   "does an assertion derived
                                       from field f exist?"
```

If `likely_unwitnessed` turns out to mean nothing more than *"the plan did not require an
assertion here"*, then §5.1 is circular: the detector would be rediscovering our own
authoring rule and calling it a structural property of the seam.

This is not yet known to be a defect, and it does not block the freeze — no measured run
depends on it. **It does block step 5.** Before the proxy is implemented, it must be shown
that `likely_unwitnessed` can arise from *real structural separation* between the local
tests and the production transition — that a seam field can go unasserted because the local
tests genuinely cannot observe it through the doubles, not merely because the plan did not
enumerate an assertion for it. The finding is recorded either way, and if the answer is that
the proxy only re-reads the plan, `v0` is replaced before any calibration result is claimed
under it.

### 5.2 Admission to the slice

A specimen enters the calibration slice iff, in this order:

1. it is a **D-specimen**, not a control — C1a, C1b and C2 are excluded by construction
   (§6), including C2, whose causal region *is* a boundary field and which would otherwise
   qualify under condition 3 below;
2. it is drawn from Baseline B (§1.2) — level A specimens are ineligible by construction;
3. its defect's causal region is the production, propagation, or guarding of a
   boundary-carried field (§1.2);
4. its local suite was produced by the frozen local-test plan of §3.1, with the git-ordering
   audit as corroboration;
5. its local tests substitute the far side at the seam (§3.1.3 rule 3).

### 5.3 Calibration decision rule

For an admitted specimen, the verdict is `PASS` iff all seven conditions hold; §5.3.1 fixes
the order in which they are adjudicated, and every other outcome falls out of that order.

```text
harness qualification, on the clean baseline revision
  1. baseline green on the oracle set                           (§1.4)
  2. assigned witness PASSES on the baseline                    (§4.1)
  3. seam-adjacent line ≥95%, branch ≥90%, mutation ≥90%,
     NoCoverage == 0                                            (§3.3, §3.3.1)

the specimen itself, on the injected revision
  4. assigned witness FAILS                                     (§4.1)
  5. full local suite green                                     (§3)
  6. seam-adjacent line ≥95%, branch ≥90%, mutation ≥90%,
     NoCoverage == 0                                            (§3.3, §3.3.1)

the detector obligation
  7. proxy returns likely_unwitnessed for the corrupted field   (§5.1)
```

Conditions 1–3 qualify the stand. Conditions 4–6 are the §5.1 specimen proper — a program
in which *the bug exists* while the suite is green and local adequacy is high — and only
these figures may be cited as §5.1 evidence. Conditions 2 and 4 together are the
counterfactual that makes the witness failure attributable to the injection. Condition 7 is
the detector obligation E1's general question does not carry.

#### 5.3.1 Adjudication order (one input, one verdict)

Stated as prose, the outcomes overlapped: a specimen with a red baseline witness *and* an
abstaining proxy satisfied both the "any of 1–6 fails" clause and the "7 is indeterminate"
clause, and §3.3.1's causal-region rule spoke of "the revision being qualified" while the
prose carved out condition 6 only. A decision rule that admits two answers for one input is
not a decision rule.

A first-match rule keyed on *kinds* of failure did not fix it either: with condition 1 red
(baseline incorrect) **and** an unassessed mutant at condition 3, a kind-first order returned
`INCONCLUSIVE_UNASSESSED` for a specimen already proven invalid at condition 1 — contradicting
this document's own rule that `INVALID` names the *lowest-numbered* failing condition. The
prerequisite order has to be genuinely sequential, not merely declared.

Adjudication is therefore a **sequential automaton over the conditions in order**. Each
condition is evaluated only if every earlier one held; the first that does not hold decides
the verdict and evaluation stops:

```text
condition 1  fail                        -> INVALID(1)
condition 2  fail                        -> INVALID(2)
condition 3  fail, unassessed in causal  -> INCONCLUSIVE_UNASSESSED (baseline)
             fail, otherwise             -> INVALID(3)
condition 4  fail                        -> INVALID(4)
condition 5  fail                        -> INVALID(5)
condition 6  fail, unassessed in causal  -> INCONCLUSIVE_UNASSESSED (injected)
             fail, otherwise             -> INVALID(6)
condition 7  indeterminate               -> INCONCLUSIVE_PROXY
             likely_witnessed            -> FAIL_PROXY
             likely_unwitnessed          -> PASS
```

The causal-region carve-out now lives *inside* conditions 3 and 6 rather than above the whole
ladder, so it applies symmetrically to both revisions while never pre-empting an earlier
failure. "We could not measure it" and "we measured it and it was inadequate" stay distinct,
without letting the former mask a specimen that was already invalid upstream.

Condition 7 is **never** reached unless 1–6 all hold: a proxy verdict about a specimen that
was never validly constructed carries no information, in either direction.

One sub-case worth naming, now falling out of the order rather than needing an exception:

- **condition 2 fails** (assigned witness already red on the baseline) — the stand is broken
  for that seam. The automaton returns `INVALID(2)` and never evaluates condition 4, so a
  co-occurring "witness did not fail" can never be reported as the cause. Nothing about the
  injection may be concluded.
- **`FAIL_PROXY`** (rule 4) — per P-038 §5.1 this kills the implementation or
  the proxy definition, **not the research hypothesis**: it is recorded, the proxy may be
  revised under a new version id, and the specimen stays in the record. It is not evidence
  against boundary blindness.

Neither inconclusive kind is ever silently read as pass or fail, and the rates of both —
`INCONCLUSIVE_PROXY` and `INCONCLUSIVE_UNASSESSED` — are reported alongside every
calibration result. The five verdict names here are exactly the `calibration_outcome`
values of §7; no other outcome vocabulary exists.

---

## 6. Defect and control catalog

Frozen. All of **D1, D2, D3, D4, C1a, C1b and C2** must be built and measured before any E1
result is written up. The catalog deliberately does not consist only of absence defects.

| ID | Class | Seam field | Injection | Expected local | Expected witness |
|---|---|---|---|---|---|
| **D1** | boundary **absence** | `static` | `STATICCALL` never writes `static` onto the constructed callee frame; the field defaults to false. The callee-side guard is present and correct. | passes | W6 fails |
| **D2** | boundary **misbinding** | `address` | `DELEGATECALL` sets the callee's `address` to the callee instead of the caller | passes | W4 fails |
| **D3** | boundary **misbinding** | `caller` | `CALL` sets the callee's `caller` to the **callee's own address** instead of the immediate caller's | passes | W3 fails |
| **D4** | exceptional **propagation** | `success` | callee `REVERT` is flattened into a normal return | **fails** — see §6.1 | W2 fails |
| **C1a** | **negative control** — ordinary local fault | none | `SUB` computes `a - b - 1` | **fails** | n/a — passes |
| **C1b** | **negative control** — ordinary local fault | none | `LT` implemented as `≤` | **fails** | n/a — passes |
| **C2** | **positive control** — boundary fault with a local oracle | `static` | as D1, but the plan adds one collaborator-argument assertion the projection excludes; stays a local test | **fails** | W6 fails |

The D-rows each name an **assigned witness**, and §4.1's two-armed counterfactual applies to
them. The C-rows do not, and this is not an oversight:

**C1a/C1b have no assigned witness and their composition witnesses pass.** None of W1–W6
executes `SUB` or `LT` — the seam fixtures are `PUSH`/`CALL`/`MLOAD`/`SSTORE` shaped — so an
arithmetic fault is invisible to every one of them. What it *does* break is the §1.4 oracle
set, which is full of arithmetic cases, and the local suite, which is the point: C1 shows the
local apparatus catches an ordinary fault that never reaches the seam. Its expected signature
is the exact mirror of a boundary defect — **oracle red, local red, witnesses green** — and
recording it as "witness fails" would have been simply false.

**D3 introduces no new semantic dimension.** An earlier draft had it propagate the
transaction origin, but `origin` is neither in the frozen opcode subset (§1.2) nor among the
boundary-carried fields (§1.3 excludes tx-context opcodes beyond `ADDRESS`/`CALLER`), so
that injection would have required widening the model to host its own defect. Misbinding
`caller` to the callee's own address stays entirely inside the frozen field set, and W3
(#141) discriminates it exactly: the fixture expects the caller's `0x…aaa` and would observe
the callee's `0x…c42`.

**C1a and C1b are both mandatory**, and both are named concretely. An `or` in a
preregistration is a deferred choice wearing a commitment's clothes — it lets whichever
control behaves more agreeably be selected after the fact.

**C1a/C1b** exist to show the local apparatus catches what it should — an experiment in
which local evidence never catches anything is measuring a broken harness. **C2** exists to
show the seam is not intrinsically invisible: when the local oracle is present, the boundary
defect is caught locally. C2's assertion is one the §3.1.2 projection withholds — a
collaborator-argument assertion, not a relational one, so that C2 stays a *local* test —
added to the frozen plan as a declared exception and recorded both in the plan and in its
manifest, never improvised at the keyboard.

**The §5.3 decision rule governs D-specimens only.** All three controls would trip it —
C1a/C1b on condition 4 (no witness failure), C2 on condition 5 (local suite red) — and would
be recorded as `INVALID`, which would be a true statement about the wrong question.
The controls are not candidate §5.1 specimens; they are checks on the apparatus. Each is
scored against its own expected signature above, and `calibration_outcome` is `n/a` for all
three.

**D4 stays a D-specimen and is expected to be scored `INVALID(5)`.** It is not reclassified
as a control, because its role is different from C1 and C2: it is a genuine boundary defect
that the §3.1.2 projection predicts will be caught locally anyway (§6.1). Letting it run the
full ladder and land on `INVALID` is the honest outcome, and one the preregistration commits
to in advance rather than discovering afterwards.

A corpus of hand-picked blind spots would be, in the E1 document's own words, uselessly
self-congratulatory. D1 in particular must not be treated as the canonical or first
calibration witness merely because it matches an absence mechanism already observed in
Own.NET. We already know absence defects are interesting; building a stand around the
mechanism we intend to demonstrate and then demonstrating it is not evidence.

### 6.1 Paper check — can these defects logically pass locally?

The §3.1.2 projection is only a repair if the catalog can actually clear it. Worked through
before any code, applying the §3.1.2(b) survival rule verbatim: **is every value needed to
decide the corrupted postcondition observable through that unit's own interface, with the far
side substituted?**

| | Corrupted postcondition | Values needed to decide it | Survives projection | Predicted local |
|---|---|---|---|---|
| **D1** | `STATICCALL` ⇒ constructed callee frame carries `static = true` | the frame's internals — manifested only as an argument to the substituted callee | **no** (clause a) | **passes** |
| **D2** | `DELEGATECALL` ⇒ constructed frame carries the *caller's* `address` | same — argument to the double | **no** (clause a) | **passes** |
| **D3** | `CALL` ⇒ constructed frame carries the immediate caller's address as `caller` | same — argument to the double | **no** (clause a) | **passes** |
| **D4** | callee `REVERT` ⇒ caller-visible failure | the unit's own output: the callee's returned frame result, or the caller's own stack given a stub that reports failure | **yes** | **fails** |

Note that D1–D3 are excluded by clause (a) — the collaborator-argument clause — and not by
relationality. Their producing-side postconditions mention no real consumer at all. This is
exactly the case the earlier `iff`-relational wording got wrong, and the reason the rule is
now stated over the observation set.

**D1 was re-specified to survive this check.** It previously read "the callee-side write
guard is not implemented at all" — a *single-sided* consuming postcondition, fully observable
by a callee-side test handed a stub frame with `static = true`. It would have been caught
locally and could never have been a §5.1 specimen. Moving the absence to the producing side —
the flag is never written — keeps it an absence defect (there is still no construct at the
causal point for a mutation operator to reach, §6.2) while placing it where the boundary
hides it.

**D4 does not survive, and is kept anyway.** "Callee `REVERT` becomes caller-visible failure"
is single-sided wherever it is sited: as callee-side halt handling it is observable in the
frame result the callee unit itself returns; as caller-side interpretation it is observable
on the caller's own stack with a stub that reports failure. Either way a projected
postcondition covers it and the local suite goes red. The genuinely relational version needs
a failure crossing **two** seams, which the frozen depth-1 subset (§1.3) does not model.

Re-siting D4 until it passed would have been the same rigging in a new coat. It is instead
**preregistered as a locally-caught boundary defect** — a second positive control, distinct
in kind from C2: C2 is caught because an assertion was deliberately added outside the
projection, D4 because its postcondition never left the projection. Its value is that it
keeps the catalog from asserting what E1 is supposed to test, namely that boundary defects
are *generally* invisible. They are not — only those whose deciding values the declared
boundary hides, which is a broader class than the relational one (see Step 2 §5.2, where all
fifteen producing-side postconditions fall to the collaborator-argument clause rather than to
relationality). D4 is the preregistered counter-example.

**Consequences for the calibration slice.** D1, D2 and D3 are the candidate §5.1 specimens.
D4 will trip condition 5 and be recorded `INVALID(5)`, which for D4 is the predicted and
correct result rather than a defect in the stand.

Every entry above is a **falsifiable prediction**, not a guarantee. It is made here against
the field-level description of the seam; step 2 will produce the concrete postcondition list,
and the check must be re-run against *that* before any code exists.

#### 6.1.1 The step-2 definition gate

The outcome of that re-run is **not** a `calibration_outcome`. Those five values (§7) score a
measured specimen; this fires at step 2, before an interpreter or a measurement exists, and
needs its own vocabulary:

```text
step2_definition_gate

  PASS
      at least one of D1-D3 survives the concrete projection.
      §5.1 calibration is runnable; proceed to step 3.

  FAIL_NO_ELIGIBLE_SPECIMEN
      none of D1-D3 survives.
      Stop E1-v1 before implementation and before any measurement.
      Per P-038 §5.1 this kills the implementation or the definition,
      NOT the research hypothesis. Preserve the record; redesign only
      as E1-v2.
```

One surviving specimen is the minimum for §5.1 to be runnable at all, and that is what the
gate tests. It is deliberately *not* "all three must survive" — requiring that would stop a
runnable calibration over a catalog-breadth concern, which is a different question and gets
its own record:

```text
class_coverage      which defect classes retain a surviving specimen
                    absence   -> D1
                    misbinding -> D2, D3
```

A class with no survivor is **declared out of scope for E1-v1 results** and may not be
claimed in the write-up. Concretely: if D1 falls but D2/D3 stand, calibration proceeds and
the absence class is reported as untested — never as tested-and-negative.

Both the gate outcome and `class_coverage` are recorded whichever way they land, and neither
may be resolved by re-siting a defect in this document.

**C2 stays distinguishable.** C2 is D1 plus one assertion that the projection excludes,
added to the plan as a declared exception. D1 is a producer-side absence, so C2's added
assertion inspects exactly the value the boundary hides — the field of the frame handed to
the substituted collaborator — and the contrast C2 exists to draw is intact while C2 remains
local.

### 6.2 Mutation-representability rule

Frozen classification, decided per defect **from the frozen StrykerJS operator catalog and
the recorded causal region, before the measured run**:

```text
representable
    some operator in the frozen catalog, applied at a single location
    inside the causal region of the clean baseline, yields a program whose
    behaviour on the entire frozen subset is identical to the injected defect

not_representable
    no operator in the frozen catalog can do so — typically because the
    defect is the absence of a construct, leaving nothing at the causal
    point to mutate

indeterminate
    deciding would require a search beyond the frozen enumeration budget
```

The enumeration budget is frozen in the manifest. `indeterminate` is a real outcome and is
reported, not resolved by assertion.

---

## 7. Measurements recorded per specimen

Recorded machine-readably, raw, per specimen. No scalar summary score is produced — the E1
document's prohibition on collapsing these into a vanity score is binding here.

```text
detected_by_local_suite            bool
assigned_witness                   W1..W6
witness_green_on_baseline          bool   (§4.1 counterfactual, arm 1)
witness_fails_on_injected          bool   (§4.1 counterfactual, arm 2)
detected_by_composition_witness    bool   (per witness id)
mutation_representable             representable | not_representable | indeterminate

  measured on BOTH revisions, recorded separately and never interchanged:
  baseline_*  = harness qualification      injected_*  = the §5.1 evidence

baseline_seam_line_coverage        float
baseline_seam_branch_coverage      float
baseline_seam_mutation_score       float
baseline_seam_unassessed           {no_coverage, timeout, ignored, compile_error}
injected_seam_line_coverage        float
injected_seam_branch_coverage      float
injected_seam_mutation_score       float
injected_seam_unassessed           {no_coverage, timeout, ignored, compile_error}

  raw mutant records, per revision — the authority from which the two
  bools below are COMPUTED, never hand-set. source_file/span is the raw
  evidence; locus is a CLASSIFICATION derived from it against the frozen
  region definitions, and is recomputable from the raw fields:
baseline_mutants                   [{mutant_id, operator, status,
                                     source_file, span, locus}]
injected_mutants                   [{mutant_id, operator, status,
                                     source_file, span, locus}]
    locus: causal_region | seam_adjacent | outside   (derived)
mutation_report_ref                immutable reference to the full engine
                                   report for each revision, kept verbatim

  derived, kept per revision so an INCONCLUSIVE stays attributable:
baseline_unassessed_in_causal      bool   (§3.3.1 via condition 3)
injected_unassessed_in_causal      bool   (§3.3.1 via condition 6)

  provenance — what was actually measured, not what was intended:
baseline_revision_sha              the exact commit measured as clean
injected_revision_sha              the exact commit measured as defective
test_domain_id                     calibration_local | c2_control   (§3.2.1-2)
test_domain_digest                 digest of that domain's test-ID list
                                   (calibration_local_test_set_digest, or
                                    c2_control_test_set_digest for C2)
toolchain_digest                   pinned (language, runner, coverage,
                                   mutation engine) version tuple (§2)
repo_wide_coverage                 float  (context only, never a threshold)
repo_wide_mutation_score           float  (context only, never a threshold)
defect_class                       D1..D4 | C1a | C1b | C2
semantic_seam                      seam id
boundary_field                     one of §1.2
local_assertions_touching_field    int
requires_post_composition_state    bool
proxy_verdict                      likely_witnessed | likely_unwitnessed | indeterminate
proxy_version                      e1-static-test-proxy/v0
in_calibration_slice               bool
calibration_outcome                PASS | FAIL_PROXY | INVALID
                                   | INCONCLUSIVE_PROXY
                                   | INCONCLUSIVE_UNASSESSED
                                   | n/a
calibration_failing_condition      1..7 | null   (lowest-numbered, §5.3.1 rule 2)
```

The two `INCONCLUSIVE` kinds are distinct values, not one value with a comment: proxy
abstention and an unmeasured causal region are different states with different remedies, and
a single label would make the §5.3.1 rates unreportable. `baseline_unassessed_in_causal` and
`injected_unassessed_in_causal` are likewise kept apart so that a recorded
`INCONCLUSIVE_UNASSESSED` can always be traced to the revision that caused it — with one
shared bool the record could not say whether condition 3 or condition 6 had fired.

---

## 8. Freeze manifest — staged and append-only

An earlier version of this section asked for one manifest, before the first measured run,
carrying both final test-domain digests, the source regions, the baseline revision sha and
every defect's `fault_patch`. That is not constructible. The first measured run is the
Baseline A qualification (Step 2 §10 step 3), and at that moment the realised `LT-BR-*` set
does not exist — it is enumerated from the clean Baseline B at step 6 — while `fault_patch`
describes injections that come later still. The demand was for a document to contain values
that its own deadline preceded.

The resolution is **not** to soften the freeze. It is to stage the manifest and make it
append-only: the *rules* freeze at the first measurement exactly as §0 promises, and the
*values* those rules produce are appended later, by a procedure that was already frozen.

```text
M0  protocol manifest        written BEFORE Baseline A (Step 2 §10 step 3)
      Step 0 and Step 2 document revisions (git sha of each)
      resolved oracle case-index lists, level A and level B      (§1.4)
      pinned toolchain versions                                  (§2)
      the 213 core case IDs and plan_core_digest                 (Step 2 §8)
      c2_control_core_digest                                     (Step 2 §9)
      the observation projection, case rule, input enumeration
        and branch-search procedure, by reference and revision
      the defect and control catalog                             (§6)
      the proxy version id                                       (§5.1)

M1  clean-baseline record    appended BEFORE qualification (Step 2 §10 step 6)
      the exact clean Baseline B revision sha
      seam_adjacent_region and causal_region per seam            (§3.2, §3.3.1)
      the realised LT-BR-* list
      final_calibration_domain and final_c2_domain, with
        test_domain_digest and c2_control_test_set_digest        (Step 2 §9.1)
      the StrykerJS operator catalog as used and the enumeration
        budget                                                   (§6.2)

M2  specimen record          appended BEFORE each injected measurement
      the exact injected revision sha
      id, class, semantic_seam, boundary_field, assigned_witness (§4.1)
      fault_patch, expected_trigger, expected_semantic_difference
      the §6.2 representability classification
```

**Append-only is the load-bearing word.** An earlier stage is never rewritten, and a later
stage may not contradict one. If M1 or M2 cannot be written as the frozen rules require —
a region that cannot be delimited, a branch with no frozen witness — that is a stop
condition under Step 2 §8.2.2, not a licence to revise M0.

No stage carries a post-hoc claim about which technique did or did not detect a defect.

---

## 9. What Step 0 authorises

Only this document. No interpreter, no harness, no injection, no measurement.

The next steps, in order, each gated on the previous:

1. **freeze** — this document reviewed and merged;
2. **normative semantics + projection + local-test plan** — the complete semantics (§3.1.1),
   the declared local test boundary and observation projection (§3.1.2), and the exhaustively
   enumerated plan derived from them (§3.1.3), all frozen **before** any test or interpreter
   code is written. The §6.1 paper check is re-run against the concrete postcondition list at
   this point and scored by the **step-2 definition gate** (§6.1.1): `PASS` if at least one
   of D1–D3 survives, `FAIL_NO_ELIGIBLE_SPECIMEN` if none does — in which case E1-v1 stops
   here, before implementation and before any measurement, and is resolved by an `E1-v2`
   rather than by re-siting a defect. `class_coverage` is recorded either way;
3. **Baseline A** — interpreter for §1.1, green on its oracle slice, harness + coverage +
   mutation + manifest replay all demonstrated working;
4. **local suite** — instantiated from the frozen plan, meeting the §3.3 thresholds with
   `NoCoverage == 0` (§3.3.1) **measured against the calibration local suite alone**
   (§3.2.1), both it and `c2_control_suite` enumerated with their digests recorded,
   committed **before** any defect exists;
5. **Baseline B** — the seam of §1.2, green on the full oracle set, **and every assigned
   witness W1–W6 green** (§4.1 arm 1);
6. **proxy** — gated on the §5.1.1 circularity check, then `e1-static-test-proxy/v0`
   implemented exactly as §5.1 specifies;
7. **injection and measurement** — catalog §6, recorded per §7, both revisions measured.

> **Steps 3–7 are superseded by [E1 Step 2 §10](./E1-step2-semantics-and-plan.md#10-revised-implementation-sequence).**
> The ordering above was not executable: it placed the local-suite qualification before
> Baseline B, while the frozen plan contains level-B postconditions — asking for coverage and
> mutation thresholds over production code that does not yet exist. Step 2 §10 resequences so
> that the clean Baseline B precedes qualification, and the realised test domain is frozen
> after it but **before any defect exists**. Steps 1–2 above stand unchanged. This amendment
> is made before any measured run, which §0 permits.

A null result is acceptable and is preserved. Redesign after seeing results belongs to
`E1-v2` and to a new preregistration document, never to an edit of this one.
