# Step 6a record — E1-v5 domain realisation

Executes Step 2 §10 step 6a under [E1-v5](../../../docs/experiments/E1-v5-preregistration.md).

**This is E1-v5's first measured run.** Under §4.3 it is the moment the E1-v5 freeze becomes
final: the governing documents may no longer be revised, and a revision required after it
produces `E1-v6`.

**It ends in a stop.** `M1` was not written and no adjudicating figure was produced. See
[`E1-v5-STOP.md`](../../../docs/experiments/E1-v5-STOP.md).

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

That creates a coordinate problem, and the honest fix is worth recording because two obvious
ones failed:

```text
positions differ   the search instruments TRANSPILED JavaScript, so its branchMap carries
                   generated-JS lines; jest reports TypeScript lines
attempt 1 FAILED   passing the source map to instrumentSync — istanbul stores the map for a
                   later remap rather than rewriting positions
attempt 2 FAILED   remapping the whole coverage map with istanbul-lib-source-maps, including
                   a counter-tagging trick to keep the arms distinguishable — positions did
                   not move
what works         ORDER corresponds exactly. Both are istanbul walking the same program, so
                   the k-th arm of a file is the same arm in both.
```

So arms are aligned by ordinal — and the alignment is **verified, not assumed**: the discovery
record stores each file's full arm-type sequence, and the search refuses to align a file whose
sequence disagrees. It reported `arm alignment verified for every file`.

## 4. The frozen §8.2.2 search

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

Then, at the third arm in frozen source order:

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

## 7. What the §3.10 reading did, and did not, do here

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

## 8. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no
defect was injected, no calibration figure exists. `M1` does not exist, and §7 makes it a
precondition for any adjudicating figure.

**Clean Baseline B stands**, inherited and unmodified, carrying its recorded limitation: at
least 4 case IDs incompletely realise 2 frozen postconditions
([`v3-review-findings.md`](./v3-review-findings.md) §2).
