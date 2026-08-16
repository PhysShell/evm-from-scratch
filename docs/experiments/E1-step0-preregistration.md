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

`GAS` is included **as a stack producer with no accounting behind it**: it pushes a frozen
constant. It is here only because the upstream `DELEGATECALL` fixture passes a gas argument,
and dropping that fixture would cost the `address` / `storage_owner` seam its witness. Gas
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

### 3.1 Local test authoring rule (anti-tuning)

Local tests are **derived mechanically from the frozen semantics document**, never from the
defect catalog:

1. one test per documented postcondition of each production function;
2. additional tests only as needed to reach the §3.3 branch-coverage threshold;
3. at the seam, the far side **must** be a test double — a caller-side test constructs a
   stub callee frame, a callee-side test is handed a stub frame it does not build.

**The defect catalog in §6 may not be consulted while authoring local tests.** The
authoring commits must precede the first injection commit in git history, and that ordering
is a checkable post-hoc audit of this rule. If it is violated, the affected specimens leave
the calibration slice.

The reason is blunt: if the person writing the local tests knows which boundary field a
defect will corrupt, "the local tests happened not to assert that field" stops being a
finding and becomes an authoring decision.

### 3.2 Seam-adjacent region

Every measurement below is **local to the seam**, never repository-wide. For each seam the
freeze manifest names an explicit `seam_adjacent_region`: the production functions
containing (a) caller-side construction of the boundary-carried fields and (b) callee-side
consumption of and guarding on them. Repository-wide coverage and repository-wide mutation
score are recorded for context and are **not** admissible as the §3.3 thresholds.

### 3.3 Thresholds

Frozen, and required of the **clean baseline** before any injection:

| Measurement | Threshold over `seam_adjacent_region` |
|---|---|
| Line coverage | ≥ 95% |
| Branch coverage | ≥ 90% |
| Mutation score | ≥ 90%, computed as killed / (killed + survived) |

Mutants reported `NoCoverage`, `Timeout`, `Ignored` or `CompileError` are **excluded from
the denominator and reported separately as raw counts**. Folding a no-coverage mutant into
either side of the ratio is prohibited: the whole point of the experiment is that local
adequacy was genuinely high, and a denominator that hides uncovered code manufactures
exactly the adequacy being claimed.

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

Using upstream fixtures as witnesses is deliberate: they were written to teach EVM
semantics, not to catch our injected defects, so they cannot be accused of being shaped
around the mechanism we hope to demonstrate.

A witness "fails" for a specimen iff its asserted stack/success outcome differs from the
upstream expectation. Witness cases are excluded from the §1.4 oracle green-suite
requirement (see §1.4) and from the §3 local suite.

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

### 5.2 Admission to the slice

A specimen enters the calibration slice iff, in this order:

1. it is drawn from Baseline B (§1.2) — level A specimens are ineligible by construction;
2. its defect's causal region is the production, propagation, or guarding of a
   boundary-carried field (§1.2);
3. its local suite satisfies the §3.1 authoring rule, git-history-checkable;
4. its local tests substitute the far side at the seam (§3.1.3).

### 5.3 Calibration decision rule

For an admitted specimen, **CALIBRATION PASS** iff all six hold:

```text
1. clean baseline green on the oracle set                       (§1.4)
2. composition witness fails on the injected specimen           (§4)
3. full local suite green on the injected specimen              (§3)
4. seam-adjacent line ≥95% and branch ≥90% on the baseline      (§3.3)
5. seam-adjacent mutation score ≥90% on the baseline            (§3.3)
6. proxy returns likely_unwitnessed for the corrupted field     (§5.1)
```

Conditions 1–5 construct the §5.1 specimen; condition 6 is the detector obligation E1's
general question does not carry.

**If 1–5 hold and 6 fails**, the outcome is `CALIBRATION FAIL — proxy`. Per P-038 §5.1 this
kills the implementation or the proxy definition, **not the research hypothesis**: it is
recorded, the proxy may be revised under a new version id, and the specimen stays in the
record. It is not evidence against boundary blindness.

**If any of 1–5 fails**, the outcome is `SPECIMEN INVALID` with the failing condition named.
An invalid specimen is not a result about detection in either direction.

**If 6 returns `indeterminate`**, the outcome is `CALIBRATION INCONCLUSIVE — proxy abstained`.
It is never silently read as either pass or fail, and the abstention rate across specimens
is reported alongside every calibration result.

---

## 6. Defect and control catalog

Frozen. At least one specimen from **each** of D1, D2, D4, C1 and C2 must be built and
measured before any E1 result is written up. The catalog deliberately does not consist only
of absence defects.

| ID | Class | Seam field | Injection | Expected local | Expected witness |
|---|---|---|---|---|---|
| **D1** | boundary **absence** | `static` | the callee-side write guard is not implemented at all | passes | W6 fails |
| **D2** | boundary **misbinding** | `address` | `DELEGATECALL` sets the callee's `address` to the callee instead of the caller | passes | W4 fails |
| **D3** | boundary **misbinding** | `caller` | `CALL` propagates the transaction origin as `caller` instead of the immediate caller | passes | W3 fails |
| **D4** | exceptional **propagation** | `success` | callee `REVERT` is flattened into a normal return | passes | W2 fails |
| **C1** | **negative control** — ordinary local fault | none | off-by-one in `SUB`, or `LT` implemented as `≤` | **fails** | fails |
| **C2** | **positive control** — boundary fault with a local oracle | `static` | as D1, but the local suite contains an explicit assertion on the guard | **fails** | W6 fails |

**C1** exists to show the local apparatus catches what it should — an experiment in which
local evidence never catches anything is measuring a broken harness. **C2** exists to show
the seam is not intrinsically invisible: when the local oracle is present, the boundary
defect is caught locally. C2's local suite is a documented, deliberate exception to §3.1
and is marked as such in its manifest.

A corpus of hand-picked blind spots would be, in the E1 document's own words, uselessly
self-congratulatory. D1 in particular must not be treated as the canonical or first
calibration witness merely because it matches an absence mechanism already observed in
Own.NET. We already know absence defects are interesting; building a stand around the
mechanism we intend to demonstrate and then demonstrating it is not evidence.

### 6.1 Mutation-representability rule

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
detected_by_composition_witness    bool   (per witness id)
mutation_representable             representable | not_representable | indeterminate
seam_adjacent_line_coverage        float
seam_adjacent_branch_coverage      float
seam_adjacent_mutation_score       float
mutation_excluded_counts           {no_coverage, timeout, ignored, compile_error}
repo_wide_coverage                 float  (context only, never a threshold)
repo_wide_mutation_score           float  (context only, never a threshold)
defect_class                       D1..D4 | C1 | C2
semantic_seam                      seam id
boundary_field                     one of §1.2
local_assertions_touching_field    int
requires_post_composition_state    bool
proxy_verdict                      likely_witnessed | likely_unwitnessed | indeterminate
proxy_version                      e1-static-test-proxy/v0
in_calibration_slice               bool
calibration_outcome                PASS | FAIL_PROXY | INVALID | INCONCLUSIVE | n/a
```

---

## 8. Freeze manifest

Before the first measured run, one machine-readable manifest records: the resolved oracle
case-index list (§1.4), the pinned tool versions (§2), the `seam_adjacent_region` per seam
(§3.2), the StrykerJS operator catalog as used (§6.1), the enumeration budget (§6.1), the
proxy version id (§5.1), and the baseline revision sha.

Per injected defect, the manifest carries the fields already specified by the E1 document —
`id`, `class`, `semantic_seam`, `baseline_revision`, `fault_patch`, `expected_trigger`,
`expected_semantic_difference` — plus `boundary_field` and the §6.1 representability
classification. It carries **no** post-hoc claim about which technique did or did not detect
the defect.

---

## 9. What Step 0 authorises

Only this document. No interpreter, no harness, no injection, no measurement.

The next steps, in order, each gated on the previous:

1. **freeze** — this document reviewed and merged;
2. **Baseline A** — interpreter for §1.1, green on its oracle slice, harness + coverage +
   mutation + manifest replay all demonstrated working;
3. **local suite** — authored under §3.1, to the §3.3 thresholds, committed **before** any
   defect exists;
4. **Baseline B** — the seam of §1.2, green on the full oracle set;
5. **proxy** — `e1-static-test-proxy/v0` implemented exactly as §5.1 specifies;
6. **injection and measurement** — catalog §6, recorded per §7.

A null result is acceptable and is preserved. Redesign after seeing results belongs to
`E1-v2` and to a new preregistration document, never to an edit of this one.
