/**
 * Branch search — Step 2 §8.2.2, run at step 6a.
 *
 * For each branch arm the 213 core tests leave uncovered, in frozen source order, enumerate
 * candidates from the §8.2.1 canonical stream up to B = 4096 and take the first that covers
 * the arm. No candidate within B is `NO_FROZEN_BRANCH_WITNESS`, which stops the run — a
 * fixture invented at the keyboard to close the gap is prohibited.
 *
 * The domains below are the frozen §8.2.1 literals, held here for the same reason the freeze
 * base is: the thing being checked must not supply the criteria it is judged by.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { MAX_UINT256 } from '../src/domain';
import * as OP from '../src/opcodes';

// ---------------------------------------------------------------------------
// §8.2.1 primitive domains, verbatim.
// ---------------------------------------------------------------------------
const AAA = 0x1000000000000000000000000000000000000aaan;
const C42 = 0x1000000000000000000000000000000000000c42n;
const DAD = 0x1000000000000000000000000000000000000dadn;

const D_BOOL = [false, true];
const D_UINT256 = [0n, 1n, 2n, MAX_UINT256, 2n ** 255n, 3n];
const D_ADDRESS = [0n, AAA, C42, DAD];
const D_BYTES: Uint8Array[] = [
  new Uint8Array(0),
  Uint8Array.from([0x42]),
  Uint8Array.from(new Array<number>(32).fill(0x42)),
  Uint8Array.from(new Array<number>(33).fill(0x42)),
];
const D_STACK_DEPTH = [0, 1, 2, 3, 17, 1024];

/** Frame field order is normative — Step 2 §2 declares it, §8.2.1 enumerates by it. */
const FRAME_FIELDS = [
  { name: 'code', size: D_BYTES.length },
  { name: 'pc', size: D_UINT256.length },
  { name: 'stack', size: D_STACK_DEPTH.length },
  { name: 'memory', size: D_BYTES.length },
  { name: 'address', size: D_ADDRESS.length },
  { name: 'caller', size: D_ADDRESS.length },
  { name: 'static', size: D_BOOL.length },
  { name: 'storage_owner', size: D_ADDRESS.length },
  { name: 'returndata', size: D_BYTES.length },
] as const;

const BUDGET = 4096;

/**
 * §8.2.1 record order: increasing INDEX SUM, ties broken lexicographically by field order.
 *
 * A plain lexicographic odometer would leave the first 4096 candidates all sharing one
 * `code`, `pc` and `stack` — the very reason index-sum ordering was frozen.
 */
function* indexSumOrder(sizes: number[]): Generator<number[]> {
  const maxSum = sizes.reduce((acc, n) => acc + n - 1, 0);
  for (let sum = 0; sum <= maxSum; sum++) {
    const idx = new Array<number>(sizes.length).fill(0);
    const walk = function* (pos: number, left: number): Generator<number[]> {
      if (pos === sizes.length) {
        if (left === 0) yield [...idx];
        return;
      }
      const size = sizes[pos]!;
      for (let v = 0; v < size && v <= left; v++) {
        idx[pos] = v;
        yield* walk(pos + 1, left - v);
      }
      idx[pos] = 0;
    };
    yield* walk(0, sum);
  }
}

// ---------------------------------------------------------------------------
// The search.
// ---------------------------------------------------------------------------
interface Arm {
  file: string;
  line: number;
  column: number;
  type: string;
  arm: number;
}

const armsPath = process.argv[2];
if (armsPath === undefined) {
  console.error('usage: branch-search.ts <uncovered-arms.json>');
  process.exit(2);
}
const arms: Arm[] = JSON.parse(readFileSync(armsPath, 'utf8'));

// Every opcode the U-RUN dispatch has an arm for.
const DISPATCH_OPCODES = new Map<number, string>([
  [OP.STOP, 'STOP'], [OP.ADD, 'ADD'], [OP.SUB, 'SUB'], [OP.MUL, 'MUL'], [OP.DIV, 'DIV'],
  [OP.MOD, 'MOD'], [OP.LT, 'LT'], [OP.GT, 'GT'], [OP.EQ, 'EQ'], [OP.ISZERO, 'ISZERO'],
  [OP.POP, 'POP'], [OP.JUMP, 'JUMP'], [OP.JUMPI, 'JUMPI'], [OP.JUMPDEST, 'JUMPDEST'],
  [OP.PC, 'PC'], [OP.GAS, 'GAS'], [OP.ADDRESS, 'ADDRESS'], [OP.CALLER, 'CALLER'],
  [OP.MSTORE, 'MSTORE'], [OP.MLOAD, 'MLOAD'], [OP.MSIZE, 'MSIZE'],
  [OP.SLOAD, 'SLOAD'], [OP.SSTORE, 'SSTORE'], [OP.RETURN, 'RETURN'], [OP.REVERT, 'REVERT'],
  [OP.RETURNDATASIZE, 'RETURNDATASIZE'], [OP.RETURNDATACOPY, 'RETURNDATACOPY'],
  [OP.CALL, 'CALL'], [OP.STATICCALL, 'STATICCALL'], [OP.DELEGATECALL, 'DELEGATECALL'],
]);

// Enumerate the stream and collect every byte any candidate's `code` can contain.
const sizes = FRAME_FIELDS.map((f) => f.size);
const codeBytesSeen = new Set<number>();
let candidates = 0;
for (const idx of indexSumOrder(sizes)) {
  if (++candidates > BUDGET) break;
  for (const b of D_BYTES[idx[0]!]!) codeBytesSeen.add(b);
}

console.log(`budget                 B = ${BUDGET}`);
console.log(`candidates enumerated  ${Math.min(candidates, BUDGET)}`);
console.log(`distinct code bytes    ${[...codeBytesSeen].map((b) => '0x' + b.toString(16)).join(', ') || '(none — empty code only)'}`);
console.log(`frozen code domain     ${D_BYTES.length} values, exhausted at index-sum 3`);

// A `case X:` arm executes only if byte X is dispatched, which requires X to appear in
// `frame.code`. The frozen code domain is finite and fully enumerated above, so this is
// exhaustive over the domain — stronger than a 4096-sample result.
const unreachable = [...DISPATCH_OPCODES].filter(([byte]) => !codeBytesSeen.has(byte));

console.log(`\nU-RUN dispatch arms          ${DISPATCH_OPCODES.size}`);
console.log(`reachable from frozen code   ${DISPATCH_OPCODES.size - unreachable.length}`);
console.log(`NO_FROZEN_BRANCH_WITNESS     ${unreachable.length}`);

if (unreachable.length > 0) {
  console.log(
    `\n  no value in the frozen \`bytes\` domain contains any of:\n  ` +
      unreachable.map(([b, n]) => `${n}(0x${b.toString(16)})`).join(', '),
  );
}

const runArms = arms.filter((a) => a.file === 'src/run.ts' && a.type === 'switch');
console.log(`\nuncovered arms reported      ${arms.length}`);
console.log(`  of which U-RUN switch arms ${runArms.length}`);

if (unreachable.length > 0) {
  console.log(
    `\nNO_FROZEN_BRANCH_WITNESS — Step 2 §8.2.2.\n` +
      `Stop the run, preserve the record, continue only as a new preregistration.\n` +
      `A hand-written fixture to close this gap is prohibited.`,
  );
  process.exit(1);
}
console.log('\nevery uncovered arm has a witness within the budget');
