# Step 4 record — the 213 frozen core tests, in their expected red state

Executes Step 2 §10 step 4 under [E1-v3](../../../docs/experiments/E1-v3-preregistration.md).

**No level-B production unit was implemented.** That is step 5, and this commit is
deliberately the historical state *before* it: the same frozen tests must turn green there
without being edited, and that only means something if red and green are separate commits.

## Result

```text
frozen plan      213
executed         213
passed           166
failed            47
names match plan true
attributable     true
```

Verified by `tools/verify-plan.ts`, not by reading a summary line. The test titles are the
case IDs, compared as a set against `M0-v3-protocol.json`:

- **no frozen ID went unexecuted** and **no executed test is outside the plan**;
- the 166 passing are *exactly* the level-A set;
- the 47 failing are *exactly* the level-B set.

Set equality is the claim, not the counts. Two errors that cancel would keep 166/47 intact
while testing the wrong things.

## Every failure is attributable

Zero suites failed before executing a case. The 47 failures split by cause:

| | Count | Why |
|---|---|---|
| missing unit | 44 | `src/{mem,sto,grd,hlt,entry,call,ret}.ts` do not exist yet |
| assertion on an existing unit | 3 | `LT-SEM-RUN-4`, `LT-SEM-SEAM-C1`, `LT-SEM-SEAM-C2` — `U-RUN` exists but does not dispatch `GAS`, `ADDRESS` or `CALLER`, all level-B opcodes |

The 44 come from `loadUnit()` (see `test/support/units.ts`), which requires a module at
**test-execution** time rather than importing it statically. Written with a static `import`,
a missing module is a TypeScript resolution error: Jest refuses to run the file, and the
evidence reads *"test suite failed to compile"* — one red mark standing in for 44 cases whose
number and reasons a later auditor would have to take on trust. It costs nothing at step 5:
once the module exists, `loadUnit` returns it and the frozen test turns green untouched.

`loadUnit` supplies no behaviour. It converts a missing module into a legible failure and
does nothing else.

## One false green, caught and fixed

`LT-SEM-GRD-1` asserts that a static-flagged `SSTORE` throws. Written as

```ts
expect(() => grd().guardedSstore(…)).toThrow();
```

it **passed** in the red state — the `toThrow` was satisfied by `loadUnit`'s own
"unit not implemented" error, not by any guard. A case reporting green while its unit does
not exist is precisely the corruption this record is supposed to be evidence against.

Fixed by loading the unit outside the assertion, so a missing module throws before the
assertion is reached and fails the case:

```ts
const g = grd();
expect(() => g.guardedSstore(…)).toThrow();
```

This is the only `toThrow` among the level-B cases, so it is the only place the shape could
occur. Level-A cases are unaffected — their units exist.

## What the level-B tests commit step 5 to

Each level-B block declares the API shape it expects, in the test file rather than in `src/`,
so no production file was touched at this step. Those shapes are the contract step 5
implements:

```text
src/mem.ts     mstore / mload / msize          over an owned { bytes } memory
src/sto.ts     sstore / sload                  over an owned World, keyed by storage_owner
src/grd.ts     guardedSstore                   the static write guard
src/hlt.ts     halt / exceptionalHalt          RETURN / REVERT -> FrameResult
src/entry.ts   rootFrame(code, tx)             the entry-frame contract
src/call.ts    popOperands / executeCall       operands, and the seam with U-RUN substituted
src/ret.ts     applyResult / returndatasize / returndatacopy
```

`test/core/opcodes-b.ts` holds the level-B opcode bytes in the test tree for the same reason:
a test needs the byte to build a fixture, while the interpreter must still not know what to
do with it. Step 5 moves them into `src/opcodes.ts` and that file goes away.

## Provenance

```text
freeze_merge_sha      bd363066c9000867d54c81f60bdd0a5b9883e025
manifest              manifest/M0-v3-protocol.json
plan_core_digest      63b4d9f9e1b40a08d2bd3f862ce072fb036bc6401f4360823cc5bfc8d79aae02
```

The oracle suite is untouched and still green at 49/49; it is a separate domain and takes no
part in this count (Step 0 §3.2.1).

## Next

Step 5: implement the clean level-B semantics of §3 — no defects — until all 213 turn green
and the level-B oracle passes 65/65. The frozen tests may not be edited to achieve it.
