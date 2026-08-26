# Step 6a record — E1-v5 domain realisation

Executes Step 2 §10 step 6a under [E1-v5](../../../docs/experiments/E1-v5-preregistration.md).

**This is E1-v5's first measured run.** Under §4.3 it is the moment the E1-v5 freeze becomes
final: the governing documents may no longer be revised, and a revision required after it
produces `E1-v6`. That remains true — the freeze is valid and was finalised here.

> ## THE FIGURES IN THIS RECORD ARE NON-ADMISSIBLE PROTOCOL EVIDENCE
>
> E1-v5's outcome is **`STOP_PROTOCOL_POSTFREEZE_CHAIN_NONCONFORMANT`**: everything the
> protocol built after the freeze is nonconformant — the `M0`/replay binding, the `D_program`
> artefact this run consumed, and this execution itself.
>
> This record covers the last of those three, preserved under the subordinate code
> **`STOP_PROTOCOL_STEP6A_NONCONFORMANT`** (§8), which in turn contains the independent
> specification defect **`STOP_PROTOCOL_ARM_ORDER_UNDERSPECIFIED`** (§7). The defects
> *above* this run in the chain — `D_program` violating frozen §3.4, and the M0/replay binding's
> self-supplied version selector, skippable mandatory rule-5 block and under-strength structural
> check — are recorded in
> [`E1-v5-STOP.md`](../../../docs/experiments/E1-v5-STOP.md) §3–§4. **They mean this run's
> inputs were already nonconformant before it started.**
>
> Everything below is a **historical observation of one tool in one environment**. No
> `LT-BR-*` ID here is allocated, no candidate index here is a frozen index, and the first stop
> here is not the frozen procedure's first stop.

`M1` was not written and no adjudicating figure was produced.

## 1. Provenance

```text
freeze_merge_sha   f670258f1e7ef4cf6adbeddeac5a81f4cf981487   E1-v5 §4.1, all five clauses PASS
freeze_base_sha    8f5aaeda667b2fecd7963f53806811b24cc36607   PR #5, closed the stopped v4
manifest           manifest/M0-v5-protocol.json               replays clean, no measurement
inherited baseline 073074bc4aa2324457c8639a6f850fbc1f558ec3   clean Baseline B, not re-run
```

The permitted non-measurement integrity replay was run first: 329/329 green — 213 core, 49
level-A oracle, 65 level-B oracle, with their length guards. It produced no figure.

**The manifest replay's PASS is not evidence that the inputs were conformant.** It recomputes
`D_program` by calling the same generator that produced the recorded digest, so it establishes
that `M0` and that generator agree with each other — not that the generator implements frozen
§3.2–§3.7, which it does not (`E1-v5-STOP.md` §4). Its toolchain set also does not cover the
instrumentation, see §8.4. None of this is repaired here.

## 2. Discovery coverage — the 213 core tests, and nothing else

```text
suites   7        test/core only
tests    213/213  green
excluded oracle-a, oracle-b, the composition witnesses, c2_control_suite
```

The exclusion is Step 0 §3.2.1: local evidence is confined to the frozen local suite, and a
branch covered by the oracle is not a branch covered locally.

**Its coverage figures are discovery output.** They locate uncovered arms and may never be
cited as baseline adequacy or as §5.3 condition-3 evidence. §10 splits 6a from 6b precisely so
that this cannot happen by accident, and a stop at 6a is not an occasion to start quoting them.

It found **45 uncovered arms** across 8 files, recorded with their per-file ordinals in
[`step6a-uncovered-arms.json`](./step6a-uncovered-arms.json).

## 3. How an arm is identified, and why that needed solving

The search must answer "does *this* candidate cover *that* arm", one candidate at a time,
which jest's whole-suite coverage cannot do. `tools/instrumented.ts` therefore loads the
production modules through `istanbul-lib-instrument` in memory — production code is not
modified.

That creates a coordinate problem, recorded with its dead ends because they cost real time:

```text
positions differ   the search instruments TRANSPILED JavaScript, so its branchMap carries
                   generated-JS lines; jest reports TypeScript lines
attempt 1 FAILED   passing the map to instrumentSync — istanbul stores it in the coverage
                   object for a later remap rather than rewriting branchMap positions
attempt 2 FAILED   remapping the whole coverage map with istanbul-lib-source-maps, including
                   a counter-tagging trick to keep arms distinguishable — positions did not
                   move
what works         mapping each arm's own position through the transpiler's source map
                   directly, with SourceMapConsumer
```

Arms are therefore targeted by ordinal, and establishing that the ordinal means the same thing
on both sides took two attempts of its own — the first rejected in review:

```text
REJECTED     comparing per-file sequences of istanbul `type` strings. A permutation among
             adjacent same-typed arms passes it unchanged, and src/jmp.ts alone opens
             `binary-expr, binary-expr, if, if`. Re-running the search does not test it,
             since the rerun goes through the same matcher.

ESTABLISHED  each arm's own generated-JS position mapped back through the transpiler's
             source map and compared with the TypeScript position the discovery run
             recorded for that ordinal:
                 103  matched by source position
                  20  positionless implicit-else arms, each identified by a sibling that
                      matched positionally
                   0  disagreements
```

`tools/verify-arm-alignment.ts` performs it and the search refuses to run when it fails.

**What this establishes under the disposition:** an internal correspondence within a
nonconformant run, under instrumentation versions `M0` never bound (§8.4). It is not
independent protocol evidence.

## 4. What the tool reported, and under what status

The files were iterated in the order the coverage extractor produced them, alphabetically by
repository-relative path: `call.ts -> dec.ts -> jmp.ts -> mem.ts -> opcodes.ts -> ret.ts ->
run.ts -> sto.ts`.

```text
budget          B = 4096 candidates per arm
|D_program|     37 members, as built. M0-v5 checked the digest under binding rule 5, but by
                calling the SAME generator — self-agreement, not conformance to §3.2-§3.7.
                The generator violates §3.4 (`E1-v5-STOP.md` §4), so these candidates came
                from a domain that is not the frozen one. The replay's structural boolean
                does not establish the member-role distinction it appears to: 35 generated
                p(j,t) members carry one trailing JUMPDEST; ε and p_trunc are anchorless
                (`E1-v5-STOP.md` §3.2). The digest itself is not a reproducible commitment
                either: rule 5 froze no hash algorithm and no canonical serialization, so
                the recorded value holds only under the encoding the verifier chose after
                the freeze (`E1-v5-STOP.md` §3.4).
records         per unit, from the §1.3 declared inputs typed by §2, enumerated in the
                §8.2.1 index-sum order — EXCEPT where §8 records that they were not
```

Two witnesses were emitted before the stop:

```text
LT-BR-U-CALL-001   src/call.ts:44:42 binary-expr#1
    candidate 796  kind=CALL code=ε stack_depth=17 memory=bytes[0] address=0x0
                   caller=0x0 static=false storage_owner=0x0 returndata=bytes[0]
                   world_shape=W0 world_code=ε

LT-BR-U-DEC-001    src/dec.ts:22:25 binary-expr#1
    candidate 1    code=ε pc=0
```

Then, at the third file in this order:

```text
NO_FROZEN_BRANCH_WITNESS   src/jmp.ts:17:27 binary-expr#1   B = 4096
```

**None of these three lines is a §8.2.2 result.** The IDs are not allocated, the indices are
not frozen indices, and the stop is not the frozen procedure's stop. **No ID is selectively
salvaged**: reconstructing the frozen stream happens to place the U-CALL fixture inside the
budget too (§8.1), and that is not a reason to keep `LT-BR-U-CALL-001`.

## 5. What that arm is

```ts
export function jumpdests(code: Uint8Array): Set<number> {
  const dests = new Set<number>();
  let pc = 0;
  while (pc < code.length) {
    const op = code[pc] ?? 0;          // <- arm #1 is the `?? 0`
```

The arm executes only when `code[pc]` is `undefined`, and the loop condition `pc < code.length`
guarantees it is not. **The arm is unreachable**, and no candidate from any domain can cover
it. It exists because `noUncheckedIndexedAccess` types `code[pc]` as possibly-undefined, so the
fallback is written to satisfy the type checker rather than to describe a state the program can
be in.

**The same idiom one file away is genuinely reachable**, which is what makes this a finding
rather than a curiosity. `src/dec.ts:22` is also `code[pc] ?? 0`, and `decode` is called at a
`pc` past the end when a `PUSH` immediate is truncated, which is `SEM-DEC-3`, a frozen
postcondition. Identical source, identical arm type; reachable in one unit and dead in the
other.

This is readable from the source without running anything, so it survives the disposition. It
is an observation about the source, **not** a verdict the procedure delivered — §8.2.2 does not
decide reachability, and "whether the arm was *truly* unreachable or merely unreached within
`B` is not decided, and does not need to be".

## 6. Why this is a stop and not a small fix

Step 2 §8.2.2 names the consequence of an unwitnessed arm exactly: stop the run, preserve the
record, continue only as a new preregistration. A hand-written fixture to close the gap is
prohibited outright.

The disposition goes further than that clause, because two independent defects were found
before this record could be accepted, and neither is repairable in v5 after measurement.

## 7. Reason one — the order is not frozen, and it decides the outcome

§8.2.2 iterates "in frozen source order"; §8.2 allocates `LT-BR-*` "in ascending order of
source position". Neither defines a total order **between files**. Three concrete admissible
orders are under discussion, and they give three distinct results:

```text
executed alphabetical   what §4 reports: two witnesses, then jmp.ts exhausts B.

§1.3 unit order         U-DEC and U-JMP both precede U-CALL, so the run would take dec.ts's
                        witness, reach jmp.ts and stop — and LT-BR-U-CALL-001 would never be
                        emitted. The realised prefix of the ID allocation changes.

mem.ts before jmp.ts    U-MEM's operand domain contains 2²⁵⁶ − 1, which reaches an allocation
                        the host cannot make: E1-v5 §3.10's evaluation stop, at candidate 11.
                        The run ends with a preserved candidate index and error class instead
                        of NO_FROZEN_BRANCH_WITNESS.
```

Three admissible orders, three outcomes, and the frozen procedure selects none of them. It
cannot be repaired inside v5: step 6a was the first measured run, so adding a file-order rule
now would pick which of three known outcomes becomes the record.

This finding is preserved under its own name, `STOP_PROTOCOL_ARM_ORDER_UNDERSPECIFIED`, as an
independent cause — not as the whole disposition.

## 8. Reason two — the tool did not implement the generator that *was* defined

Four instances, each verified against the frozen text and by execution.

### 8.1 `Frame.pc` omitted

§8.2.1 says "`Frame.pc` from `uint256`" and, arguing for index-sum ordering, "`Frame` has nine
fields". `src/domain.ts` carries `Declaration order is the §8.2.1 enumeration order`, with `pc`
second of nine. `tools/branch-search.ts` has an eight-entry `FRAME_FIELDS` and hard-codes
`pc: 0`, so `U-RUN`, `U-CALL`, `U-STO`, `U-GRD`, `U-HLT` and `U-RET` all enumerated a stream
that is not the frozen one. Replaying both, for the §4 U-CALL fixture:

```text
index under the executed stream (pc omitted)      796
index under the reconstructed frozen stream       886
```

### 8.2 `U-HLT` invents an input dimension

Frozen §1.3 declares `U-HLT`'s inputs as `frame, offset, len`. The tool adds a `halt` field, so
that stream is not the frozen one either. The field is also self-inconsistent — `exercise`
passes `RETURN`/`REVERT` while `describe` reports `NORMAL`/`EXCEPTIONAL` — but relabelling it
would only make the report honest about a stream that is still wrong. (`U-RET`'s `halt` is
legitimate: §1.3 gives it `frame, a FrameResult`.)

### 8.3 The byte domain became runtime state

`src/mem.ts` `ensure()` returns early when the buffer already covers the write, and `mstore`
then writes into that same buffer; `D_BYTES[2]` is exactly one word. The `U-MEM` record hands
the domain member in directly, and `frameFrom` does the same for `memory` and `returndata`:

```text
bytes[2] before   66,66,66,66,66,66,66,66 …
bytes[2] after    0,0,0,0,0,0,0,0 …
same object       true
```

One candidate destroys a frozen domain member for every later candidate and arm in the process.
Enumeration became history-dependent.

### 8.4 Instrumentation provenance not bound

`istanbul-lib-instrument` (6.0.3) and `source-map` (0.7.6) are transitive only — absent from
`package.json` and from `M0-v5`'s `toolchain` set — yet they fix arm enumeration order and arm
positions, and therefore every ordinal in §3 and §4. The lockfile preserves what happened *ex
post*, but `manifest-replay` checks only names present in `m0.toolchain`, so those versions were
never constrained by `M0` and replay would stay green across a change.

### 8.5 A tooling gap can print as a verdict — recorded, not repaired

A missing `UnitRecord` and a missing instrumentation entry both fall through toward
`unwitnessed`, which prints under the `NO_FROZEN_BRANCH_WITNESS — Step 2 §8.2.2` heading. Both
branches are unreachable in this run, so nothing above changes because of it. It is recorded as
a known defect; `E1-v6` must fail closed instead.

## 9. What the earlier `RangeError` observation does and does not establish

An earlier execution of this procedure — before the tool was corrected to halt at the first
exhausted arm — surveyed every arm instead, and reached a `RangeError` in `U-MEM` at candidate
11, which under E1-v5 §3.10 is an evaluation stop.

That run surveyed instead of halting, which §8.2.2 does not permit; the tool was corrected. It
was **not** wrong about which stop is correct, because no frozen text makes either stop correct
— §7 above is the whole point.

What the observation shows is that the §3.10 condition is **reachable**, at candidate 11, in a
unit whose operand domain contains `2²⁵⁶ − 1`. It is not a theoretical clause. Like everything
else here it is an observation of this tool in this environment, not a §8.2.2 result.

## 10. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no
defect was injected, no calibration figure exists. `M1` does not exist, and **E1-v5 §7** — the
preregistration's sequence, not §7 of this record — makes it a precondition for any adjudicating
figure.

**Amendment `A2` is neither validated nor falsified here.** It remains frozen and untouched, and
no defect is about it — but its support may not be drawn from this run. The two witnesses are
non-admissible, and binding rule 5's replay is not a substitute: it establishes only that `M0`
and the generator agree with each other, while the generator itself violates §3.4. **A2's
post-freeze implementation binding did not happen** (`E1-v5-STOP.md` §3.2, §4).

**Clean Baseline B stands**, inherited and unmodified, carrying its recorded limitation: at
least 4 case IDs incompletely realise 2 frozen postconditions
([`v3-review-findings.md`](./v3-review-findings.md) §2). Every defect in §8 is in the search
tooling; none is in `src/`.
