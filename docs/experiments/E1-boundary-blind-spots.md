# E1 — Boundary blind-spot corpus

## Question

Can a defect at a semantic boundary survive strong local testing evidence on both sides of that boundary, including high coverage and mutation adequacy, yet fail under a composition-level witness?

This experiment uses a deliberately small EVM implementation as a controlled specimen. The objective is not to prove anything about all software systems. It is to create a corpus where the causal defect, boundary, trigger, and expected behavior are known before measurement.

## Why this repository

The EVM has compact but non-trivial boundaries: stack ↔ opcode semantics, caller ↔ callee context, memory ↔ return data, writable ↔ static execution, storage ↔ account context, normal ↔ exceptional termination. Those boundaries are rich enough to create realistic semantic defects without requiring a production-sized codebase.

## Core design

Start from a correct baseline implementation for a frozen subset of semantics. Inject one defect at a time from a preregistered defect catalog. For every defect, collect:

- affected semantic boundary;
- exact causal region;
- triggering witness;
- local tests on the producer/caller side;
- local tests on the consumer/callee side;
- line/branch coverage where meaningful;
- mutation results on both local regions;
- composition-level outcome;
- whether the defect is representable by ordinary mutation operators.

The unit of analysis is one injected defect instance, not one failing test and not one mutated line.

## Candidate defect classes

Freeze the final catalog before running the measured corpus. Initial candidates:

1. **Context propagation** — e.g. propagate the wrong `caller`, `value`, or writable/static flag across a call boundary.
2. **Missing semantic case** — a valid enum/opcode/state value is absent from a downstream mapping or dispatch table.
3. **State ownership** — read/write state from the caller account when callee-owned state is required, or vice versa.
4. **Copy/alias boundary** — returndata/memory or stack values are aliased when a copy is required, or copied when shared identity is required.
5. **Exceptional termination propagation** — nested failure is flattened into normal return or the wrong failure class.
6. **Composition-only validation** — each component accepts its local input but their combination violates a semantic invariant.
7. **Representation mismatch** — one layer encodes a semantic distinction that the next layer collapses or misinterprets.

## Good first seams

Prefer seams where both sides can plausibly have individually strong tests:

- `CALL` → callee execution context;
- `STATICCALL` → storage write prohibition;
- callee `RETURN`/`REVERT` → caller returndata;
- bytecode decoding → `JUMPDEST` validation;
- account/storage lookup → execution context;
- nested exceptional halt → caller-visible result.

## Hypotheses

Preregister exact statistical/decision rules before measurement. Conceptually:

- **H1:** there exist injected boundary defects for which both adjacent local regions have complete/near-complete exercised paths and no surviving ordinary mutants, while the composition witness still fails.
- **H2:** defects implemented as *absence* or *cross-boundary misbinding* will be underrepresented by mutation operators relative to ordinary local arithmetic/control-flow defects.
- **H3:** composition witnesses provide incremental detection value after conditioning on local test and mutation adequacy.

These are candidate hypotheses, not conclusions.

## Controls

Include at least two controls:

- **local defects:** conventional arithmetic/control-flow defects expected to be caught by local tests or mutation testing;
- **boundary defects with explicit local oracle:** defects whose semantic distinction is directly asserted locally, demonstrating that the harness can detect boundary errors when the oracle is present.

A corpus containing only hand-picked blind spots would be uselessly self-congratulatory.

## Measurements

Per defect instance:

- detected by local tests: yes/no;
- detected by composition witness: yes/no;
- mutation operator generated an equivalent/similar fault: yes/no;
- mutation score adjacent to the seam;
- line/branch coverage adjacent to the seam;
- defect class;
- semantic seam;
- number and type of local assertions that exercise the relevant value/path;
- whether the defect requires a value/state combination only observable after composition.

Do not collapse these into a single vanity score.

## Corpus generation discipline

Each injected defect gets a manifest containing, before measured execution:

```json
{
  "id": "E1-B03-001",
  "class": "context-propagation",
  "semantic_seam": "CALL -> callee context",
  "baseline_revision": "<sha>",
  "fault_patch": "<machine-readable or patch reference>",
  "expected_trigger": "<fixture id>",
  "expected_semantic_difference": "<precise statement>"
}
```

The manifest must not contain post-hoc claims about which testing technique did or did not detect it.

## Relationship to real-world mining

This experiment is a **controlled calibration corpus**, not a substitute for mined real-world defects. Its strongest contribution is causal clarity: we know the defect was injected, where it lives, and what should expose it.

A separate real-world corpus can then test whether the same classes occur outside the laboratory. Results from the two corpora should be reported separately before any combined interpretation.

## Exit criteria

E1 is complete when:

1. the defect taxonomy and inclusion rules are frozen;
2. a correct baseline exists for the chosen semantic subset;
3. the injected corpus is generated reproducibly;
4. local tests, coverage, mutation evidence, and composition witnesses run automatically;
5. raw machine-readable results are preserved;
6. interpretation is written without changing the preregistered classification rules.

A null result is acceptable. Redesign after seeing results belongs to E1-v2, not a rewrite of E1.