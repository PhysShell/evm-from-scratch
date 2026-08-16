# E4 — Outcome-fidelity fixture

## Question

How much semantic information can be lost when VM execution outcomes are transported through logging, capture, serialization, replay, or gate-like evidence layers, and which losses change downstream acceptance decisions?

This experiment treats the VM as a producer of semantically distinct outcomes and studies the transport layer separately from execution correctness.

## Relationship to our projects

E4 is the controlled fixture for the **Qodec gate outcome-fidelity** line and its corresponding architecture work around capture, replay, artifact identity, validation, and acceptance decisions.

The production problem is not “does the VM execute correctly?” but “does an execution outcome retain the distinctions required by later evidence consumers after it crosses transport and replay boundaries?” E4 isolates that problem in a tiny system where the original semantic outcome is known exactly.

Project-level use is:

- **Qodec gate outcome fidelity:** controlled falsification fixture for semantic outcome → capture → stored artifact → replay → decision;
- **gate.rs / events.rs architecture work:** exercise failure-class preservation, artifact-kind identity, same-byte structural validation, replay validation, deduplication, and version interpretation without changing production schemas to make an experiment convenient;
- **OwnAudit evidence-binding work:** provide a small analogue for questions about whether recorded evidence still refers to and preserves the thing it claims to represent;
- **P-038 / E1:** adjacent but distinct. E1 injects defects in execution/composition semantics; E4 injects defects after the semantic outcome already exists, in the evidence path;
- **Own.NET:** no runtime dependency; any transfer is architectural evidence about representation and replay boundaries.

E4 must not claim that every information loss is a correctness defect. The experiment explicitly distinguishes **representation fidelity** from **decision fidelity** because a coarse representation can be sufficient for one declared consumer and insufficient for another. That distinction maps directly to the gate work: evidence has to preserve the semantics required by its acceptance contract, not every bit merely because it exists.

## Motivation

A VM can distinguish at least several termination/result classes even in a deliberately limited model:

- normal halt;
- return with bytes;
- explicit revert with bytes;
- exceptional halt;
- nested-call failure;
- invalid instruction / invalid jump, if included in scope.

A transport layer that records all of these as a single boolean such as `success=false` may preserve enough information for one consumer while destroying evidence required by another.

The target is not Ethereum compatibility. The target is a controlled model of **semantic outcome → captured evidence → replayed interpretation → decision**.

## Architecture

```text
VM execution
    ↓
semantic outcome
    ↓
capture/transport encoding
    ↓
stored artifact
    ↓
replay/parser
    ↓
downstream decision
```

Each layer gets an explicit schema and version. The semantic outcome is the reference; later representations are measured against it.

## Candidate outcome model

Freeze the exact model before running. A candidate representation:

```text
Outcome =
  Halt
  | Return(bytes)
  | Revert(bytes)
  | ExceptionalHalt(reason)
  | NestedFailure(call_depth, reason)
```

Do not add distinctions merely because they make a later result interesting.

## Fault classes

Inject faults in the evidence path, not the VM execution path:

1. **class collapse** — `Revert` and `ExceptionalHalt` become one generic failure;
2. **payload loss** — return/revert bytes are omitted or truncated;
3. **identity loss** — nested call identity/depth is lost;
4. **ordering loss** — multiple emitted events are replayed in the wrong order;
5. **dedup collision** — two semantically distinct artifacts deduplicate under an insufficient key;
6. **parser asymmetry** — writer preserves a distinction that replay ignores;
7. **validation bypass** — stored bytes are accepted without structural or semantic validation;
8. **version ambiguity** — the same bytes are interpreted under different schema assumptions.

## Decision fixtures

Define several downstream consumers with intentionally different information needs, for example:

- consumer A only needs success/failure;
- consumer B distinguishes revert from exceptional halt;
- consumer C requires exact return/revert bytes;
- consumer D requires nested failure provenance.

Then test whether a transport defect is harmless or decision-changing **for that declared consumer**.

This prevents the meaningless claim that every lost bit is automatically a correctness failure.

## Hypotheses

Candidate hypotheses to preregister:

- **H1:** coarse success/failure transport is insufficient for at least one realistic downstream decision even when it is sufficient for another.
- **H2:** deduplication keys that omit semantic artifact kind can erase validation/evidence distinctions.
- **H3:** replay-time validation detects some stored-artifact corruptions that write-time validation alone cannot protect against.
- **H4:** nested failures create more outcome-fidelity risk than single-frame execution because identity and provenance cross an additional boundary.

## Measurements

For every fixture:

- original semantic outcome;
- encoded artifact;
- replayed outcome;
- whether byte-level integrity is preserved;
- whether structural validity is preserved;
- whether semantic identity is preserved;
- downstream decision before transport fault;
- downstream decision after transport fault;
- fault class.

Separate **representation fidelity** from **decision fidelity**. A representation may lose information without changing a particular decision, and that distinction should remain visible.

## Independence

E4 should not require E1, E2, or E3. It may reuse a tiny VM runner, but its measured defect is always in the outcome/evidence path.

If later work wants to compare E4 with a production gate system, that is a separate external-validity exercise. Do not bake production assumptions into this controlled fixture.

## Exit criteria

E4 is complete when:

1. semantic outcome classes are frozen;
2. transport/replay schemas are versioned;
3. downstream decision fixtures are declared before fault injection results are inspected;
4. each transport fault is reproducible from a manifest;
5. representation- and decision-fidelity results are both recorded;
6. the experiment runs without depending on the zkVM or boundary-defect tracks.