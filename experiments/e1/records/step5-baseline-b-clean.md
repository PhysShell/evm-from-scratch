# Step 5 record — clean Baseline B, all 213 green

Executes Step 2 §10 step 5 under [E1-v3](../../../docs/experiments/E1-v3-preregistration.md).

**No defect from the Step 0 §6 catalog is present.** D1–D4, C1a/C1b and C2 arrive at step 8,
on their own revisions. This is the clean baseline the whole comparison is measured against.

## The four invariants

### 1. The frozen tests were not touched

```text
git diff 2964098 -- test/core/ test/support/     (empty)
```

Byte-identical to the red commit. The red → green transition is a transformation of
**production code alone**, which is the only thing that makes the transition evidence rather
than decoration.

### 2. All 213 green, verified as a partition

```text
frozen plan       213   (level A 166, level B 47, derived from Step 2 §3 + E1-v2/A1)
executed          213
passed            213
failed              0
names match plan  true
each executed 1×  true
attributable      true
all green         true
```

Run through `verify-plan.ts` **without** `--expect-red`, which switches the tool to requiring
every case green rather than the level partition. The other checks — no missing or extra IDs,
no duplicate execution, no status outside passed/failed — apply in both modes.

### 3. Both oracle slices green

```text
level A   49/49   (50/50 with its length guard)
level B   65/65   (66/66 with its length guard)
```

The level-B oracle is the 71 in-subset cases less the 6 composition witnesses, which stay
excluded so that "baseline correct" and "defect detected" are never the same measurement.

**Turning green does not promote the oracle.** It answers "is the baseline correct" and
nothing else; Step 0 §3.2.1 bars it from producing coverage, mutation or local-detection
evidence, and a suite acquires no new powers by passing.

### 4. Freeze provenance still holds

`manifest-replay` passes in full, including the E1-v3 §3.1 identity predicate and the
ordering check against the current `HEAD`.

## What was implemented

```text
src/mem.ts     mstore / mload / msize / mslice / mwrite
src/sto.ts     sstore / sload, keyed by storage_owner — never by address
src/grd.ts     guardedSstore — the static write guard
src/hlt.ts     halt / exceptionalHalt
src/entry.ts   rootFrame(code, tx)
src/call.ts    popOperands / executeCall — CONTAINS THE SEAM
src/ret.ts     applyResult / returndatasize / returndatacopy
src/run.ts     level-B dispatch; execute(frame, world) alongside run()
src/opcodes.ts level-B opcode constants
src/domain.ts  World, Account, TxContext, Memory
```

Two decisions worth naming, because both are the seam's shape rather than convenience:

**Frame construction is internal to `U-CALL`.** `calleeFrame` is not exported. Exporting it
would put the constructed frame inside the declared local interface and change what the
projection hides — the load-bearing decomposition choice of Step 2 §1.2, and the reason
D1–D3 are predicted to be invisible locally.

**`U-GRD` reads `frame.static`; it does not decide it.** Choosing the value is the producing
side's job (`SEM-SEAM-P3/P7/P11`), one unit upstream and behind the substitution. Keeping the
two apart is exactly why D1 can remove the propagation while the guard stays correct and
locally verified.

## `test/core/opcodes-b.ts` was kept

The step-4 record said this helper "goes away" at step 5. It does not. Removing it would mean
editing frozen test imports, and no wording in a record is worth breaking the red → green
chain. Production has its own constants in `src/opcodes.ts`; the test tree keeps its copy.
The duplication is deliberate and both files say so.

## One implementation defect, found by the oracle and not by the local suite

The level-B oracle failed twice on first run — `#94 MSIZE (0x20)` and `#95 MSIZE (0x60)` —
because `mload` read memory without expanding it, so `MSIZE` reported 0 where 32 and 96 were
expected. `SEM-MEM-3` says MSIZE is the highest **touched** offset, and a read touches;
upstream's own hint on #94 states it outright: *"the first 32-byte section has been
accessed"*. So this was a defect against the frozen semantics, not a gap in it, and it was
fixed in `mload` and in `U-RUN`'s `MLOAD` case, which had been discarding the expanded holder.

Worth recording plainly: **`LT-SEM-MEM-3` was green throughout.** The frozen local case checks
an empty memory and one after `mstore`; nothing in it exercises expansion by reading. The
oracle caught what the local suite did not.

This is *not* a result about boundary blindness and must not be read as one. It is an
ordinary single-unit defect, in `U-MEM`, with no seam involved — the opposite of the class
E1 studies. Its interest is narrower and worth stating anyway: the local suite is derived from
a frozen postcondition list, and a postcondition can be locally satisfiable by cases that miss
a consequence the composition-level corpus pins down. The 213 are complete with respect to the
plan, not with respect to every fact about the implementation.

## Two of the 213 are weaker than their postconditions

External review after this record was written found that `LT-SEM-CALL-5` is **vacuous** — its
closing assertion compares a length against the constant the test just built it from — and
that `LT-SEM-STO-4` performs no halt, so the one postcondition motivating the rollback
amputation has no local witness. Both are frozen and stay unedited; see
[`v3-review-findings.md`](./v3-review-findings.md) §2 for the verification and for what it
does to the claim above.

"213/213 green" stands and was always a count rather than a strength claim. It now overstates
the suite by one unfalsifiable case, and by two against the postcondition list.

## Provenance

```text
freeze_merge_sha   bd363066c9000867d54c81f60bdd0a5b9883e025
manifest           manifest/M0-v3-protocol.json
red state          2964098 (frozen tests) / 20d87be (verifier)
```

## Next

Step 6a: domain realisation — a non-adjudicating discovery run to enumerate `LT-BR-*` by the
frozen §8.2.2 search, freeze both final domains, run the §9.1 set-difference check, and append
the M1 clean-baseline record. No adjudicating figure may be produced before M1 exists.
