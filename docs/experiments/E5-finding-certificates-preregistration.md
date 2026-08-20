# E5 — Replayable finding certificates (preregistration)

**Working title:** proof-carrying findings feasibility.

**Status:** preregistration only. This document contains no implementation and authorises
none beyond §14.5. It is **frozen by the merge event defined in §14.1**, under the
mechanically checkable predicate of §14.2. Nothing in it may be revised after the first
governed E5 run (§14.4); a defect discovered after that point produces an `E5-v2`, never an
edit in place.

**Discipline:** [experiments README](./README.md) principle 2 — freeze the inputs,
vocabulary, transformations and decision rules before running the experiment they govern.

**Design cutoff:** `8f5aaeda667b2fecd7963f53806811b24cc36607` (§1).

---

## 0. What E5 is, and what it is not

### 0.1 The question

> Can a complex or untrusted analyzer attach to a finding a compact **derivation
> certificate** that a small, independent verifier checks against **nothing but** a frozen
> canonical fact bundle and a closed, versioned set of inference rules — such that the
> verifier rejects any conclusion whose premises are missing, substituted, mismatched in
> revision or site, or logically insufficient?

E5 studies the **derivation layer** and only the derivation layer. It asks whether a
conclusion follows from evidence that has already been presented. It does not ask whether
that evidence is right, complete, or worth having.

### 0.2 The five questions, kept apart

| | Question |
|---|---|
| **E1** | is local assurance sufficient for a boundary defect? |
| **E2** | does an execution satisfy a frozen constraint system? |
| **E3** | where do assurance mechanisms disagree? |
| **E4** | did the semantic outcome survive evidence transport? |
| **E5** | **does the finding follow from the canonical facts presented?** |

E5 is **not** an `E1-v6`, **not** a part of E3, and **not** an extension of E4. It shares
E1's *specimens* and shares nothing else with it (§6.4).

### 0.3 Explicit non-goals

E5 does not investigate, and no E5 result may be cited about:

- EVM correctness, or MiniEVM correctness;
- adequacy of tests, coverage, or mutation analysis;
- the P-038 association hypothesis, or any incidence/prevalence claim;
- correctness or completeness of the fact extractor (§2.2 — this is a *limit of the
  guarantee*, not a footnote);
- completeness of static analysis in general;
- zero-knowledge proofs, succinctness, or any cryptographic soundness property beyond the
  collision resistance assumed of the digest function;
- SARIF transport fidelity (that is E4's surface);
- production adoption of proof-carrying findings in Own.NET or OwnAudit (§15).

### 0.4 Prior art, used for one architectural principle only

The shape

```text
friendly proof producer
        ↓
primitive derivation
        ↓
small independent checker
```

is long-established in proof engineering, and is the pattern Jan Mas Rovira's Hilbert/eDSL
work is cited here for. It is used as **prior art for that architectural principle and for
nothing else**. No DSL, type system, term language, tactic vocabulary or naming convention
is transferred. No source material from that work was consulted while writing this document;
the principle above is the entire borrowing, and E5's fact model, rule forms and identity
constraints are derived from the frozen E1 documents named in §1.2 and from P-038 §3.

---

## 1. Design cutoff, provenance, and what was deliberately not read

### 1.1 The cutoff

```text
E5_DESIGN_CUTOFF_SHA = 8f5aaeda667b2fecd7963f53806811b24cc36607
```

`H2` — the merge that closed the unfrozen E1-v4 history. The E5 branch is cut from this
commit and **not** from the head of the E1-v5 work that was in flight when E5 was designed.

The reason is not procedural tidiness. E5 must choose its proof vocabulary, its completeness
rules and its adversarial cases **before** anyone has seen which certificate is easiest to
build. A vocabulary selected after seeing E1-v5's measurements would be a vocabulary selected
to succeed.

**`E5_DESIGN_CUTOFF_SHA` is not `freeze_base_sha`.** They answer different questions and are
deliberately kept apart (§14.2):

```text
E5_DESIGN_CUTOFF_SHA   what was knowable to this document's author.
                       An epistemic fact. NEVER changes — changing it would be a
                       claim that E5 was designed with information it did not have.

freeze_base_sha        which state of the default branch the freeze event is
                       anchored to, topologically.
                       A git fact. Changes only by the recorded successor
                       procedure of §14.2, and changes nothing scientific.
```

An earlier revision of this document equated the two. That was convenient while the branch
point and the merge base were the same commit, and wrong as soon as anything else landed
first — see the topology amendment log in §14.2.

### 1.2 What was read

Frozen at the cutoff, blob shas recorded so the reading is checkable:

```text
docs/experiments/README.md                        24b28d89c5313ae7c7f5c97b12db956c8109c986
docs/experiments/E1-step0-preregistration.md      c294d724ce50952db4642f9ef757a3f7a6bf33b6
docs/experiments/E1-step2-semantics-and-plan.md   586bb92f66d9c6c889a9c2266832264d526a87b4
docs/experiments/E1-v1-STOP.md                    dc029ca830ca82a552558208ba582d226ec7e3a8
docs/experiments/E1-v2-STOP.md                    7648316e82e88d81a04d54269a7f3f463299f917
docs/experiments/E1-v3-STOP.md                    ae594fd2f5ec0c56e5006b80fc5ddd8a40bc8b23
docs/experiments/E1-v4-STOP.md                    ca4fea7868e71bd50b857ed68f0d3605f0897f5e
docs/experiments/E2-plonky3-zkvm.md               4a5c805fb72f0822cb621fe39d008539e1cd2f19
docs/experiments/E3-testing-vs-proof.md           6de98e19ca9aa36864964cacd729bc68bc7818a6
docs/experiments/E4-outcome-fidelity.md           a326e178027113d8224d5281d792e516c847e5f4
```

Read-only, in other repositories, as production boundary context:

```text
PhysShell/Own.NET   docs/proposals/P-032-own-arch-facts.md
PhysShell/Own.NET   docs/proposals/P-038-boundary-transition-witness.md
PhysShell/OwnAudit  src/OwnAudit.Core/Finding.cs
PhysShell/OwnAudit  docs/architecture-review.md
PhysShell/OwnAudit  report/sarif.py
```

Nothing in those repositories is changed by E5 (§15).

### 1.3 What was deliberately not read, and why

E1-v4-STOP §1.2 disqualified a preregistration for being *shaped by outcomes observed before
the freeze it was asking for*. That ruling is binding here, so the exclusions are stated as
facts about this document's authorship rather than as intentions:

- **No E1-v5 material.** No E1-v5 preregistration, branch, PR #6 content, measurement,
  result record, manifest or STOP document was read. No E1 tooling was executed. No branch
  search was run. No `M0`/`M1`/`M2` was created. No coverage, mutation or test run was
  performed for E5's benefit.
- **No E1 implementation source.** Nothing under `experiments/e1/src/`,
  `experiments/e1/test/`, `experiments/e1/tools/`, `experiments/e1/manifest/` or
  `experiments/e1/records/` was read. Only the directory and file *names* were listed, and
  only to write the exclusion paths in §6.4 and §11.
- **No specimen source, injected or clean.** At the cutoff no injected revision exists at
  all (§4.6), so the fact model and ruleset of §5 and §7 could not have been fitted to a
  specimen: **there is no specimen to fit them to.** This is a stronger anti-tuning
  guarantee than any E1 version has had, and it is available only because E5 is being
  written now rather than after E1-v5 lands.

Everything below is derived from the frozen documents in §1.2, on paper, which §14.5
permits and requires.

### 1.4 One disclosure

The ruleset of §7 and the canonical derivation skeletons of §8 were written together, in
one pass, from Step 2 §3.4 and Step 0 §6. That co-design is unavoidable — a rule vocabulary
and the derivations it must support cannot be authored blind to each other — and it is
disclosed rather than dressed up as independence. What carries the anti-tuning weight is
§1.3: both are fixed before any specimen source exists.

---

## 2. Trusted boundary

### 2.1 The pipeline

```text
frozen specimen source revision
        ↓
TRUSTED-FOR-E5 fact extractor
        ↓
canonical fact bundle                    (frozen by digest in E5-M1, §14.3)
        ↓
UNTRUSTED certificate producer
        ↓
finding claim + detached certificate
        ↓
small independent verifier               (§9)
        ↓
VALID  |  INVALID(reason_code, step_index?)
```

Everything above the bundle is trusted by assumption. Everything below it is trusted by
nothing.

### 2.2 The limit of the guarantee

**E5 does not prove that fact extraction is correct.**

If the extractor misrepresents the source, the verifier can *correctly* certify a conclusion
that is false about the source. A `VALID` verdict means exactly:

> the declared conclusion follows, under ruleset `E5-RULES/v1`, from the facts in the bundle
> whose digest this certificate names.

It does not mean the conclusion is true of the program. That is not a caveat attached to the
result; it is the shape of the result. Any E5 write-up that states `PASS` without stating
this sentence overclaims.

Two consequences are load-bearing and are enforced elsewhere in this document:

1. **Completeness assumptions must be facts, never verifier behaviour** (§3). A verifier
   that decided for itself that a bundle was complete would be silently re-importing the
   trust it is supposed to withhold.
2. **The adversarial producer may forge certificates, never bundles** (§10.4/A17). A
   producer that can also forge facts is outside E5's threat model, and E5 makes no claim
   against it. Pretending otherwise would be E5 claiming an extractor guarantee it has not
   got.

### 2.3 The producer may abstain; the verifier may not

The producer's output vocabulary:

```text
CERTIFICATE(...)
ABSTAIN(reason)
```

`ABSTAIN` reasons are a closed set:

```text
NO_SEAM_SITE_FACT        no SEAM_SITE fact for the target site/revision
NO_BINDING_FACT          no CONSTRUCTION_WRITE fact for the target site/field
NO_COMPLETENESS_WITNESS  a negative claim was requested with no CONSTRUCTION_WRITES_COMPLETE
NO_SPEC_FACT             no SPEC_REQUIRED_BINDING fact for the target site/field
UNMODELLED_BINDING       a required BindingExpr contains UNMODELLED (§5.2)
BINDINGS_AGREE           actual and required bindings are equal; there is nothing to claim
NO_APPLICABLE_RULE       no frozen rule licenses a step from the available premises
```

The verifier's output vocabulary is **exactly two shapes**:

```text
VALID
INVALID(reason_code, step_index?)
```

The verifier has no `ABSTAIN`, no `INDETERMINATE`, no `WARN`. Abstention is an epistemic
right of the *producer*, which may decline to claim. A checker handed a certificate has been
asked a closed question and must answer it deterministically on the bytes it was given.

This is a deliberate asymmetry with P-038 §3.1, where the *static proxy* must be able to
abstain and `indeterminate` is first-class. The proxy is a producer of claims about a seam;
the E5 verifier is a checker of a claim already made. Giving a checker an abstention would
create exactly the third state that lets an unverifiable certificate be reported as "not
rejected".

---

## 3. The epistemic invariant — absence is not proven absence

This section is the centre of E5. Everything in §5, §7 and §9 exists to make it structural
rather than promised.

### 3.1 The forbidden inference

```text
    no FACT(X) in the bundle
    ------------------------            PROHIBITED
           NOT_X
```

The absence of a fact from a bundle is a fact about the bundle, not about the world. It is
equally consistent with "X does not hold", "the extractor does not model X", "extraction was
truncated", and "the bundle was filtered".

This is P-038 §3.2 — *absence requires proof the camera was on* — carried from the
observation layer down into the derivation layer:

```text
P-038 §3.2      no observation   !=  not_observed
E5   §3.1       no fact          !=  fact of absence
```

### 3.2 The closed-domain rule

A negative conclusion is admissible only when a **positive** premise explicitly carries the
closed domain over which the negation is taken:

```text
CONSTRUCTION_WRITES_COMPLETE(revision r, site s,
                             scope FRAME_CONSTRUCTION,
                             recorded_fields F)
SPEC_REQUIRED_BINDING(spec v, site s, field f, ...)
SEAM_SITE(revision r, site s)
f ∉ F
------------------------------------------------------------
SEAM_FIELD_NOT_BOUND(r, v, s, f)
```

The negation `f ∉ F` is taken over `F`, a set written **inside the payload of a fact that is
present**. It is never taken over the bundle. The completeness witness is what makes the
statement decidable, and it is itself an ordinary fact that can be missing, forged, or
scoped to the wrong subject — and that is exactly why §10 attacks it four ways
(A12a, A13a–c) instead of trusting it.

### 3.3 Structural enforcement — no quantification over the bundle

The rule above would be worth little if the verifier could reach the bundle directly. So it
is not given it:

> **The verifier kernel never receives the fact bundle.** It receives a `Certificate` and an
> opaque `FactResolver` whose entire surface is `Resolve(fact_id) -> Fact | NOT_FOUND`, and it
> may call it only on `fact_id` values that appear explicitly in the certificate.

The bundle is held by exactly one module, `BundleLoader`, which does exactly three things and
hands the kernel none of them:

1. parses the bundle bytes into a private `fact_id -> Fact` map (a duplicate key is a parse
   failure, §9.2 V5);
2. computes the bundle digest over the canonical serialization (§5.5);
3. constructs the `FactResolver` over that private map.

The kernel therefore has no search, no filter, no count, no "is there a fact such that…" —
not because it declines to, but because it has no name for the collection. There is no
expressible computation by which it could observe that something is *missing* and conclude
anything from it; the only thing a missing referenced id can produce is
`INVALID(PREMISE_NOT_FOUND)`.

§9.3 freezes that architecture and gives it five mechanical checks, `K1`–`K5`. §12.2 `G3`
makes a breach of any of them a soundness failure rather than a note.

**One permitted exception, narrowly stated.** The loader's two bundle-wide computations —
parse well-formedness and digest recomputation — can *only* produce `INVALID`. They are not
inferences and are allowed. The rule is: **the verifier may quantify over the bundle only in
ways that can never satisfy a premise or license a conclusion**, and §9.3 confines every such
quantification to one module that returns no facts.

**And one thing that looks like a violation and is not.** The fact-sufficiency test of §8.5
*does* quantify over the bundle: it asks whether any fact fills a slot. It is run by the E5
run harness, never by the verifier; it produces a **run outcome** (§12.2 G5) and never a
proposition; and no certificate's verdict depends on it. Keeping it outside the kernel is
deliberate — the moment a checker is allowed to ask "is there a fact such that…", §3.1 is
back on the table.

### 3.4 What this does not buy

The closed-domain rule makes a completeness assumption *visible and attributable*. It does
not make it *true*. `CONSTRUCTION_WRITES_COMPLETE` is produced by the trusted-for-E5
extractor (§2.2), so a certificate can be `VALID` over a completeness witness that lies.
E5's contribution here is that the lie is now a named, revision-bound, site-bound artifact
that someone can be wrong about on the record — instead of an implicit closed-world
assumption baked into a checker.

---

## 4. Specimen eligibility — frozen now, evaluated later

### 4.1 Why this is fixed here

"After E1 we will pick the most suitable defect" is a deferred choice wearing a
commitment's clothes (Step 0 §6's phrasing, applied to E5). The specimen set is therefore
fixed now, from the already-frozen Step 0 §6 catalog:

```text
D1   boundary ABSENCE,     field `static`,        site U-CALL/STATICCALL
D2   boundary MISBINDING,  field `address`,       site U-CALL/DELEGATECALL
D3   boundary MISBINDING,  field `caller`,        site U-CALL/CALL
```

D4, C1a, C1b and C2 are **not** E5 specimens. D4's causal region is the `success`
propagation path, which E5-RULES/v1 does not model at a construction site (§7.4); C1a/C1b
have no seam field at all; C2 is D1 plus a test-plan exception, which changes E1's local
evidence and nothing E5 reads.

### 4.2 The predicate

`E5-ELIGIBLE(x)` for a candidate E1 specimen record `x`. All clauses must hold:

```text
1.  x.defect_class ∈ { D1, D2, D3 }

2.  an M2 specimen record for x exists in the E1 record, and its own protocol
    (Step 0 §8) placed it BEFORE x's injected measurement

3.  x.baseline_revision_sha is recorded and resolves to a commit in this repository

4.  x.injected_revision_sha is recorded and resolves to a commit in this repository

5.  the two shas differ, and the tree diff between them is exactly the fault_patch
    recorded in x's M2 record — injection identity is unambiguous

6.  x.assigned_witness is recorded, and BOTH arms of the Step 0 §4.1 counterfactual
    have been ADJUDICATED: witness_green_on_baseline and witness_fails_on_injected
    are both recorded as booleans.
        Their VALUES are not read by this predicate. See §4.3.

7.  every source path touched by x's recorded fault_patch exists in BOTH trees,
    so the E5 extractor has, on each revision, the frame-construction source it
    must read. This clause names the fault_patch and not any E1 region vocabulary,
    so it survives E1 renaming `seam_adjacent_region` or `causal_region`.
```

`E5_INPUT_SET := { x : E5-ELIGIBLE(x) }`, evaluated **once**, at a single recorded E1 commit,
and written into `E5-M1` (§14.3) before any verification runs.

### 4.3 Closure clause — what eligibility may not read

No clause of §4.2 reads, and no future reading of it may consult:

```text
proxy_verdict                   calibration_outcome           in_calibration_slice
detected_by_local_suite         detected_by_composition_witness
witness_green_on_baseline VALUE witness_fails_on_injected VALUE
any coverage figure             any mutation figure           any unassessed-mutant state
mutation_representable          calibration_failing_condition
```

**Clause 6 is deliberately "adjudicated", not "satisfied".** Requiring the counterfactual to
*hold* would make E5's input set a function of an E1 *outcome*, and E5 would then be
contingent on E1 succeeding — the exact dependency §0.2 separates the experiments to avoid.
Requiring it to have been *run and recorded* is pure provenance: it certifies that E1 treated
the revision pair as a real measured specimen with frozen shas, which is all E5 needs.

The alternative reading was considered and rejected for that reason. It is recorded here so
that a later reader can see the choice was made deliberately and before any input existed.

A companion honesty note: E5's claims are **source-level**. Whether `W4` actually failed is a
behavioural measurement E5 neither uses nor speaks to. A specimen whose witness did not fire
is still a specimen about whose source a certificate can be built or honestly refused.

### 4.4 All eligible inputs are used

If several of D1–D3 are eligible, **E5 uses all of them**. There is no selection step, no
"primary specimen", and no dropping of an inconvenient one: §12.2 G5 makes a single
insufficient specimen decide the whole run's outcome, precisely so that subsetting cannot buy
a better result.

### 4.5 `claim_class_coverage`

Recorded whichever way it lands, exactly as Step 0 §6.1.1 requires of E1:

```text
absence     -> D1
misbinding  -> D2, D3
```

A class with no eligible specimen is **declared out of scope for that E5 run's results and
may not be claimed in the write-up.** In particular, if D1 is not eligible, the absence /
completeness-witness machinery of §3 has no primary certificate to exercise and the
D1-scoped adversarial cases (A12a, A13a–c, A14d) are `NOT_APPLICABLE`. Such a run may reach
`PASS`, but that `PASS` may not be cited as evidence about the absence invariant — the
run's record must carry `absence: untested`.

Because that is a real weakening, class-independent tests of the same machinery are mandatory
in every run that has any eligible specimen. `A14c` and `A14e` run against the clean baseline
bundle, `A16` and `A17` against the starved bundle; both bundles exist for every specimen
regardless of class, and together they exercise the rule preconditions and the producer's
abstention duty from the negative side (§10.4). They are weaker than a D1 primary certificate
and are not offered as a substitute for one.

### 4.6 If no input is ever eligible

```text
E5 = BLOCKED_NO_ELIGIBLE_E1_INPUT
```

This is a terminal state for that E5 run, not a licence to redesign specimen selection, and
**not a negative result about proof-carrying findings**. A growing pile of blocked runs is
not a growing pile of findings — the sentence E1 has now owed itself four times.

**State at the design cutoff.** E1 has never reached its injection step. E1-v1, v2 and v3
stopped before it and E1-v4 was never frozen; no `M2` record and no injected revision exists
at `8f5aaed`. Evaluated today, `E5_INPUT_SET = {}` and E5 is `BLOCKED_NO_ELIGIBLE_E1_INPUT`.
That is a fact about E1's progress, not an obstacle to freezing this document: every rule
below is derived from frozen *semantics*, and none of them needs an input to be *written*.
E5 is preregisterable now and runnable only later. §17.1 states this as the run's standing
blocker.

---

## 5. Canonical facts

### 5.1 Identity model

Two revision namespaces, kept apart so that a spec fact and a source fact can never be
spliced into one another's role:

```text
spec_revision      the blob sha of docs/experiments/E1-step2-semantics-and-plan.md
                   as of E5_DESIGN_CUTOFF_SHA, i.e.
                   586bb92f66d9c6c889a9c2266832264d526a87b4

source_revision    a git commit sha of this repository, naming the tree the
                   extractor read
```

A **site** is:

```text
SiteId := "U-CALL/CALL" | "U-CALL/STATICCALL" | "U-CALL/DELEGATECALL"
```

Per P-038 §3.5, site identity is **revision-scoped**. Every source-namespace fact carries its
`source_revision`, and **no rule in §7 relates facts from two different source revisions.**
E5 therefore never asserts cross-revision site equivalence, and inherits P-038's non-goal
rather than quietly solving it.

Identity is structural. **No rule, premise constraint or conclusion may be keyed on message
text, human-readable labels, file paths, or line spans.** `source_file` and `span` appear in
one payload (§5.3) as provenance for a human reader; nothing in §7 or §9 reads them.

### 5.2 `BindingExpr` — a closed algebra

```text
FrameField := code | pc | stack | memory | address | caller | static
            | storage_owner | returndata            (Step 2 §2 field order)

BindingExpr :=
      CALLEE_ADDRESS              the `address` operand of the call
    | CURRENT_FRAME(FrameField)   a field of the constructing (caller) frame
    | CODE_AT(BindingExpr)
    | LITERAL_BOOL(true | false)
    | ZERO
    | EMPTY
    | UNMODELLED(token)
```

`UNMODELLED` is mandatory honesty, not a fallback. An extractor that cannot map a source
expression into this algebra **must** emit `UNMODELLED(token)` and must never coerce.

Structural equality of two `BindingExpr` terms is decided syntactically over this algebra.
A term is **fully modelled** iff it contains no `UNMODELLED` node at any depth.

**Rules that compare bindings require both sides fully modelled** (§7.2, R3 and R5). Without
that precondition, `UNMODELLED(x) ≠ CURRENT_FRAME(address)` would read as a misbinding, and a
parser failure would manufacture findings. This is the single most important soundness guard
in the ruleset after §3.3.

### 5.3 Fact kinds — closed set, `E5-FACTS/v1`

| kind | namespace | subject | payload |
|---|---|---|---|
| `SPEC_REQUIRED_BINDING` | spec | (site, field) | `postcondition_id`, `required: BindingExpr` |
| `SEAM_SITE` | source | site | `source_file`, `span` (provenance only, §5.1) |
| `CONSTRUCTION_WRITE` | source | (site, field) | `bound_to: BindingExpr` |
| `CONSTRUCTION_WRITES_COMPLETE` | source | site | `scope`, `recorded_fields: FrameField[]` |
| `FRAME_FIELD_DEFAULT` | source | field | `default: BindingExpr` |

`scope` is drawn from a closed set; `E5-RULES/v1` recognises exactly one value,
`FRAME_CONSTRUCTION`. Any other value is well-formed and simply fails the rule precondition
that requires it (§7.2 R2) — which is what makes A13c a real test rather than a parse error.

There is **no fact kind meaning "field f is not written"**, and no rule may introduce one.
The only route to a negative proposition is R2, through a completeness witness (§3.2).

### 5.4 The frozen spec-fact set

`SPEC_REQUIRED_BINDING` facts are a transcription of Step 2 §3.4, not an authoring exercise.
The complete set for `E5-RULES/v1` is fixed here so that the implementer transcribes rather
than chooses — 3 sites × 9 frame fields = 27 facts, all with
`spec_revision = 586bb92f66d9c6c889a9c2266832264d526a87b4`:

| site | field | required | from |
|---|---|---|---|
| `U-CALL/CALL` | `address` | `CALLEE_ADDRESS` | `SEM-SEAM-P1` |
| `U-CALL/CALL` | `caller` | `CURRENT_FRAME(address)` | `SEM-SEAM-P2` |
| `U-CALL/CALL` | `static` | `CURRENT_FRAME(static)` | `SEM-SEAM-P3` |
| `U-CALL/CALL` | `storage_owner` | `CALLEE_ADDRESS` | `SEM-SEAM-P4` |
| `U-CALL/STATICCALL` | `address` | `CALLEE_ADDRESS` | `SEM-SEAM-P5` |
| `U-CALL/STATICCALL` | `caller` | `CURRENT_FRAME(address)` | `SEM-SEAM-P6` |
| `U-CALL/STATICCALL` | `static` | `LITERAL_BOOL(true)` | `SEM-SEAM-P7` |
| `U-CALL/STATICCALL` | `storage_owner` | `CALLEE_ADDRESS` | `SEM-SEAM-P8` |
| `U-CALL/DELEGATECALL` | `address` | `CURRENT_FRAME(address)` | `SEM-SEAM-P9` |
| `U-CALL/DELEGATECALL` | `caller` | `CURRENT_FRAME(caller)` | `SEM-SEAM-P10` |
| `U-CALL/DELEGATECALL` | `static` | `CURRENT_FRAME(static)` | `SEM-SEAM-P11` |
| `U-CALL/DELEGATECALL` | `storage_owner` | `CURRENT_FRAME(storage_owner)` | `SEM-SEAM-P12` |
| *each site* | `code` | `CODE_AT(CALLEE_ADDRESS)` | `SEM-SEAM-P13` |
| *each site* | `pc` | `ZERO` | `SEM-SEAM-P14` |
| *each site* | `stack` | `EMPTY` | `SEM-SEAM-P15` |
| *each site* | `memory` | `EMPTY` | `SEM-SEAM-P15` |
| *each site* | `returndata` | `EMPTY` | `SEM-SEAM-P15` |

Deliberately excluded, with the reason stated so it is a scope condition and not an
oversight:

- **`U-ENTRY` / root-frame postconditions (`SEM-ROOT-1..7`).** D1–D3 all sit at `U-CALL`
  producing sites. Adding `U-ENTRY` would widen the fact model to host no specimen.
- **Consuming-side and relational postconditions (`SEM-SEAM-C*`, `SEM-RET-*`,
  `SEM-REL-*`).** These are about execution, not construction; E5 reads source structure.
- **`success`.** It is a boundary-carried field in Step 0 §1.2, but it lives in
  `FrameResult`, not in the constructed `Frame`. `E5-RULES/v1` can express no claim about it
  (§7.4), which is why D4 is not an E5 specimen (§4.1).

### 5.5 `fact_id`, canonicalization, and the bundle digest

Frozen, because leaving them to the implementer would leave a tuning surface:

```text
canonicalization    RFC 8785 JSON Canonicalization Scheme (JCS)
digest              SHA-256, lowercase hex

fact_id             sha256( JCS( fact object with its `fact_id` field removed ) )
fact bundle         a JSON object mapping fact_id -> fact
fact_bundle_digest  sha256( JCS( the bundle object ) )
```

**`fact_id` is content-derived and position-independent.** This is not a convenience: it is
what makes A15 (§10.4) a meaningful test. If ids were positional, adding an unrelated fact
would renumber existing ones and every certificate would break for a reason that has nothing
to do with derivation. Content-derived ids also mean that two facts differing only in
`source_revision` have different ids, which is what makes A14b bite.

The verifier recomputes the id of every **referenced** fact (§9.2 V9c). It does not audit
unreferenced ones; an unreferenced malformed fact affects a certificate only through the
bundle digest, which is exactly the behaviour A11/A15 pin down.

### 5.6 What the extractor may not do

Binding on the trusted-for-E5 extractor, and checkable by review of its output:

- it must not emit a fact asserting that something is absent (§5.3);
- it must not emit `CONSTRUCTION_WRITES_COMPLETE` for a site it did not enumerate
  exhaustively — a completeness witness is a claim, and emitting one speculatively is the
  extractor lying in the one place E5 has no defence (§3.4);
- it must not coerce an unparseable expression into a modelled `BindingExpr` (§5.2);
- it is run **once per source revision**, and its output bundle digest is written into
  `E5-M1` before any verification runs (§14.3). Re-extraction after a rejection is a
  protocol violation and yields `INVALID_EXPERIMENT`.

---

## 6. Conclusions, certificates, and the E1 firewall

### 6.1 Proposition shapes — closed set

Propositions are the *only* things a step may derive and the *only* things a certificate may
declare as its conclusion. There is no free-text conclusion, ever.

```text
P1  SEAM_FIELD_BOUND_AS   (source_revision, site, field, BindingExpr)
P2  SEAM_FIELD_NOT_BOUND  (source_revision, spec_revision, site, field)
P3  SEAM_FIELD_MISBOUND   (source_revision, spec_revision, site, field,
                           required: BindingExpr, actual: BindingExpr)
P4  BOUNDARY_DEFECT_PRESENT(source_revision, spec_revision, site, field,
                           kind: ABSENCE | MISBINDING)
```

`P4` is E5's primary claim shape. `P1`–`P3` are intermediate, and may also stand as a
certificate's final conclusion — which is what lets a producer make an honest weaker claim
instead of abstaining entirely.

### 6.2 Certificate schema `E5-CERT/v1`

```text
Certificate {
  schema_version      "E5-CERT/v1"
  ruleset_id          "E5-RULES/v1"
  spec_revision       blob sha (§5.1)
  source_revision     commit sha (§5.1)
  fact_bundle_digest  sha256 hex (§5.5)
  conclusion          Proposition
  steps               ProofStep[]        ordered, non-empty
}

ProofStep {
  rule_id             a rule id of the declared ruleset
  premises            PremiseRef[]       order is significant; slots are positional
  derived             Proposition        the producer's claim, RECOMPUTED by the verifier
}

PremiseRef := { fact: fact_id } | { step: index }     1-based, must be < this step's index
```

### 6.3 Identity binding

A certificate's identity is the tuple

```text
( schema_version, ruleset_id, spec_revision, source_revision,
  fact_bundle_digest, conclusion )
```

Every one of these is checked (§9.2). Together they make the following impossible without
detection: replaying a D2 certificate against D3's facts (site identity inside `conclusion`
and inside every rule's constraints), replaying an injected-revision certificate against the
clean baseline (`source_revision` + content-derived fact ids), and swapping the ruleset or
schema underneath a derivation.

`steps[i].derived` is carried in the certificate but is **never authority**. The verifier
recomputes it and compares; a mismatch is `STEP_PROPOSITION_MISMATCH`. Carrying it costs a
few bytes and buys a detectable failure mode (A8) that a verifier computing silently would
not have.

**What identity binding cannot do.** The verifier checks that the certificate's declared
revisions agree with the facts it references. It cannot check that the declared
`source_revision` is the revision anyone *wanted* a claim about — it has no other source of
truth, by construction (§9.1). Choosing which revision to ask about belongs to the caller, and
`A5` establishes only that a certificate cannot silently disagree with itself.

### 6.4 No E1 implementation, in either direction

```text
PROHIBITED   E5 verifier  ->  experiments/e1/src/*
PROHIBITED   E5 verifier  ->  experiments/e1/tools/*
PROHIBITED   E5 producer  ->  experiments/e1/src/*
PROHIBITED   E5 producer  ->  experiments/e1/tools/*
PROHIBITED   E5 extractor ->  experiments/e1/src/*    (as a library)
PROHIBITED   E5 verifier  ->  E5 producer, E5 extractor
```

**Reuse the specimen, not the implementation.** E5 consumes E1 *revisions* and *records* —
git shas and manifest values — and reads specimen source only as **text**, through its own
extractor. The extractor reading a `.ts` file's bytes from a checked-out revision is
permitted; importing anything from `experiments/e1/` as a module is not.

E5's own space is `experiments/e5/`. **This preregistration creates none of it** — no
directory, no schema file, no fixture (§14.5).

---

## 7. Inference vocabulary — `E5-RULES/v1`

### 7.1 Rule form

Every rule is a fixed record. Nothing about it is negotiable at certificate-construction
time:

```text
rule_id
arity                    an integer; the step must supply exactly this many premises
slots[1..arity]          each declares a required kind:
                           an input fact kind (§5.3), or a derived proposition shape (§6.1)
identity constraints     equalities that must hold ACROSS premises
preconditions            conditions on premise payloads
conclusion function      a TOTAL function of the resolved premises,
                         computed by the verifier
```

Binding rules on the whole set:

- a rule may not accept a producer-supplied conclusion — `derived` is always recomputed;
- a rule may not accept a free parameter; every value in the conclusion comes from a premise;
- an unknown `rule_id` is always `INVALID(UNKNOWN_RULE)` — there is no default, no fallback,
  no "unrecognised rules are skipped";
- the ruleset id is part of certificate identity (§6.3). Any change to any rule, constraint,
  precondition or conclusion function produces `E5-RULES/v2` and does not edit `v1`.

### 7.2 The rules

Constants of the ruleset:

```text
BOUNDARY_CARRIED_FIELDS = { address, caller, static, storage_owner, returndata, success }
                          (Step 0 §1.2, verbatim)
RECOGNISED_SCOPE        = { FRAME_CONSTRUCTION }
```

---

**`R1` — `SITE_BINDING`** · arity 2

```text
slot 1   fact  SEAM_SITE(source_revision r, site s)
slot 2   fact  CONSTRUCTION_WRITE(source_revision r2, site s2, field f, bound_to b)

identity      r = r2 ,  s = s2
precondition  b is fully modelled
derives       SEAM_FIELD_BOUND_AS(r, s, f, b)
```

---

**`R2` — `ABSENCE_UNDER_COMPLETENESS`** · arity 3 · *the only negative-conclusion rule*

```text
slot 1   fact  SEAM_SITE(source_revision r, site s)
slot 2   fact  CONSTRUCTION_WRITES_COMPLETE(source_revision r2, site s2,
                                            scope sc, recorded_fields F)
slot 3   fact  SPEC_REQUIRED_BINDING(spec_revision v, site s3, field f, required b_req)

identity      r = r2 ,  s = s2 = s3
precondition  sc ∈ RECOGNISED_SCOPE
              f ∉ F                            <- the closed-domain negation, §3.2
derives       SEAM_FIELD_NOT_BOUND(r, v, s, f)
```

The field `f` is supplied by slot 3, a fact — never by the producer. Nothing here quantifies
over the bundle.

---

**`R3` — `MISBINDING`** · arity 2

```text
slot 1   step  SEAM_FIELD_BOUND_AS(r, s, f, b_act)
slot 2   fact  SPEC_REQUIRED_BINDING(spec_revision v, site s2, field f2, required b_req)

identity      s = s2 ,  f = f2
precondition  b_act and b_req are both fully modelled
              b_act ≠ b_req   (structural inequality over §5.2)
derives       SEAM_FIELD_MISBOUND(r, v, s, f, b_req, b_act)
```

---

**`R4` — `DEFECT_FROM_MISBINDING`** · arity 1

```text
slot 1   step  SEAM_FIELD_MISBOUND(r, v, s, f, b_req, b_act)

precondition  f ∈ BOUNDARY_CARRIED_FIELDS
derives       BOUNDARY_DEFECT_PRESENT(r, v, s, f, MISBINDING)
```

`R4` is not a relabelling. Its precondition is E1's own definition of what makes a defect a
*boundary* defect (Step 0 §1.2), and it is what stops E5 manufacturing a boundary-defect
claim about `pc` or `code`.

---

**`R5` — `DEFECT_FROM_ABSENCE`** · arity 3

```text
slot 1   step  SEAM_FIELD_NOT_BOUND(r, v, s, f)
slot 2   fact  FRAME_FIELD_DEFAULT(source_revision r2, field f2, default d)
slot 3   fact  SPEC_REQUIRED_BINDING(spec_revision v2, site s2, field f3, required b_req)

identity      r = r2 ,  v = v2 ,  s = s2 ,  f = f2 = f3
precondition  f ∈ BOUNDARY_CARRIED_FIELDS
              d and b_req are both fully modelled
              b_req ≠ d
derives       BOUNDARY_DEFECT_PRESENT(r, v, s, f, ABSENCE)
```

`b_req ≠ d` is doing real work: an omitted write whose silent default happens to equal what
the specification requires is not a defect, and E5 must not certify it as one.

### 7.3 Rules that deliberately do not exist

Stated so that a later reader can see the vocabulary was bounded on purpose:

- **No rule with a bundle-negative premise.** Only `R2`, through an explicit closed domain.
- **No rule relating two source revisions.** P-038 §3.5 (§5.1).
- **No rule about `success`, returndata propagation, or callee-side guarding.** That is D4's
  and `SEM-REL-*`'s territory, it needs an execution or two-sided model E5 does not have,
  and adding it would let E5 quietly become E1-v6 (§0.2).
- **No transitivity, weakening, or generic structural rule.** E5 is not a theorem prover;
  the vocabulary is exactly what D1–D3's claim shapes need and stops there.
- **No rule taking a producer-chosen constant.** Every conclusion component traces to a
  premise.

### 7.4 Expressible claim space

`E5-RULES/v1` can express exactly: `BOUNDARY_DEFECT_PRESENT` of kind `MISBINDING` or
`ABSENCE`, at one of three `U-CALL` construction sites, about one of the five frame fields in
`BOUNDARY_CARRIED_FIELDS ∩ FrameField` (`address`, `caller`, `static`, `storage_owner`,
`returndata`), plus the three intermediate shapes. Everything else is out of scope by
construction, declared here rather than discovered when it is inconvenient.

---

## 8. Canonical derivation skeletons

### 8.1 Why they are frozen here

§14.5 prohibits "manually constructing a working derivation and then writing the rules around
it". The defence against it is not to leave the derivation open — that would just move the
choice to the implementer, after the facts are visible. The defence is to fix the derivation
now, on paper, from the frozen semantics, while no specimen exists to fit it to (§1.3).

These skeletons are **falsifiable predictions**, not guarantees. If a skeleton does not
verify against a real bundle, that is a result (§12.2), not an invitation to write a
different skeleton.

### 8.2 `D1` — `U-CALL/STATICCALL`, field `static`, kind `ABSENCE`

```text
S1  R2  ABSENCE_UNDER_COMPLETENESS
      p1  fact  SEAM_SITE(r, U-CALL/STATICCALL)
      p2  fact  CONSTRUCTION_WRITES_COMPLETE(r, U-CALL/STATICCALL,
                                             FRAME_CONSTRUCTION, F)
      p3  fact  SPEC_REQUIRED_BINDING(v, U-CALL/STATICCALL, static,
                                      LITERAL_BOOL(true))
      ->  SEAM_FIELD_NOT_BOUND(r, v, U-CALL/STATICCALL, static)

S2  R5  DEFECT_FROM_ABSENCE
      p1  step  S1
      p2  fact  FRAME_FIELD_DEFAULT(r, static, LITERAL_BOOL(false))
      p3  fact  SPEC_REQUIRED_BINDING(v, U-CALL/STATICCALL, static,
                                      LITERAL_BOOL(true))
      ->  BOUNDARY_DEFECT_PRESENT(r, v, U-CALL/STATICCALL, static, ABSENCE)
```

conclusion = `S2.derived`.

### 8.3 `D2` — `U-CALL/DELEGATECALL`, field `address`, kind `MISBINDING`

```text
S1  R1  SITE_BINDING
      p1  fact  SEAM_SITE(r, U-CALL/DELEGATECALL)
      p2  fact  CONSTRUCTION_WRITE(r, U-CALL/DELEGATECALL, address, CALLEE_ADDRESS)
      ->  SEAM_FIELD_BOUND_AS(r, U-CALL/DELEGATECALL, address, CALLEE_ADDRESS)

S2  R3  MISBINDING
      p1  step  S1
      p2  fact  SPEC_REQUIRED_BINDING(v, U-CALL/DELEGATECALL, address,
                                      CURRENT_FRAME(address))
      ->  SEAM_FIELD_MISBOUND(r, v, U-CALL/DELEGATECALL, address,
                              CURRENT_FRAME(address), CALLEE_ADDRESS)

S3  R4  DEFECT_FROM_MISBINDING
      p1  step  S2
      ->  BOUNDARY_DEFECT_PRESENT(r, v, U-CALL/DELEGATECALL, address, MISBINDING)
```

### 8.4 `D3` — `U-CALL/CALL`, field `caller`, kind `MISBINDING`

Identical in shape to §8.3 with `site = U-CALL/CALL`, `field = caller`,
`required = CURRENT_FRAME(address)`, `actual = CALLEE_ADDRESS`.

**D2 and D3 carry the same `required`/`actual` pair.** Under Step 0 §6, D2 misbinds
`DELEGATECALL`'s `address` to the callee and D3 misbinds `CALL`'s `caller` to the callee's own
address; both are `CALLEE_ADDRESS` against a required `CURRENT_FRAME(address)`. The *only*
thing separating the two certificates is `(site, field)` identity — which makes A6b (§10.4)
a genuinely sharp test rather than a formality.

### 8.5 Fact sufficiency — the mechanical test that separates two outcomes

Evaluated per eligible specimen `s`, before any verdict is interpreted:

```text
INSUFFICIENT_KIND
    some input-fact premise slot of s's skeleton cannot be filled by ANY fact in
    s's primary bundle matching that slot's declared KIND and SUBJECT IDENTITY
    (site / field / revision namespace)

INSUFFICIENT_PAYLOAD
    every slot fills, but some filling fact's payload contains UNMODELLED in a
    position the skeleton's rules require to be fully modelled (§5.2)

SUFFICIENT
    otherwise
```

This test inspects **kind and subject identity only** for `INSUFFICIENT_KIND`, and the
`UNMODELLED` predicate only for `INSUFFICIENT_PAYLOAD`. It never runs a rule's identity
constraints, never runs its preconditions, and never compares bindings.

That boundary is what stops one input producing two outcomes. Everything the sufficiency test
looks at is a property of the **fact model and extraction contract**; everything it declines
to look at is a property of the **ruleset**.

**And note what `FAIL_FACT_MODEL` is not.** It says E5's own frozen fact model failed to
serve a claim it committed to. It says nothing about whether the extractor faithfully
reflected the source — which E5 cannot test at all (§2.2).

### 8.6 Expected-claim status — the test that keeps the last outcome honest

Sufficiency deliberately declines to compare bindings. That leaves a case the outcome
vocabulary must not misname. Consider an eligible D2 whose injected revision, for whatever
reason, carries

```text
actual   = CURRENT_FRAME(address)
required = CURRENT_FRAME(address)
```

Every fact is present, every payload is modelled, so `sufficiency = SUFFICIENT`. The honest
producer then correctly answers `ABSTAIN(BINDINGS_AGREE)`: **according to the canonical facts
there is no defect to certify.** Routing that to a derivation-failure outcome would be false
— nothing failed to derive, there was nothing to derive.

This is not a hypothetical corner. §4.3 requires the E1 witness counterfactual to have been
*adjudicated*, not *satisfied*, precisely so that E5 never depends on an E1 outcome — which
means a specimen whose injection did not do what the catalog says is **not excluded by
construction**, and E5 must have a name for it.

So a second frozen classification is evaluated per specimen, after `sufficiency = SUFFICIENT`
and **before any producer is invoked**. It compares the facts filling the skeleton slots
against payloads this document has already written down in §8.2–§8.4 — nothing new is chosen
here:

```text
D1   the CONSTRUCTION_WRITES_COMPLETE fact filling S1 slot 2 has
        scope           == FRAME_CONSTRUCTION
        static          ∉  recorded_fields
     the FRAME_FIELD_DEFAULT fact filling S2 slot 2 has
        default         == LITERAL_BOOL(false)

D2   the CONSTRUCTION_WRITE fact filling S1 slot 2 has
        bound_to        == CALLEE_ADDRESS

D3   the CONSTRUCTION_WRITE fact filling S1 slot 2 has
        bound_to        == CALLEE_ADDRESS

EXPECTED_CLAIM_SUPPORTED       every comparison above holds
EXPECTED_CLAIM_CONTRADICTED    any of them does not
```

The `SPEC_REQUIRED_BINDING` side needs no comparison: §5.4 freezes all 27 spec facts, so the
required bindings are fixed by this document and the only variable is what the extractor
found in the source.

`EXPECTED_CLAIM_CONTRADICTED` routes to its own outcome, `INVALID_EXPECTED_CLAIM_INPUT`
(§12.2 G6). It is an **input-integrity** result: the E1 record says this revision carries
defect `Dn`, and the canonical facts extracted from it say otherwise. The two live causes are
an injection that did not do what Step 0 §6 describes, and an extractor that misread the
source — and E5 can distinguish neither, which is exactly why it must not dress the situation
up as a result about certificates.

Three outcomes therefore partition cleanly, and each names a different broken thing:

```text
FAIL_FACT_MODEL              the facts needed are not there, or not modelled
INVALID_EXPECTED_CLAIM_INPUT the facts are there and say the claim is false
FAIL_DERIVATION_FEASIBILITY  the facts are there and support the claim, and no
                             valid certificate for it was obtained
```

---

## 9. The verifier

### 9.1 Structural constraints

The verifier:

- does **not** read specimen source code;
- does **not** invoke, import, or link E1 (§6.4);
- does **not** import the certificate producer, the fact extractor, or any analyzer state;
- does **not** search for a proof — it checks the one it was handed, in the order it was
  handed;
- does **not** repair, complete, normalise, or re-order a certificate;
- does **not** heuristically match facts: resolution is by exact `fact_id`, never by
  similarity, kind-and-nearest-site, or any fallback;
- does **not** use the network, spawn processes, write files, or evaluate code carried in a
  certificate;
- checks the `ruleset_id` against the single closed, versioned ruleset it embeds;
- walks steps strictly in the given order, `1..n`;
- resolves a premise only to an input fact or to a **previously verified** step
  (`{step: j}` requires `j < i`), never forward;
- **recomputes** every step's proposition and compares it to the declared one;
- **recomputes** the final conclusion and compares it to the declared one;
- is deterministic on identical input bytes.

**No LOC threshold is imposed.** A line count is a target to be gamed, not a property. The
kernel's smallness is instead pinned by its *obligations* (the list above), its *capability
boundary* (§9.3 `K1`–`K5`) and its *dependency surface* (§11.2 `S1`–`S4`): a checker that must
not search, must not read source, is never handed the bundle at all, and must not import three
named trees has very little room to be large — and every one of the checks that enforce those
facts is mechanical.

### 9.2 Rejection ladder — a sequential automaton

Checks are evaluated **in order**; the first that fails decides the verdict and evaluation
stops. This is the same device E1 Step 0 §5.3.1 adopted for the same reason: a decision rule
that admits two answers for one input is not a decision rule. Here it also makes every
adversarial case's `reason_code` predictable in advance (§10.2).

```text
V1   certificate bytes parse and validate against E5-CERT/v1   -> MALFORMED_CERTIFICATE
V2   schema_version == "E5-CERT/v1"                            -> UNKNOWN_SCHEMA_VERSION
V3   ruleset_id == the embedded ruleset's id                   -> UNKNOWN_RULESET
V4   conclusion is a well-formed instance of a §6.1 shape      -> UNKNOWN_CONCLUSION_SHAPE
V5   bundle bytes parse and validate against E5-FACTS/v1
       (a duplicate fact_id key is a parse failure)            -> MALFORMED_BUNDLE
V6   sha256(JCS(bundle)) == cert.fact_bundle_digest            -> BUNDLE_DIGEST_MISMATCH
V7   steps is non-empty                                        -> EMPTY_DERIVATION
V8   every step's rule_id is in the embedded ruleset           -> UNKNOWN_RULE

V9   for i = 1..n, in ascending order, checks (a)..(h) in order:
       a  |premises| == rule.arity                             -> PREMISE_ARITY_MISMATCH
       b  every premise ref resolves:
            {fact: id} present in the bundle                   -> PREMISE_NOT_FOUND
            {step: j} with 1 <= j < i                          -> PREMISE_FORWARD_REFERENCE
       c  every resolved INPUT fact:
            fact_id == sha256(JCS(fact without fact_id))       -> FACT_ID_NOT_CONTENT_DERIVED
       d  every resolved INPUT fact's revision field matches
            the certificate: source-namespace facts against
            cert.source_revision, spec-namespace facts
            against cert.spec_revision                         -> REVISION_MISMATCH
       e  every premise's kind/shape == the rule's slot kind   -> PREMISE_KIND_MISMATCH
       f  the rule's cross-premise identity constraints hold   -> PREMISE_IDENTITY_MISMATCH
       g  the rule's preconditions hold                        -> RULE_PRECONDITION_UNSATISFIED
       h  recompute(rule, premises) == step.derived            -> STEP_PROPOSITION_MISMATCH

V10  recompute of the LAST step == cert.conclusion             -> CONCLUSION_MISMATCH

     all checks pass                                           -> VALID
```

`INVALID` carries the `step_index` for any failure inside `V9`.

The order is chosen for one reason and it is worth stating: **`V6` (digest) sits above every
premise check**, so any adversarial transform that mutates the bundle without honestly
rebinding the digest stops at `V6` and never exercises the check it was built to test. That
is why §10.1's honest-rebind rule exists, and why `A11` — the one case that *deliberately*
skips the rebind — is paired with `A15`, which performs it.

### 9.3 The capability boundary, and the kernel checks

An earlier draft asked a reviewer to confirm by eye that the verifier "performs no iteration,
filtering, counting, searching or aggregation over the bundle". That put the whole
closed-domain guarantee of §3 — every machine-checked layer above it — on a human reading a
program for the absence of a behaviour. The guarantee is now **structural**: the kernel is
not given anything it could enumerate.

**The frozen architecture.**

```text
BundleLoader                       the ONLY module that ever holds the bundle
    parse bytes -> private map     (a duplicate fact_id is a parse failure, §9.2 V5)
    compute the bundle digest      (§5.5)
    construct a FactResolver over the private map
    return exactly (FactResolver, digest)
         │
         ▼
FactResolver                       an OPAQUE capability, not a collection
    Resolve(FactId) -> Fact | NOT_FOUND        <- its entire surface
         │
         ▼
VerifierKernel                     ladder V7..V10 and the rule engine
    receives exactly (Certificate, FactResolver)
    has no name for the bundle, the map, the parser or the digest
```

The kernel cannot enumerate the bundle for the same reason a program cannot read a file it
has no handle to: it never receives one. "No search over the bundle" stops being a promise
about what the code does and becomes a fact about what it was handed.

**The checks.** Adjudicated under the soundness gate (§12.2 G3, via A12b), because a breach
here is a breach of §3, not of independence.

```text
K1   VerifierKernel's declared inputs are exactly (Certificate, FactResolver).
       The bundle type, the map type, the parser module and the digest module do
       not appear among its declared inputs                            MECHANICAL

K2   VerifierKernel's transitive dependency closure does not contain the
       BundleLoader module, the bundle/map type, the parser, or the digest
       implementation                                                  MECHANICAL

K3   the FactResolver interface declares EXACTLY ONE operation,
       `Resolve(FactId) -> Fact | NOT_FOUND`. It exposes no iterator, no
       length or count, no key set, no collection-valued member, and no
       operation returning more than one Fact                          MECHANICAL

K4   VerifierKernel's closure contains no reflection, dynamic member access,
       dynamic import, or serialization round-trip that could reach past the
       FactResolver interface (§11.2 S2 category (v))                  MECHANICAL

K5   BundleLoader exports exactly one symbol, with exactly the signature
       `load(bytes) -> (FactResolver, digest)`, and no other operation over the
       map escapes the module                                          MECHANICAL
```

**What review is still left, stated exactly.** `K1`–`K5` are all mechanically inspectable, and
together they mean the kernel *cannot* quantify over the bundle whatever its body says. What
they do not do is prove that `load`'s body computes the digest it claims — that is one small
function with one exported signature and no other job, and it is the residue. It is recorded
in the result as `loader_review_statement` (§12.1) and it is honestly a residue, not an
elimination: closing it fully would need a verified toolchain, which E5 does not have and does
not claim. The point of this section is that the residue is now a dozen lines of a loader
rather than the whole checker.

**No meta-validator.** `K1`–`K5` are read off declared types, module closures and exported
surfaces. E5 does not build a validator for the validator; it makes the dangerous capability
absent instead of policing its use.

### 9.4 Reason code vocabulary — closed

```text
MALFORMED_CERTIFICATE        UNKNOWN_SCHEMA_VERSION       UNKNOWN_RULESET
UNKNOWN_CONCLUSION_SHAPE     MALFORMED_BUNDLE             BUNDLE_DIGEST_MISMATCH
EMPTY_DERIVATION             UNKNOWN_RULE                 PREMISE_ARITY_MISMATCH
PREMISE_NOT_FOUND            PREMISE_FORWARD_REFERENCE    FACT_ID_NOT_CONTENT_DERIVED
REVISION_MISMATCH            PREMISE_KIND_MISMATCH        PREMISE_IDENTITY_MISMATCH
RULE_PRECONDITION_UNSATISFIED  STEP_PROPOSITION_MISMATCH  CONCLUSION_MISMATCH
```

No other code exists. There is no `OTHER`, no `UNKNOWN_ERROR`, and no code that means
"rejected for a reason we did not anticipate" — a verifier that needs one has departed from
the frozen ladder, which is a protocol failure (§12.2 G4), not a new code.

---

## 10. Adversarial matrix

### 10.1 One transform, one variable — the honest-rebind rule

An adversarial case that changes two things at once proves nothing: the verdict can be
attributed to either change, and typically stops at whichever check comes first. Every case
below therefore mutates **exactly one** thing, and the mechanical consequences of that
mutation are repaired honestly.

> **Honest rebind.** After any mutation of the fact bundle:
> 1. recompute the content-derived `fact_id` of every mutated or inserted fact (§5.5);
> 2. **repoint** every premise reference that named a mutated fact to that fact's new id;
> 3. recompute `fact_bundle_digest` and write it into the certificate.
>
> Nothing else is touched: `rule_id`s, premise structure, `derived` propositions and the final
> conclusion stay byte-identical to the primary certificate unless the case says otherwise.

Step 2 is the one that is easy to forget and the one that matters most. Without it, a
site-substitution case would reach the verifier as a *dangling reference* and be rejected as
`PREMISE_NOT_FOUND` — testing deletion, not site mismatch, while looking like a pass.

Two cases deliberately **omit** the rebind, and say so: `A11` (bundle digest mismatch) and
`A14a` (naive clean replay). Their whole content is what happens without it.

### 10.2 Expected reason codes are preregistered

Every rejecting case names **exactly one** expected `reason_code`, computed on paper from the
ladder of §9.2. Not a set, not a preference order.

If a case is rejected with a different code, the frozen ladder and the frozen transform
disagree — the preregistration made a wrong prediction about its own machinery. That is a
defect discovered by execution, and it is adjudicated as `INVALID_EXPERIMENT` (§12.2 G4),
never smoothed over by widening the expectation afterwards. It is placed *below* the
soundness gate so that it can never mask an accepted forgery.

### 10.3 Applicability

```text
ALL   runs for every eligible specimen
D1    runs only if D1 is eligible;      otherwise NOT_APPLICABLE (§4.5)
MULTI runs only if >= 2 specimens are eligible; otherwise NOT_APPLICABLE
```

A `NOT_APPLICABLE` case is recorded as such and is not a failure. A case that is *applicable*
but could not be constructed **is** a failure, and yields `INVALID_EXPERIMENT` (§12.2 G0) —
otherwise "we could not build the attack" would silently read as "the attack did not work".

#### A1 is the primary observation, not an adversarial construction

`A1` sits in the matrix for readability, but it is not an attack: it is the primary
certificate being verified. Treating it as a mandatory *construction* created a dead branch in
the automaton, and it is worth spelling out because it was live in an earlier revision:

```text
producer ABSTAIN  ->  no primary certificate exists
                  ->  A1 "could not be constructed"
                  ->  G0 INVALID_EXPERIMENT
                  ->  G7 is never reached
```

which made `primary_verdict = NOT_PRODUCED` — a value added precisely to name the honest
abstention — unreachable. So:

```text
primary_producer_outcome = CERTIFICATE
    A1 is verified. Its verdict IS primary_verdict.

primary_producer_outcome = ABSTAIN
    A1                 = NOT_PRODUCED
    primary_verdict    = NOT_PRODUCED
    adjudication CONTINUES to G5 / G6 / G7. This is not a G0 condition.
```

#### Cases derived from the primary certificate

The same defect reaches further than `A1`: most of the matrix mutates the primary certificate
or its bundle, so if no primary certificate exists none of them can be built either. They are
classified once, here, and their applicability is conditional:

```text
P-cases   consume the primary certificate
          A1, A2, A3, A4, A5, A6a, A6b, A7, A8, A9a, A9b, A10, A11,
          A12a, A13a, A13b, A13c, A14a, A14b, A15

I-cases   independent of it — driven by a bundle and a producer
          A12b, A12c, A14c, A14d, A14e, A16, A17

If primary_producer_outcome = ABSTAIN for a specimen, every P-case for that
specimen is NOT_APPLICABLE(NO_PRIMARY_CERTIFICATE) — recorded, not a failure.
The I-cases still run.
```

**Abstention is not an escape hatch.** A producer cannot dodge the matrix by declining to
emit: abstaining sets `primary_verdict = NOT_PRODUCED`, which reaches `G7` and therefore
cannot reach `PASS`. And the I-cases that still run are exactly the ones that do not need a
cooperative producer — the structural audit `A12b`, the adversarial producer's clean-baseline
attempts `A14c`/`A14d`, and the starved-bundle cases `A16`/`A17`. A silent producer is scored,
not excused.

### 10.4 The matrix

| id | name | applies | the single variable, and the transform | expect |
|---|---|---|---|---|
| **A1** | positive replay — *the primary observation, not an attack (§10.3)* | ALL | none — the primary bundle and the primary certificate, unmodified. If the producer abstained, `NOT_PRODUCED`, and adjudication continues | `VALID` |
| **A2** | deleted premise | ALL | *presence of one required fact.* Delete the fact bound to slot 1 of step `S1` (`SEAM_SITE`). Honest rebind (digest only; the reference is left dangling on purpose) | `INVALID(PREMISE_NOT_FOUND, 1)` |
| **A3** | wrong site | ALL | *one premise's site.* Replace the `SEAM_SITE` fact at `S1` slot 1 with the `SEAM_SITE` fact for the next site in the frozen cyclic order `CALL → STATICCALL → DELEGATECALL → CALL`, same revision. Honest rebind **including repointing** | `INVALID(PREMISE_IDENTITY_MISMATCH, 1)` |
| **A4** | wrong revision, fact-level | ALL | *one premise's `source_revision`.* Replace the `SEAM_SITE` fact at `S1` slot 1 with a copy identical except `source_revision` = the specimen's clean baseline sha. Honest rebind including repointing | `INVALID(REVISION_MISMATCH, 1)` |
| **A5** | wrong revision, certificate-level | ALL | *the certificate's declared revision.* Set `cert.source_revision` to the clean baseline sha. Bundle untouched, digest still correct | `INVALID(REVISION_MISMATCH, 1)` |
| **A6a** | cross-specimen splice, foreign revision | MULTI | *one premise's provenance.* Into specimen `P`'s bundle merge specimen `Q`'s fact occupying the same skeleton slot, carrying `Q`'s `source_revision`; repoint; honest rebind | `INVALID(REVISION_MISMATCH, 1)` |
| **A6b** | cross-specimen splice, revision-normalised | MULTI | *one premise's site/field, with revision made to agree.* As A6a, but rewrite the spliced fact's `source_revision` to `P`'s before inserting, keeping `Q`'s site and field | `INVALID(PREMISE_IDENTITY_MISMATCH, 1)` |
| **A7** | mutated conclusion | ALL | *the declared final conclusion.* Flip `kind`: `MISBINDING → ABSENCE` for D2/D3, `ABSENCE → MISBINDING` for D1. Steps and bundle untouched | `INVALID(CONCLUSION_MISMATCH)` |
| **A8** | mutated intermediate proposition | ALL | *one step's declared proposition.* In `steps[1].derived`, replace `field` with the next field in the frozen `FrameField` order. Nothing else touched | `INVALID(STEP_PROPOSITION_MISMATCH, 1)` |
| **A9a** | rule substitution — arity | ALL | *the final step's `rule_id`.* Swap the defect-forming rule for the other one: `R5 ↔ R4` | `INVALID(PREMISE_ARITY_MISMATCH, n)` |
| **A9b** | rule substitution — typed, unlicensed | D2/D3 | *step `S2`'s `rule_id`.* Replace `R3` with `R1` — same arity 2, different slot kinds | `INVALID(PREMISE_KIND_MISMATCH, 2)` |
| **A10** | unknown rule | ALL | *the final step's `rule_id`.* Replace it with `R99_NOT_A_RULE` | `INVALID(UNKNOWN_RULE)` |
| **A11** | bundle digest mismatch | ALL | *the bundle bytes, with the binding left stale.* Insert one unreferenced fact and **do not** rebind the digest | `INVALID(BUNDLE_DIGEST_MISMATCH)` |
| **A12a** | absence without completeness witness | D1 | *presence of the completeness witness.* Delete the `CONSTRUCTION_WRITES_COMPLETE` fact; rebind the digest; leave the conclusion and the reference in place | `INVALID(PREMISE_NOT_FOUND, 1)` |
| **A12b** | no negative path exists — static audit | ALL | *not a certificate.* Audit the frozen ruleset: no rule derives a negative proposition without a `CONSTRUCTION_WRITES_COMPLETE` premise; and the capability-boundary checks `K1`–`K5` of §9.3 hold | audit passes |
| **A12c** | honest producer on a silent bundle | D1 | *presence of the completeness witness, at the producer.* The A16 starved bundle, at the real producer, asking for the primary claim. This is A16 **with the abstention reason pinned**, not a second transform | `ABSTAIN(NO_COMPLETENESS_WITNESS)` |
| **A13a** | forged witness — wrong site | D1 | *the witness's site.* Replace it with the witness for `U-CALL/CALL`, same revision, same scope; repoint; honest rebind | `INVALID(PREMISE_IDENTITY_MISMATCH, 1)` |
| **A13b** | forged witness — wrong revision | D1 | *the witness's `source_revision`.* Same site and scope, clean-baseline revision; repoint; honest rebind | `INVALID(REVISION_MISMATCH, 1)` |
| **A13c** | forged witness — wrong scope | D1 | *the witness's `scope`.* Same site and revision, `scope = ROOT_FRAME_CONSTRUCTION`; repoint; honest rebind | `INVALID(RULE_PRECONDITION_UNSATISFIED, 1)` |
| **A14a** | clean replay — naive | ALL | *the bundle it is played against.* The primary certificate bytes, unmodified, against the clean baseline bundle | `INVALID(BUNDLE_DIGEST_MISMATCH)` |
| **A14b** | clean replay — honest rebind | ALL | *the bundle it is played against, with the digest repaired.* As A14a, with `fact_bundle_digest` set to the clean bundle's digest. Steps untouched | `INVALID(PREMISE_NOT_FOUND, 1)` |
| **A14c** | clean re-derivation — misbinding | D2/D3 | *the source revision, everything rebuilt honestly.* The A17 adversarial producer emits the D2/D3 skeleton against the clean baseline bundle, with all references and the digest correctly bound | `INVALID(RULE_PRECONDITION_UNSATISFIED, 2)` |
| **A14d** | clean re-derivation — absence | D1 | *the source revision, everything rebuilt honestly.* The A17 adversarial producer emits the D1 skeleton against the clean baseline bundle, whose completeness witness truthfully lists `static` | `INVALID(RULE_PRECONDITION_UNSATISFIED, 1)` |
| **A14e** | honest producer on the clean baseline | ALL | *the source revision, at the producer.* Hand the real producer the clean baseline bundle and ask for the specimen's primary claim | `ABSTAIN(BINDINGS_AGREE)` for D2/D3; `ABSTAIN(...)`, reason from §2.3, for D1 |
| **A15** | irrelevant extra facts | ALL | *the bundle's unreferenced content, honestly rebound.* Merge the complete clean-baseline fact set into the injected bundle; no referenced fact changes, so no repointing is needed; rebind the digest | `VALID` |
| **A16** | insufficient evidence | ALL | *the producer's input.* Hand the real producer the starved bundle (every `CONSTRUCTION_WRITE` and `CONSTRUCTION_WRITES_COMPLETE` for the target site removed) and ask for the primary claim | `ABSTAIN(...)`, reason from §2.3 |
| **A17** | malicious producer | ALL | *the producer.* A preregistered adversarial producer emits a full skeleton over the starved bundle, referencing a fabricated `fact_id` it computed but did not insert | `INVALID(PREMISE_NOT_FOUND, 1)` |

### 10.5 Three notes a hostile reader will want

**A15's merge is well-defined.** A clean-revision fact and an injected-revision fact can never
collide on `fact_id`: `source_revision` is part of every source-namespace fact's content
(§5.5). Spec-namespace facts are byte-identical in both bundles and merge idempotently onto
the same ids. The merge therefore adds facts and changes none.

**A15 is the digest interaction, done honestly.** It changes the bundle and repairs the
binding, which is precisely the thing §10.1 step 3 demands; it is not "edit the bytes after
signing". Its pairing with A11 is the whole point: the same insertion, once with the binding
repaired and once without, must give `VALID` and `BUNDLE_DIGEST_MISMATCH` respectively. And
A15 only works because `fact_id` is content-derived (§5.5) — if ids were positional, the
merge would renumber every existing fact and A15 would fail for a reason that has nothing to
do with derivation.

**A17 forges certificates, not facts.** The adversarial producer is explicitly forbidden from
writing into the fact bundle. A producer that can also fabricate *facts* defeats E5 trivially
and by design (§2.2): the verifier would accept a well-formed derivation over fabricated
premises, correctly. Building an attack E5 cannot survive and then reporting that it survived
would be worse than not running it.

**"Syntactically valid but logically inadmissible" mostly collapses into typed rejection —
and that is a finding.** With five rules of fixed arity and fixed slot kinds, a substituted
rule is almost always caught at `V9a` or `V9e` before any semantic check runs (A9a, A9b). The
nearest thing to a fully well-typed, semantically-refused derivation is A14c/A14d, where every
constraint holds and the rule declines on its *precondition*. That is not a gap being papered
over; it is what a deliberately impoverished vocabulary buys, and it should be reported as
such rather than dressed up as a richer defence than it is.

---

## 11. Independence — a separate acceptance condition

If the checker can only confirm a finding with access to analyzer internals, the experiment
has not demonstrated a replayable certificate. So this is adjudicated on its own, before any
certificate verdict is interpreted (§12.2 G2).

### 11.1 The clean-room run

```text
1.  Create an empty directory OUTSIDE this repository's worktree.
2.  Copy into it ONLY:
        the verifier tree
        the ruleset artifact
        the fact bundle(s)
        the certificate(s)
3.  Absent by construction:
        experiments/e1/**
        the E5 certificate producer
        the E5 fact extractor
        any specimen source tree, clean or injected
        any E1 manifest, record, or measurement
4.  Network access disabled.
5.  Run the verifier over every certificate in the run — primary and adversarial.
```

### 11.2 The checks

```text
S1   the verifier's transitive module closure contains no path under
       experiments/e1/, the producer tree, or the extractor tree
S2   that closure references nothing in these five frozen categories:
       (i)    network access of any kind
       (ii)   process creation or shell invocation
       (iii)  dynamic code evaluation, or code loading not resolvable statically
       (iv)   filesystem WRITE of any kind
       (v)    reflection, dynamic member access, or serialization round-trip
              used to reach past a declared interface       (cf. §9.3 K4)
       E5-M0 records the language-specific identifiers realising exactly these
       five categories, and adds no sixth
S3   two runs, in two different working directories, over identical input bytes,
       yield byte-identical (verdict, reason_code, step_index) for every certificate
S4   the clean-room run yields, for every certificate, the same
       (verdict, reason_code, step_index) as the in-repository run
```

All four are mechanical. The kernel's *capability* constraints — that it is never handed
anything it could enumerate — are `K1`–`K5` in §9.3 and are adjudicated under soundness, not
here. `S1`–`S4` govern what the verifier may **reach**; `K1`–`K5` govern what it may **hold**.
Mixing them would let a failure of one be reported under the other's name.

Category `(v)` is the independence-side companion of §9.3 `K4`: the capability boundary is
only structural if the kernel cannot reflect its way around the interface it was given.

The five `S2` categories are enumerated here rather than deferred to `E5-M0` for the obvious
reason: a deny-list chosen after the freeze is a deny-list chosen by whoever needs it short.

Failure of any clause yields `FAIL_INDEPENDENCE`.

### 11.3 What is not frozen

The verifier's implementation language, file layout, digest *library*, and test runner are
deliberately left open. None of them is a tuning surface: no choice among them can change
which certificates verify, because the ladder (§9.2), the ruleset (§7), the canonicalization
and the digest *function* (§5.5) are all fixed. `S1`–`S4` and `K1`–`K5` are language-agnostic:
each is stated over declared inputs, module closures, exported surfaces and interface shapes,
all of which every plausible implementation language exposes.

---

## 12. Decision rule

### 12.1 Recorded per specimen, raw

No scalar summary score is produced. E1 Step 0 §7's prohibition applies here unchanged.

```text
specimen_id                     D1 | D2 | D3
baseline_revision_sha           from the E1 record (§4.2 clause 3)
injected_revision_sha           from the E1 record (§4.2 clause 4)
e1_m2_record_ref                immutable reference
extractor_revision              the single extractor revision recorded in E5-M1
injected_bundle_digest          sha256
clean_bundle_digest             sha256
primary_certificate_digest      sha256 of the certificate bytes, or null
sufficiency                     SUFFICIENT | INSUFFICIENT_KIND | INSUFFICIENT_PAYLOAD
expected_claim_status           EXPECTED_CLAIM_SUPPORTED
                                | EXPECTED_CLAIM_CONTRADICTED
                                | NOT_EVALUATED   (sufficiency != SUFFICIENT)
primary_producer_outcome        CERTIFICATE | ABSTAIN(reason)
primary_verdict                 VALID | INVALID(reason_code, step_index?) | NOT_PRODUCED
adversarial_results             [{case_id, class, applicable, not_applicable_reason,
                                  verdict, reason_code, step_index,
                                  expected_reason_code, matched}]
                                class: P | I                            (§10.3)
                                not_applicable_reason: null
                                  | NOT_ELIGIBLE_D1 | FEWER_THAN_TWO_SPECIMENS
                                  | NO_PRIMARY_CERTIFICATE
producer_outcome_A16            CERTIFICATE | ABSTAIN(reason)
producer_outcome_A12c           CERTIFICATE | ABSTAIN(reason) | NOT_APPLICABLE
independence_S1..S4             pass | fail, each recorded separately (§11.2)
kernel_K1..K5                   pass | fail, each recorded separately (§9.3)
loader_review_statement         the verbatim recorded review of BundleLoader,
                                  the one residual review obligation   (§9.3)
producer_outcome_A14e           CERTIFICATE | ABSTAIN(reason)
```

Run-level:

```text
e5_input_set                    the evaluated set, with the E1 commit it was read at
claim_class_coverage            absence / misbinding, per §4.5
e5_outcome                      one value from §12.2
invalid_experiment_reason       null, or the specific G0/G4 clause
```

`primary_verdict = NOT_PRODUCED` records the case where the honest producer **abstained** on
the primary claim over a bundle the §8.5 test called `SUFFICIENT`. That is not a soundness
failure — abstaining is always the producer's right (§2.3) — and it is not a fact-model
failure, because the facts were there and fully modelled. Without this value the automaton
would have had a hole: a run in which nothing was forged, nothing was missing, and nothing was
proved.

It reaches `FAIL_DERIVATION_FEASIBILITY` (§12.2 `G7`) only when `expected_claim_status` is
`EXPECTED_CLAIM_SUPPORTED`. When the facts contradict the expected claim, the same abstention
is the *correct* answer and `G6` has already routed the run to
`INVALID_EXPECTED_CLAIM_INPUT` (§8.6). And per §10.3, an abstention makes the P-cases
`NOT_APPLICABLE` rather than unconstructible, so `G0` no longer fires ahead of `G7`.

### 12.2 Aggregate outcome — a sequential automaton

Evaluated in order. The first gate that fires decides the outcome and evaluation stops. One
run, one outcome.

```text
G0   protocol integrity                                  -> INVALID_EXPERIMENT
       any of:
         the run's commit fails E5_FROZEN (§14.2)
         E5-M0 or E5-M1 missing, or written out of the order §14.3 requires
         a recorded specimen sha does not resolve, or its tree differs from
           the E1 M2 record it claims
         the extractor was run more than once for a source revision, or its
           revision differs from the one E5-M1 records
         a bundle digest differs from the one E5-M1 records
         an APPLICABLE mandatory case among A2..A17 could not be constructed
           — A1 is excluded: it is the primary observation, and its absence
           under producer abstention is NOT_PRODUCED, not a protocol failure
           (§10.3). P-cases are NOT_APPLICABLE, not unconstructible, when
           there is no primary certificate
         this document was edited after the first governed E5 run (§14.4)

G1   E5_INPUT_SET is empty                               -> BLOCKED_NO_ELIGIBLE_E1_INPUT

G2   any clause S1..S4 of §11.2 fails                    -> FAIL_INDEPENDENCE

G3   any applicable rejecting case returned VALID
     OR A15 returned anything but VALID
     OR A12c, A14e or A16 returned a CERTIFICATE
     OR A12b's audit failed, incl. any of K1..K5 of §9.3 -> FAIL_SOUNDNESS

G4   any applicable rejecting case returned INVALID with
     a reason_code other than its preregistered one,
     OR A12c abstained with a reason other than
     NO_COMPLETENESS_WITNESS, or A14e for D2/D3 with a
     reason other than BINDINGS_AGREE                    -> INVALID_EXPERIMENT

G5   any eligible specimen has
     sufficiency != SUFFICIENT                           -> FAIL_FACT_MODEL

G6   any eligible specimen has expected_claim_status
     == EXPECTED_CLAIM_CONTRADICTED               (§8.6) -> INVALID_EXPECTED_CLAIM_INPUT

G7   any eligible specimen has
     primary_verdict != VALID                            -> FAIL_DERIVATION_FEASIBILITY
       (covers both INVALID and NOT_PRODUCED, §12.1;
        the sub-cause is RECORDED, not adjudicated — see §12.3)

G8   otherwise                                           -> PASS
```

Why the order is this order, since a first-match automaton is only as good as its ordering:

- **`G2` above `G3`.** A verifier that fails the independence checks is not the artifact E5
  set out to study. Reporting a soundness property of it would attribute that property to
  something that is not the object of study. This mirrors E1 §5.3.1, where condition 7 is
  never reached unless the stand qualifies.
- **`G3` above `G4`.** An accepted forgery is the worst outcome available and must never be
  masked by a bookkeeping disagreement about *which* rejection or abstention reason fired.
  `G3` asks only whether the answer had the right *shape* — rejected, abstained, verified;
  `G4` asks whether it had the right *reason*. A16's reason is deliberately left open (any
  §2.3 value), because which fact the starved bundle is missing first is an extraction detail;
  A12c's and A14e's are pinned, because those two cases exist to test one specific reason each.
- **`G4` above `G5`/`G6`.** If the matrix and the ladder disagree, the rejections are not
  evidence about anything yet, and reading a fact-model or derivation-feasibility result out
  of them would be reading a broken instrument.
- **`G5` above `G6` above `G7`.** These three are ordered by how far upstream the defect is,
  and their triggers are disjoint on a single specimen by construction: `G6` is evaluated only
  where `sufficiency = SUFFICIENT`, and `G7` only where the expected claim is *supported*
  (§8.6). The ordering resolves the remaining case — different specimens firing different
  gates — in favour of naming the most upstream broken thing. A run cannot be reported as a
  derivation failure while one of its inputs is contradicting its own catalog entry.

### 12.3 What `PASS` means, and what it does not

`PASS` means exactly:

> On the frozen MiniEVM specimens listed in this run's `e5_input_set`, this certificate
> architecture is feasible: an untrusted producer built compact derivations that an
> independent verifier accepted from the fact bundle alone, and rejected under every
> preregistered adversarial transformation with the preregistered reason.

`PASS` does **not** mean:

- that Own.NET findings are sound;
- that any fact extractor is complete, or correct (§2.2);
- that production adoption of proof-carrying findings is justified (§15);
- any theorem about C# source, or about any language;
- that P-038 is proven, supported, or advanced (§16);
- that an arbitrary finding family is expressible — `E5-RULES/v1`'s claim space is three
  sites and five fields (§7.4);
- that the absence invariant was exercised, unless `claim_class_coverage` records `absence`
  as covered (§4.5).

`FAIL_DERIVATION_FEASIBILITY` is likewise narrow, and §8.6 is what makes the words accurate.
It says: the facts were present, fully modelled, and actually supported the expected claim, and
**no valid certificate for that claim was obtained** — nothing more.

It deliberately does **not** say why. Two sub-causes are recorded and neither is adjudicated:

```text
primary_verdict = NOT_PRODUCED    the producer abstained
primary_verdict = INVALID(code)   the producer emitted a certificate the verifier rejected
```

An earlier revision called this outcome `FAIL_EXPRESSIVITY`, which asserted more than E5 can
measure: a producer that simply emits a malformed derivation would have been reported as a
frozen calculus that "could not express" the claim, when the calculus may be fine. Separating
producer failure from ruleset inexpressivity needs a second, independently written producer to
act as a control, and E5 has one producer. Naming the outcome after what is observed — no
feasible derivation was obtained — is the honest width.

The remedy differs by sub-cause and is chosen by a human reading the record, not by this
automaton: a defective producer is fixed and the run repeated under the same frozen document
(the producer is not part of the freeze surface, §14.6); a genuinely inexpressive ruleset needs
an `E5-v2` with a new ruleset id, never a rule added to `v1`.

`INVALID_EXPECTED_CLAIM_INPUT` means less than any of them: E5 was handed a revision whose
canonical facts contradict the defect the E1 catalog assigns to it. It is a statement about
that input, it is preserved in the record, and it is **not** evidence about the injection,
about the extractor, or about certificates — E5 cannot tell those apart (§8.6).

---

## 13. What E5 measures, restated in one line

E5 measures **whether a conclusion follows from presented evidence**, and nothing about
whether that evidence was worth presenting. Every gate in §12.2, every rule in §7, and every
row of §10.4 is scoped to that sentence.

---

## 14. Freeze discipline

E1 has stopped four times: twice on frozen documents that turned out defective, once on a
freeze that was never performed, and once on a preregistration contaminated before the freeze
it requested. E5's mechanism is built from those four failures and is deliberately **smaller**
than E1's — a complicated freeze predicate is one more thing that can be defective.

### 14.1 The freeze event

> **The freeze event is the merge commit that first introduces this document into this
> repository's default branch, identified topologically by §14.2 and by nothing else.**

Not its authoring, not its review, not its being committed on a branch. E1-v2 stopped
precisely because *committed* was treated as *merged* (E1-v2-STOP §1). The merge is an event
with a sha.

**It must be an ordinary merge commit — no squash, no rebase, no fast-forward.** A squash or
a fast-forward destroys the two-parent topology §14.2 keys on, and leaves E5 with no
identifiable freeze event at all. This is not a style preference; it is the mechanism.

The merge is performed by the repository owner, not by the author of this document.

### 14.2 `E5_FROZEN` — self-identifying, not selected afterwards

An earlier draft of this section defined `M` as "the merge commit of this document" and then
had `E5-M0` *record* which commit that was. That is a post-hoc selectable anchor sitting at
the exact point of the protocol whose job is to forbid post-hoc selection, and it admits:

```text
M_real     the preregistration is genuinely merged
   ↓
           the document is edited
   ↓
M_fake     some later merge
   ↓
E5-M0      declares M = M_fake
```

All three of the old clauses were satisfied by that history, because nothing in them said `M`
was the commit that *first introduced* the path. `M` is therefore now **computed from git
history**, not declared.

```text
freeze_base_sha := f670258f1e7ef4cf6adbeddeac5a81f4cf981487     (see the log below)
doc_path        := docs/experiments/E5-finding-certificates-preregistration.md

M is the unique commit reachable from the default branch's tip satisfying ALL of:

  (a)  M has exactly two parents
  (b)  M^1 == freeze_base_sha
  (c)  doc_path is ABSENT at M^1
  (d)  doc_path is PRESENT at M^2
  (e)  blob(M:doc_path) == blob(M^2:doc_path)
  (f)  EXACTLY ONE commit reachable from the default branch's tip satisfies
       (a)-(e). Zero  -> E5 is not frozen.
            Two or more -> INVALID_EXPERIMENT; E5 is not frozen and may not be
            frozen by choosing between them.

E5_FROZEN(c) iff
  1.  M exists and is unique per (a)-(f);
  2.  c == M, or c is a descendant of M;
  3.  no commit in M..c modifies doc_path.
```

Every clause is a `git` command. `(b)` anchors the freeze to a commit **this document names
in its own text**, so the anchor is carried by the frozen artifact rather than supplied by a
later manifest. `(c)`/`(d)` make `M` the introducing merge and not merely *a* merge. `(e)`
forbids altering the document while merging it. `(f)` is what closes the substitution above:
a second candidate does not let someone pick; it stops E5.

#### Topology amendment log

`freeze_base_sha` may be changed **only** by the successor procedure below, and every change
is logged here. The log exists so that re-anchoring is countable: a document that had quietly
re-anchored five times would be visibly not frozen at all.

| # | `freeze_base_sha` | why it was set / superseded |
|---|---|---|
| 1 | `8f5aaeda667b2fec…` | initial value, equated with `E5_DESIGN_CUTOFF_SHA`. **Superseded**: the E1-v5 PR merged first, landing `f670258f…` on `main` as an ordinary merge with first parent `8f5aaed…`. Clause `(b)` became unsatisfiable for any future merge. |
| 2 | `f670258f1e7ef4cf…` | current. The tip of `main` after that merge. |

The supersession was executed under the successor rule this section already carried, before
any freeze occurred and before any E5 implementation existed, and it changed **no scientific
surface**: `E5_DESIGN_CUTOFF_SHA`, the `spec_revision` blob shas of §1.2, the fact model, the
ruleset, the skeletons, the adversarial matrix and the decision rule are all untouched. It is
a git fact catching up with git.

Verified at the time of the amendment, because clause `(f)` deserves a check rather than an
assumption: `f670258f…` itself is **not** a candidate for `M`. It has two parents and its first
parent is `8f5aaed…`, so it passes `(a)`–`(c)`, but `doc_path` is absent at its second parent,
so `(d)` fails. It cannot be mistaken for this document's introducing merge.

`E5-M0` still records `M` and the document's blob sha, but now as **audit values that must
equal the computed ones**. A recorded value disagreeing with the computation is
`INVALID_EXPERIMENT` (§12.2 G0), not a tie-break.

**Two operational consequences, and they are binding.**

1. **This document's merge must be the next change to the default branch.** Clause `(b)`
   requires `M^1` to be exactly `freeze_base_sha`. If any other merge lands first, no commit
   can satisfy `(b)` and this document becomes unfreezable as written. The merge must also be
   an ordinary two-parent merge — no squash, no rebase, no fast-forward (§14.1).
2. **If that ordering is missed, E5 is not re-anchored quietly.** The remedy is a new reviewed
   revision of this preregistration naming a new `freeze_base_sha`, opened as an explicit
   successor, with the reason recorded in the log above — the same shape E1-v4-STOP
   established. Silently re-pointing `freeze_base_sha` after the fact would reintroduce
   exactly the defect this section exists to remove.

**The branch is not rebased when this happens.** Re-anchoring changes which commit `M^1` must
be, not where the work was authored. Rebasing the E5 branch onto the new base would rewrite
the commits and destroy the provenance that this document was written at
`E5_DESIGN_CUTOFF_SHA` — which is the one thing §1.3 rests on. An ordinary merge of the
unrebased branch produces `M^1 = freeze_base_sha` and `M^2 = the branch head` with no rewrite
at all.

The cost is real: a stricter predicate has more ways to become unsatisfiable, it couples E5's
freeze to a merge ordering, and it has already cost one recorded re-anchoring. That cost is
accepted, because the alternative is a freeze whose anchor can be chosen after the edits it is
supposed to forbid. Note also what the log makes visible: re-anchoring is cheap for *topology*
and impossible for *content* — no successor may move `E5_DESIGN_CUTOFF_SHA`, so no successor
can buy the author later knowledge.

### 14.3 Two manifests, append-only

`E5-M0` and `E5-M1` are append-only. An earlier stage is never rewritten and a later one may
not contradict it. If a stage cannot be written as these rules require, that is a stop
condition, not a licence to revise the earlier stage.

```text
E5-M0   protocol manifest      written AFTER the freeze merge M,
                               BEFORE any extractor or verifier run
    E5_DESIGN_CUTOFF_SHA                                            (§1.1)
    freeze_base_sha, and the topology amendment log as of the freeze (§14.2)
      — a DISTINCT value from the design cutoff; equating them is the defect
      recorded as log entry 1
    M, the COMPUTED freeze merge sha, together with the (a)-(f) evidence
      — recorded as an audit value that must equal the computed one, never
      as the thing that selects it                                    (§14.2)
    E5_DOC_BLOB_SHA, likewise recomputable from M
    spec_revision  (the E1 Step 2 blob sha, §5.1) and the E1 Step 0 blob sha
    ruleset_id and a digest over the ruleset artifact
    the E5-FACTS/v1 and E5-CERT/v1 schema digests
    the eligibility predicate, fact model, conclusion shapes, rules, skeletons,
      adversarial matrix, verifier ladder and decision rule — by reference to
      this document's sections and its blob sha
    canonicalization and digest function            (RFC 8785 JCS / SHA-256)
    the §11.2 S2 deny-list, all five categories
    the §9.3 capability boundary: the FactResolver interface declaration and
      the BundleLoader exported signature, by reference and digest

E5-M1   input record            appended BEFORE the first verification run
    the commit at which E5_INPUT_SET was evaluated — REQUIRED to be the default
      branch's HEAD at the moment E5-M1 is written, so that eligibility cannot be
      read at a conveniently early commit that excludes an awkward specimen
    E5_INPUT_SET, with each specimen's baseline and injected shas and M2 refs
    claim_class_coverage
    the extractor revision
    the per-revision fact bundle digests, clean and injected
```

One E5 run has exactly one `E5-M1`. If E1 later produces further eligible specimens, that is a
**second E5 run**, with its own `E5-M1` and its own recorded outcome, under this same frozen
document. Both results stand; neither replaces the other, and a later run may not be presented
as a correction of an earlier one.

There is no `E5-M2`. Per-specimen results are outputs, recorded under §12.1, not a manifest
stage: nothing about a specimen needs fixing after `E5-M1` and before its measurement, so
adding a third stage would be ceremony without a job.

**A recorded sha is the target commit, never the manifest commit.** Committing `E5-M0` or
`E5-M1` into this repository moves `HEAD`; every recorded revision denotes the commit the
extraction or verification *runs against*, and every run checks out that recorded sha
explicitly. E1 Step 0 §8 learned this and it carries over unchanged.

### 14.4 The first governed run, and after it

> **The first governed E5 run** is the first execution of the E5 verifier against any fact
> bundle produced by the E5 extractor from a source revision named in `E5-M1`.

From that moment this document is final. A defect found afterwards is preserved and resolved
by an `E5-v2` — a new preregistration document with its own freeze event — never by an edit
in place, and never by widening an expectation that turned out to be wrong.

Before that moment, but after the freeze merge, this document is **not** editable either;
§14.2 clause 3 makes any edit visible and any commit under it fails `E5_FROZEN`. If the
preregistration is found to be logically unimplementable before the first governed run, the
remedy is a new reviewed revision opened as an explicit successor under this same discipline,
with the defect recorded — the same shape E1-v4-STOP established, and for the same reason: a
history that asserts a consistent specification existed before the measurement, when it did
not, is worse than a recorded stop.

### 14.5 What is prohibited before the freeze

```text
PROHIBITED before the E5 freeze merge:
    certificate producer implementation
    verifier implementation
    fact extractor implementation
    running an extractor against actual D1-D3 source, clean or injected
    trial certificates of any kind
    testing whether the proposed rules can prove an actual specimen
    manually constructing a working derivation and then writing rules around it
    creating experiments/e5/ , schema files, fixtures, or tests

PERMITTED and required:
    paper reasoning from the frozen E1 semantic documents of §1.2
```

This preregistration creates exactly one file. `experiments/e5/` does not exist and this
document does not require an empty directory for it.

### 14.6 What the freeze protects

The freeze exists to stop tuning, so it covers the things a later implementer could otherwise
choose after seeing a result:

| protected | where |
|---|---|
| specimen eligibility | §4.2, §4.3 |
| fact model, `BindingExpr`, identity, digest | §5 |
| completeness semantics | §3, §5.3, §7.2 R2 |
| conclusion shapes | §6.1 |
| certificate schema and identity binding | §6.2, §6.3 |
| inference rules | §7 |
| canonical derivation skeletons | §8.2–§8.4 |
| fact-sufficiency test | §8.5 |
| expected-claim classification | §8.6 |
| producer/kernel capability boundary | §9.3 |
| freeze anchor and its topology | §14.1, §14.2 |
| verifier obligations, capability boundary `K1`–`K5`, rejection ladder | §9 |
| adversarial transformations and expected codes | §10 |
| independence requirement | §11 |
| decision rule and its precedence | §12.2 |
| producer / verifier boundary | §2, §9.1 |

Deliberately **not** frozen: implementation language, file layout, digest library, test
runner (§11.3) — and **the producer's implementation**. Its boundary and its obligations are
frozen (§2.3, §9.1, and it may never write into the fact bundle, §10.5), but how it searches
for a derivation is not: that is the whole "friendly proof producer" premise of §0.4, and it
is why a defective producer is repaired and re-run under this same frozen document rather than
requiring an `E5-v2` (§12.3).

---

## 15. Relationship to production — a non-binding transfer hypothesis

Nothing in production changes because of this document, and nothing should change because of
an E5 `PASS` either. Recorded here so the transfer target is on record before the result, not
invented after it.

If E5 returns `PASS`, a **separate future proposal** may investigate:

```text
Own.NET
    canonical facts
    deterministic finding
    detached certificate
        ↓
OwnAudit
    independent verifier
        ↓
    normalization
        ↓
    Finding / SARIF / report
```

with the preferred shape being **related versioned artifacts**, alongside the existing
`own.arch.facts/*` and `own.findings/v1` contracts of P-032:

```text
own.findings/*
own.*.facts/*
own.finding-certificates/*
```

Explicitly **not** proposed, now or as a consequence of `PASS`:

- adding `Derivation[]` — or any proof structure — to `OwnAudit.Core.Finding`. The existing
  `Finding.Evidence → SARIF relatedLocations` and `Finding.Flow → SARIF codeFlows` are
  **presentation and evidence surfaces**, not a proof kernel, and conflating them would put a
  checker's obligations into a reporting type;
- making the SARIF exporter a verifier. A future SARIF result may *carry*
  `certificate_status` and `certificate_id` in `properties`, which is transport of a verdict
  someone else computed. `report/sarif.py` must not compute it.

This mirrors OwnAudit's own treatment of the P-038 overlay: an accepted experiment supplies a
reporting contract, not an adopted product, and it changes no gate verdict.

---

## 16. Relation to P-038

The two guarantees are adjacent and must not be blurred.

```text
P-038 / E1     is the evidence boundary sufficient?
E5             does the conclusion follow from that evidence?
```

P-038 asks whether we have enough evidence — whether a boundary phenomenon can be missed by
local assurance mechanisms, and whether a negative observation is defensible at all. E5 starts
after canonical evidence has been presented and asks only whether the claim follows from it.

Three consequences:

1. **Proof-carrying findings do not solve extractor completeness.** A certificate can be
   `VALID` over incomplete or wrong facts (§2.2). Anyone reading `VALID` as "the finding is
   true" has skipped the sentence in §2.2.
2. **That is exactly why completeness assumptions must be explicit facts** (§3), not an
   implicit closed-world assumption inside a checker. E5's contribution to the P-038 line, if
   any, is that shape — not a stronger guarantee.
3. **E5 borrows P-038 §3.2/§3.3 and P-038 §3.5, and changes neither.** No E5 result may be
   cited as P-038 evidence in any direction, and this document proposes no change to P-038.

---

## 17. Known limitations, and the standing blocker

### 17.1 E5 is preregisterable now and runnable later

At the design cutoff, E1 has produced no injected revision and no `M2` record, so
`E5_INPUT_SET = {}` and any E5 run today returns `BLOCKED_NO_ELIGIBLE_E1_INPUT` (§4.6).

This is a blocker on *execution*, not on *preregistration*, and the distinction is load-
bearing:

- everything frozen above is derived from Step 2 §2/§3.4 and Step 0 §1.2/§6, all of which
  were frozen long before this document;
- no rule, skeleton, transformation or decision gate needs an input in order to be *written*;
- writing them now is strictly stronger than writing them later, because no specimen exists
  to fit them to (§1.3).

Waiting for E1 to finish before preregistering E5 would produce a worse document, not a
better one. So the blocker is recorded and E5 is frozen anyway.

### 17.2 The limitations a reader should weigh

1. **The extractor is trusted and untested** (§2.2). This is the largest limitation and it is
   structural, not incidental.
2. **One residual review obligation remains, and it is the `BundleLoader`** (§9.3). `K1`–`K5`
   are mechanical and make the kernel structurally incapable of enumerating the bundle, so the
   closed-domain guarantee no longer rests on reading the checker for the absence of a
   behaviour. What is left is whether one exported function with one signature computes the
   digest it claims. Eliminating even that would need a verified toolchain; E5 does not have
   one and does not claim to.
3. **The claim space is three sites and five fields** (§7.4). Nothing here generalises to
   arbitrary findings, and §12.3 forbids claiming that it does.
4. **A well-typed-but-unlicensed rule substitution barely exists** in a five-rule vocabulary
   (§10.5). The adversarial matrix is honest about which of its rows are typed rejections.
5. **If D1 is not eligible, the central invariant is only tested negatively** (§4.5). A
   `PASS` in that case must carry `absence: untested`.
6. **E5 is single-run and small-n by construction.** At most three specimens. No statistical
   claim of any kind is available, and none is made.
7. **E5 depends on E1 for inputs and on nothing else.** It does not depend on E1 *succeeding*
   (§4.3). If E1-v5 stops after adjudicating at least one D-specimen, E5 is runnable; if it
   stops before, E5 is blocked. Neither is an E5 result.

### 17.3 A null result is a result

`FAIL_SOUNDNESS`, `FAIL_DERIVATION_FEASIBILITY`, `FAIL_INDEPENDENCE`, `FAIL_FACT_MODEL`,
`INVALID_EXPECTED_CLAIM_INPUT` and `BLOCKED_NO_ELIGIBLE_E1_INPUT` are all preserved and
written up. Redesign after seeing a
result belongs to an `E5-v2` and a new preregistration document, never to an edit of this one.
