# E3 — Testing assurance vs formal constraints

## Question

When the same small virtual machine is evaluated by ordinary tests/mutation analysis and by a formal execution-constraint system, which defect classes are detected by each, and which survive because the defect lies in the shared specification or semantic boundary?

This is deliberately a downstream experiment. It must not be implemented until E1 and E2 have frozen the artifacts that E3 consumes. Otherwise the comparison can be tuned after seeing results and becomes scientifically worthless with impressive-looking charts.

## Relationship to our projects

E3 is the explicit **bridge experiment between the OwnAudit / P-038 assurance work and the Plonky3 / verifiable-computation work**.

E1 asks whether strong local testing evidence can miss composition defects. E2 asks whether the same small computation can be constrained and proven. E3 asks the question that neither can answer alone: **what additional failure surface does each assurance mechanism cover, and where can they share the same blind spot?**

Project-level use is:

- **OwnAudit / P-038:** test whether the boundary/composition phenomenon survives when a second, formally constrained assurance mechanism is added;
- **Blind Spot Miner / leakmine:** provide defect-class labels that can later inform which mined fault families are plausible candidates for cross-technique blind spots;
- **Plonky3 / ZK research:** falsify the sloppy interpretation that a valid proof means the intended computation is correct, by separating implementation, constraint, specification, and boundary-model defects;
- **verifiable payment/calculation work:** establish what a proof can and cannot say before any payment rule is trusted merely because it verifies;
- **Own.NET/Qodec:** no production dependency; any relevance is methodological evidence about assurance boundaries, not a reason to embed the MiniEVM or prover into those systems.

The key research object is not a competition called “tests vs proofs.” It is the disagreement matrix. A proof-valid, specification-wrong case is as important as a test-green, constraint-invalid case.

## Dependencies

E3 consumes, without silently modifying:

- E1's frozen defect taxonomy and selected injected-defect corpus;
- E1's local/composition test evidence;
- E2's frozen MiniEVM semantic specification;
- E2's execution trace schema;
- E2's proof/constraint implementation.

Any change needed to E1 or E2 after E3 begins requires a new versioned experiment rather than retroactively changing the inputs.

## Core comparison

For each eligible defect instance, classify detection by:

1. local unit tests;
2. composition-level witnesses;
3. ordinary mutation testing / mutation representability;
4. trace validity checks;
5. proof generation / verification under the frozen constraint system.

The important result is the *pattern*, not a single winner.

Candidate detection matrix:

| Defect | Local tests | Composition witness | Mutation | Trace constraints | Proof |
|---|---:|---:|---:|---:|---:|
| D1 | pass/fail | pass/fail | caught/not represented/survived | accept/reject | verifies/rejects |

## Defect families of special interest

### A. Implementation bug, correct specification

The interpreter violates the normative semantics while the constraint system models them correctly.

Expected possibility: tests may miss the bug while the generated trace becomes invalid under the constraints.

### B. Constraint implementation bug, correct specification

The interpreter follows the semantics but AIR/constraints omit or misencode a rule.

Expected possibility: ordinary execution tests remain green while an invalid trace can obtain a proof.

### C. Shared specification bug

Interpreter and AIR both faithfully implement an incorrect normative rule.

Expected possibility: tests and proofs all agree on the wrong behavior. This is the most important antidote to the sloppy claim that "the computation is proven correct."

### D. Boundary-model bug

Each local transition is individually valid, but the interface between two semantic regions loses, aliases, or misbinds information.

This is the direct bridge to the boundary blind-spot work.

## Hypotheses

Freeze precise decision rules before running. Candidate hypotheses:

- **H1:** trace constraints detect some implementation defects that survive local tests and ordinary mutation testing.
- **H2:** proof validity provides no protection against defects encoded identically in the semantic specification and the constraint system.
- **H3:** boundary/composition witnesses remain necessary even when individual transition relations are formally constrained, unless the boundary invariant itself is represented in the constraints.
- **H4:** mutation representability differs systematically between local syntactic faults and cross-boundary semantic misbindings.

## Independence safeguards

Where practical:

- use separate code paths for interpreter execution and constraint evaluation;
- generate some invalid traces by an external corruption tool rather than by the prover implementation;
- keep semantic fixtures declarative;
- have E3 read E1/E2 artifacts by versioned format rather than linking directly to their internal functions;
- record exact source revisions for all inputs.

## Negative controls

Include defects that should be caught trivially by all relevant techniques. If every interesting method only gets difficult hand-picked cases while controls are absent, the experiment is rigged by construction.

Also include semantically equivalent mutations or non-observable implementation changes so that "detection" is not conflated with arbitrary code difference.

## Results

Report at least:

- per-defect detection matrix;
- counts by preregistered defect class;
- disagreements between assurance mechanisms;
- mutation representability rate by defect class;
- examples of proof-valid but specification-wrong behavior;
- examples of test-green but constraint-invalid behavior, if observed;
- confidence/uncertainty appropriate to corpus size.

Do not market the result as a universal ranking of testing vs formal verification. The useful claim is narrower: under the frozen MiniEVM corpus, different assurance mechanisms cover different failure surfaces.

## Exit criteria

E3 is complete when:

1. all consumed E1/E2 revisions are pinned before measurement;
2. detection rules are frozen;
3. the full comparison runs reproducibly;
4. raw per-defect results are retained;
5. interpretation distinguishes implementation, specification, constraint, and boundary-model defects;
6. no E1/E2 rule is rewritten to make the E3 result cleaner.