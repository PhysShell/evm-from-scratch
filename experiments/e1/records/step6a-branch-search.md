# Step 6a record — E1-v5 domain realisation

Executes Step 2 §10 step 6a under [E1-v5](../../../docs/experiments/E1-v5-preregistration.md).

**This is E1-v5's first measured run.** Under §4.3 it is the moment the E1-v5 freeze becomes
final: the governing documents may no longer be revised, and a revision required after it
produces `E1-v6`.

**It ends in a stop, and the stop is about the procedure rather than about the specimen.**
`M1` was not written and no adjudicating figure was produced. See
[`E1-v5-STOP.md`](../../../docs/experiments/E1-v5-STOP.md) —
`STOP_PROTOCOL_ARM_ORDER_UNDERSPECIFIED`.

**Everything below §4 is an observation under the file order this implementation chose**, not
the uniquely determined §8.2.2 result. Frozen Step 2 orders arms "by source position" but
defines no total order BETWEEN files, and different admissible orders give different outcomes
— §7 sets that out.

## 1. Provenance

```text
freeze_merge_sha   f670258f1e7ef4cf6adbeddeac5a81f4cf981487   E1-v5 §4.1, all five clauses PASS
freeze_base_sha    8f5aaeda667b2fecd7963f53806811b24cc36607   PR #5, closed the stopped v4
manifest           manifest/M0-v5-protocol.json               replays clean, no measurement
inherited baseline 073074bc4aa2324457c8639a6f850fbc1f558ec3   clean Baseline B, not re-run
```

The permitted non-measurement integrity replay was run first: 329/329 green — 213 core, 49
level-A oracle, 65 level-B oracle, with their length guards. It produced no figure.

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

`tools/verify-arm-alignment.ts` performs it and the search refuses to run when it fails, so no
result here rests on an unestablished ordinal mapping.

## 4. The §8.2.2 search, under this implementation's file order

The files were iterated in the order the coverage extractor produced them, alphabetically by
repository-relative path: `call.ts -> dec.ts -> jmp.ts -> mem.ts -> opcodes.ts -> ret.ts ->
run.ts -> sto.ts`. §7 explains why that choice is result-bearing and why the outcome below is
therefore an observation rather than the frozen procedure's verdict.

```text
budget          B = 4096 candidates per arm
|D_program|     37, recomputed from §3.2-§3.7; digest and the sole-trailing-jumpdest
                property checked by M0-v5 under binding rule 5
records         per unit, from the §1.3 declared inputs typed by §2, enumerated in the
                §8.2.1 index-sum order
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
rather than a curiosity. `src/dec.ts:22` is also `code[pc] ?? 0`, and it got a witness at the
*first* candidate — because `decode` is called at a `pc` past the end when a `PUSH` immediate
is truncated, which is `SEM-DEC-3`, a frozen postcondition. Identical source, identical arm
type; reachable in one unit and dead in the other.

## 6. Why this is a stop and not a small fix

Step 2 §8.2.2 names the consequence exactly: stop the run, preserve the record, continue only
as a new preregistration. A hand-written fixture to close the gap is prohibited outright.

The procedure also, deliberately, does **not** decide reachability — "whether the arm was
*truly* unreachable or merely unreached within `B` is not decided, and does not need to be".
§5 above is an observation about the source, not a verdict the procedure delivered. The stop
would be identical either way.

## 7. The order is not frozen, and it decides the outcome

§8.2.2 iterates "in frozen source order"; §8.2 allocates `LT-BR-*` "in ascending order of
source position". Neither defines a total order **between files**, and the choice changes the
result in two concrete ways:

```text
§1.3 unit order        U-DEC and U-JMP both precede U-CALL, so the run would take dec.ts's
                       witness, reach jmp.ts and stop — and LT-BR-U-CALL-001 would never be
                       emitted. The realised prefix of the frozen ID allocation changes.

mem.ts before jmp.ts   U-MEM's operand domain contains 2²⁵⁶ − 1, which reaches an allocation
                       the host cannot make: E1-v5 §3.10's evaluation stop, at candidate 11.
                       The run ends with a preserved candidate index and error class instead
                       of NO_FROZEN_BRANCH_WITNESS.
```

Two admissible orders, three outcomes, and the frozen procedure selects none of them. It
cannot be repaired inside v5: step 6a was the first measured run, so adding a file-order rule
now would pick which of three known outcomes becomes the record.

## 8. What the §3.10 reading did, and did not, do here

An earlier execution of this same procedure — before the tool was corrected — surveyed every
arm instead of halting at the first exhausted one, and reached a `RangeError` in `U-MEM` at
candidate 11, which under E1-v5 §3.10 is an evaluation stop.

That run was wrong and its outcome is not this run's outcome. §8.2.2 halts at the **first** arm
that exhausts `B`, and `src/jmp.ts:17:27` precedes `src/mem.ts` in frozen source order, so the
correct stop is `NO_FROZEN_BRANCH_WITNESS`. The tool was corrected to halt where the frozen
text says to halt, and re-run.

It is recorded because it is evidence about the frozen procedure rather than about the tool:
**the §3.10 condition is reachable**, at a low candidate index, in a unit whose operand domain
contains `2²⁵⁶ − 1`. A later version reaching `U-MEM` before exhausting an earlier arm will
meet it, and §3.10 says what happens then — the run stops, the candidate index, arm and error
class are preserved, and no next candidate is tried.

## 9. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no
defect was injected, no calibration figure exists. `M1` does not exist, and §7 makes it a
precondition for any adjudicating figure.

**Clean Baseline B stands**, inherited and unmodified, carrying its recorded limitation: at
least 4 case IDs incompletely realise 2 frozen postconditions
([`v3-review-findings.md`](./v3-review-findings.md) §2).
