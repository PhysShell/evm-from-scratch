# E2 — MiniEVM → execution trace → Plonky3

## Question

Can a deliberately small EVM subset be turned into an end-to-end verifiable-computation specimen whose execution semantics remain understandable enough to inspect manually?

The purpose is educational and experimental: connect ordinary interpreter semantics to an execution trace and then to algebraic constraints/proofs without inheriting the complexity of a production zkEVM.

## Scope

Start with a frozen MiniEVM subset. Candidate first version:

- `STOP`
- `PUSH1..PUSH32`
- `POP`
- `ADD`, `SUB`, `MUL`
- `EQ`, `LT`
- `AND`, `OR`, `XOR`
- a small fixed subset of `DUP` and `SWAP`, or the families if cheap enough

Do **not** begin with calls, storage, gas, dynamic memory, Keccak, account state, or Ethereum fork compatibility.

The subset may grow only when an explicit experiment requires a new semantic boundary.

## Architecture

```text
program bytecode
      ↓
reference interpreter
      ↓
structured execution trace
      ↓
AIR / constraints
      ↓
Plonky3 prover
      ↓
proof
      ↓
verifier
```

The interpreter and constraint system must share a semantic specification, but should avoid sharing opaque implementation logic that could make the same bug appear in both implementations unnoticed.

## Trace model

Define an explicit row schema before implementing the AIR. A candidate row contains:

- step index;
- program counter;
- opcode;
- stack pointer;
- bounded stack cells or stack commitment representation;
- opcode operands/results needed by the transition;
- halt flag;
- error/validity flag if invalid programs are modeled.

The exact shape belongs in a versioned schema. The trace should be serializable independently of Plonky3 so that it can be inspected and replayed by other tools.

## Semantic invariants

For every supported opcode, state transitions must be stated independently of code. Example for `ADD`:

- consume two stack items;
- push one result;
- result is addition modulo `2^256`;
- advance `pc` by one byte for the opcode;
- preserve unrelated state.

For `PUSHn`:

- immediate bytes belong to the instruction, not future opcodes;
- `pc` advances by `1 + n`;
- the immediate is interpreted with the chosen EVM-compatible byte order;
- stack height increases by one.

The semantic document is the authority. Interpreter behavior and AIR are implementations of it.

## Key separation

The experiment should distinguish three artifacts:

1. **semantic specification** — what execution means;
2. **reference interpreter** — produces expected execution and traces;
3. **constraint system** — accepts exactly valid traces according to the modeled semantics.

If one file or function becomes the source of truth for all three, the experiment is so tightly coupled that independent falsification becomes decorative.

## Tests

At minimum:

- existing applicable `evm.json` cases for the selected opcodes;
- hand-written transition tests for each opcode;
- invalid trace tests where one field is modified after correct execution;
- property tests for arithmetic modulo `2^256`;
- trace determinism tests;
- proof verification succeeds for valid traces;
- proof verification fails for tampered public inputs and invalid traces.

## Public inputs

Freeze the first proof statement explicitly. Candidate statement:

> Given program bytes `P`, initial stack/input commitment `I`, and claimed final output `O`, there exists an execution trace satisfying the MiniEVM transition relation that starts from `I`, executes `P`, and ends at `O`.

Do not casually mix hidden/private inputs, Ethereum account state, or payment semantics into v1. Those are later experiments.

## Threats to validity

Document at least:

- the interpreter and AIR may share the same specification mistake;
- a valid proof establishes consistency with constraints, not correctness of the constraints;
- the MiniEVM subset is not representative of full EVM complexity;
- omitting dynamic memory/calls/storage removes many of the hardest zkVM engineering problems;
- proof-system soundness is inherited from Plonky3 assumptions and implementation, not established by this experiment.

## Deliverables

1. `minievm-spec-v1.md` with normative transition semantics;
2. a reference interpreter for the frozen subset;
3. a stable trace schema and serializer;
4. Plonky3 AIR/constraint implementation;
5. prover/verifier CLI or test harness;
6. valid and intentionally invalid fixtures;
7. benchmark data kept secondary to correctness;
8. a result note stating exactly what was and was not demonstrated.

## Exit criteria

E2 is complete when a fresh checkout can reproducibly:

1. execute a supported program;
2. emit a trace;
3. prove the trace satisfies the frozen MiniEVM semantics;
4. verify the proof from the declared public inputs;
5. reject preregistered trace corruptions;
6. reproduce all results without depending on E1, E3, or E4.

Performance optimization is explicitly post-experiment unless proof generation is so slow that the basic experiment cannot run.