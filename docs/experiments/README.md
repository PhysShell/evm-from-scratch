# Experiment roadmap

This fork is being used as a controlled research specimen, not as an attempt to maintain a production-complete EVM.

The goal is to exploit the repository's small, explicit execution model and existing `evm.json` corpus to run experiments that are hard to control in large production systems.

## How this maps to our projects

The fork is not a new standalone product. It is a shared laboratory for several existing research lines.

| Experiment | Primary project connection | Secondary connection | What it contributes |
|---|---|---|---|
| **E1** | **OwnAudit / P-038** | Blind Spot Miner / leakmine, Own.NET | Controlled boundary-defect corpus with known causal seam, trigger, and ground truth; calibration for real-world boundary-blindness evidence |
| **E2** | **Plonky3 / verifiable computation** | Noir, Cairo, payment/calculation verification | Small end-to-end `program -> trace -> constraints -> proof -> verifier` specimen |
| **E3** | **OwnAudit assurance research × Plonky3** | P-038, Blind Spot Miner, verifiable calculations | Detection matrix comparing local tests, composition witnesses, mutation analysis, trace constraints, and proofs |
| **E4** | **Qodec gate outcome fidelity** | OwnAudit evidence binding, gate.rs/events.rs work | Controlled fixture for semantic outcome -> capture -> stored artifact -> replay -> acceptance decision |

The relationships are deliberately asymmetric:

- E1 does not replace P-038. E1 supplies causal calibration; P-038 supplies externally grounded evidence from real software seams.
- E2 does not imply that payment/business rules are correct merely because a proof verifies. It establishes the proving mechanism before business semantics are introduced.
- E3 is downstream of frozen E1/E2 artifacts and exists specifically to expose disagreements and shared blind spots between assurance mechanisms.
- E4 is not an EVM correctness experiment. Its defect surface begins after a semantic execution outcome already exists, in the evidence/transport/replay path.

Nothing in this fork should become an Own.NET or Qodec production dependency merely because an experiment proved useful. Transfer conclusions and patterns, not accidental laboratory architecture.

## Principles

1. **Independent tracks by default.** Each experiment should be implementable on its own branch with its own hypotheses, fixtures, measurements, and result document.
2. **Preregister before observing outcomes.** Freeze defect classes, inclusion criteria, measurements, and decision rules before running the experiment that they govern.
3. **Keep synthetic and real-world evidence separate.** A controlled injected-defect corpus gives causal clarity; mined real bugs give external validity. Neither substitutes for the other.
4. **Preserve negative results.** A failed hypothesis is a result, not an excuse to silently redesign the experiment.
5. **Do not silently grow into a modern zkEVM.** Scope expansion is allowed only when an experiment requires it. The fork should remain understandable enough that a reviewer can trace semantics end to end.

## Tracks

| ID | Track | Primary purpose | Dependency |
|---|---|---|---|
| E1 | [Boundary blind-spot corpus](./E1-boundary-blind-spots.md) · [Step 0 preregistration](./E1-step0-preregistration.md) · [Step 2 semantics & plan](./E1-step2-semantics-and-plan.md) · [v1 STOP](./E1-v1-STOP.md) · [v2 preregistration](./E1-v2-preregistration.md) · [v2 STOP](./E1-v2-STOP.md) · [v3 preregistration](./E1-v3-preregistration.md) · [v3 STOP](./E1-v3-STOP.md) · [v4 preregistration — never frozen](./E1-v4-preregistration.md) · [v4 STOP](./E1-v4-STOP.md) · [v5 preregistration](./E1-v5-preregistration.md) · [v5 STOP — `STOP_PROTOCOL_POSTFREEZE_CHAIN_NONCONFORMANT`](./E1-v5-STOP.md) | Test whether locally strong test/mutation evidence misses cross-component semantic defects | Independent |
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