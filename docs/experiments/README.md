# Experiment roadmap

This fork is being used as a controlled research specimen, not as an attempt to maintain a production-complete EVM.

The goal is to exploit the repository's small, explicit execution model and existing `evm.json` corpus to run experiments that are hard to control in large production systems.

## Principles

1. **Independent tracks by default.** Each experiment should be implementable on its own branch with its own hypotheses, fixtures, measurements, and result document.
2. **Preregister before observing outcomes.** Freeze defect classes, inclusion criteria, measurements, and decision rules before running the experiment that they govern.
3. **Keep synthetic and real-world evidence separate.** A controlled injected-defect corpus gives causal clarity; mined real bugs give external validity. Neither substitutes for the other.
4. **Preserve negative results.** A failed hypothesis is a result, not an excuse to silently redesign the experiment.
5. **Do not silently grow into a modern zkEVM.** Scope expansion is allowed only when an experiment requires it. The fork should remain understandable enough that a reviewer can trace semantics end to end.

## Tracks

| ID | Track | Primary purpose | Dependency |
|---|---|---|---|
| E1 | [Boundary blind-spot corpus](./E1-boundary-blind-spots.md) | Test whether locally strong test/mutation evidence misses cross-component semantic defects | Independent |
| E2 | [MiniEVM → execution trace → Plonky3](./E2-plonky3-zkvm.md) | Build a small end-to-end verifiable-computation specimen | Independent |
| E3 | [Testing assurance vs formal constraints](./E3-testing-vs-proof.md) | Compare what tests/mutation and proof constraints detect or fail to detect | **Depends on frozen E1 and E2 artifacts** |
| E4 | [Outcome-fidelity fixture](./E4-outcome-fidelity.md) | Study loss of execution semantics while transporting outcomes into evidence/gates | Independent |

## Recommended branch layout

The experiment documents should be merged first. Implementation then proceeds in separate branches:

- `experiment/e1-boundary-blind-spots`
- `experiment/e2-plonky3-zkvm`
- `experiment/e4-outcome-fidelity`
- `experiment/e3-testing-vs-proof` only after E1 and E2 freeze their interfaces/results needed by E3

No experiment branch should depend on another experiment's worktree unless its document explicitly says so.

## Shared artifacts, not shared implementations

Experiments may exchange versioned artifacts through stable files rather than importing each other's implementation details. Candidate interchange formats:

- `artifacts/spec/opcodes-v1.json` — frozen MiniEVM opcode/semantic scope
- `artifacts/traces/*.jsonl` — execution traces
- `artifacts/faults/*.json` — injected-defect manifests
- `artifacts/results/<experiment-id>/...` — measurements and machine-readable results

The exact schemas should be frozen by the owning experiment before they become dependencies.

## Non-goals

- Ethereum mainnet conformance
- gas-accurate modern EVM implementation
- production zkEVM engineering
- replacing real-world bug mining with synthetic faults
- claiming that a valid proof means the modeled program/specification is correct

The interesting part is precisely the gap between those assurances.