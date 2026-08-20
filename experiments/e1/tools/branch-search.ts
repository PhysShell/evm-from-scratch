/**
 * Branch search — frozen Step 2 §8.2.2, run at step 6a under E1-v5.
 *
 * For each arm the 213 core tests leave uncovered, enumerate candidates from the §8.2.1
 * canonical stream for that unit's input record, up to B = 4096, and take the FIRST that
 * covers the arm.
 *
 * ORDER WARNING. §8.2.2 says "in frozen source order" and §8.2 allocates `LT-BR-*` "in
 * ascending order of source position", but no frozen text defines a total order BETWEEN files.
 * This tool iterates the order its input record supplies — alphabetical by repository-relative
 * path — and that choice is result-bearing: it changes which arm stops the run and which
 * `LT-BR-*` IDs are realised. Whatever this prints is an observation under that order, not the
 * frozen procedure's verdict. E1-v5 stopped on exactly this
 * (`STOP_PROTOCOL_ARM_ORDER_UNDERSPECIFIED`), and a successor must freeze a total order first.
 *
 *   covered within B      -> emit LT-BR-<unit>-<nnn>, inputs recorded verbatim
 *   not covered within B  -> NO_FROZEN_BRANCH_WITNESS: stop, preserve the record
 *   evaluation throws     -> E1-v5 §3.10: a host-level exception is NOT a coverage verdict.
 *                            Neither branch of §8.2.2 applies, the procedure has no defined
 *                            continuation, and the run STOPs preserving the candidate index,
 *                            the arm and the error class. NO NEXT CANDIDATE IS TRIED.
 *
 * A hand-written fixture invented to close a gap remains prohibited outright.
 *
 * The §8.2.1 domains are held here as literals for the same reason the freeze base is: the
 * thing being checked must not supply the criteria it is judged by. `D_program` comes from
 * `program-domain.ts`, which reads no file and imports nothing from `records/`.
 */
import { readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { MAX_UINT256 } from '../src/domain';
import type { Frame, FrameResult, World, Account } from '../src/domain';
import { buildDomain } from './program-domain';
import { loadAll, armSourcePositions, validateAlignment, snapshot, covered } from './instrumented';

const E1 = join(__dirname, '..');
const BUDGET = 4096;

// ---------------------------------------------------------------------------
// §8.2.1 primitive domains, verbatim.
// ---------------------------------------------------------------------------
const AAA = 0x1000000000000000000000000000000000000aaan;
const C42 = 0x1000000000000000000000000000000000000c42n;
const DAD = 0x1000000000000000000000000000000000000dadn;

const D_BOOL = [false, true];
const D_HALT: FrameResult['halt'][] = ['NORMAL', 'EXCEPTIONAL'];
const D_KIND = ['CALL', 'STATICCALL', 'DELEGATECALL'] as const;
const D_UINT256 = [0n, 1n, 2n, MAX_UINT256, 2n ** 255n, 3n];
const D_ADDRESS = [0n, AAA, C42, DAD];
const D_BYTES: Uint8Array[] = [
  new Uint8Array(0),
  Uint8Array.from([0x42]),
  Uint8Array.from(new Array<number>(32).fill(0x42)),
  Uint8Array.from(new Array<number>(33).fill(0x42)),
];
const D_STACK_DEPTH = [0, 1, 2, 3, 17, 1024];
const D_PROGRAM = buildDomain();

/** §8.2.1's six World shapes, with each `code 0x42` replaced by the record's program (§3.8). */
const D_WORLD_SHAPE = [
  (_code: Uint8Array): World => new Map<bigint, Account>(),
  (_code: Uint8Array): World => new Map([[AAA, { code: new Uint8Array(0), storage: new Map() }]]),
  (code: Uint8Array): World => new Map([[AAA, { code, storage: new Map() }]]),
  (code: Uint8Array): World => new Map([[AAA, { code, storage: new Map([[0n, 0n]]) }]]),
  (code: Uint8Array): World => new Map([[AAA, { code, storage: new Map([[0n, 0x42n]]) }]]),
  (code: Uint8Array): World =>
    new Map([
      [AAA, { code, storage: new Map() }],
      [C42, { code, storage: new Map([[0n, 0x42n]]) }],
    ]),
];

const stackOf = (depth: number): bigint[] =>
  Array.from({ length: depth }, (_, k) => D_UINT256[k % D_UINT256.length]!);

// ---------------------------------------------------------------------------
// §8.2.1 record order: increasing INDEX SUM, ties broken lexicographically by field order.
// A plain lexicographic odometer would leave the first 4096 candidates all sharing one
// `code` — the very reason index-sum ordering was frozen.
// ---------------------------------------------------------------------------
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
// Unit input records, from the §1.3 declared inputs typed by §2.
// ---------------------------------------------------------------------------
interface UnitRecord {
  unit: string;
  fields: { name: string; size: number }[];
  /** Runs the unit on one candidate. May throw: §3.10 governs what that means. */
  exercise: (idx: number[], units: Record<string, Record<string, unknown>>) => void;
  describe: (idx: number[]) => Record<string, string>;
}

const frameFrom = (idx: number[], at: number): Frame => ({
  code: D_PROGRAM[idx[at]!]!.code,
  pc: 0,
  stack: stackOf(D_STACK_DEPTH[idx[at + 1]!]!),
  memory: D_BYTES[idx[at + 2]!]!,
  address: D_ADDRESS[idx[at + 3]!]!,
  caller: D_ADDRESS[idx[at + 4]!]!,
  static: D_BOOL[idx[at + 5]!]!,
  storage_owner: D_ADDRESS[idx[at + 6]!]!,
  returndata: D_BYTES[idx[at + 7]!]!,
});

const FRAME_FIELDS = [
  { name: 'code', size: D_PROGRAM.length },
  { name: 'stack', size: D_STACK_DEPTH.length },
  { name: 'memory', size: D_BYTES.length },
  { name: 'address', size: D_ADDRESS.length },
  { name: 'caller', size: D_ADDRESS.length },
  { name: 'static', size: D_BOOL.length },
  { name: 'storage_owner', size: D_ADDRESS.length },
  { name: 'returndata', size: D_BYTES.length },
];
const WORLD_FIELDS = [
  { name: 'world_shape', size: D_WORLD_SHAPE.length },
  { name: 'world_code', size: D_PROGRAM.length },
];
const worldFrom = (idx: number[], at: number): World =>
  D_WORLD_SHAPE[idx[at]!]!(D_PROGRAM[idx[at + 1]!]!.code);

const describeFrame = (idx: number[], at: number): Record<string, string> => ({
  code: D_PROGRAM[idx[at]!]!.label,
  stack_depth: String(D_STACK_DEPTH[idx[at + 1]!]),
  memory: `bytes[${idx[at + 2]}]`,
  address: `0x${D_ADDRESS[idx[at + 3]!]!.toString(16)}`,
  caller: `0x${D_ADDRESS[idx[at + 4]!]!.toString(16)}`,
  static: String(D_BOOL[idx[at + 5]!]),
  storage_owner: `0x${D_ADDRESS[idx[at + 6]!]!.toString(16)}`,
  returndata: `bytes[${idx[at + 7]}]`,
});

/** U-CALL substitutes U-RUN (§1.3), so the collaborator is a double, not the real loop. */
const substitutedRunFrame = (): FrameResult => ({ halt: 'NORMAL', returndata: new Uint8Array(0) });

const RECORDS: Record<string, UnitRecord> = {
  'src/run.ts': {
    unit: 'U-RUN',
    fields: [...FRAME_FIELDS, ...WORLD_FIELDS],
    exercise: (idx, u) => {
      (u['run']!['execute'] as (f: Frame, w: World) => unknown)(frameFrom(idx, 0), worldFrom(idx, 8));
    },
    describe: (idx) => ({
      ...describeFrame(idx, 0),
      world_shape: `W${idx[8]}`,
      world_code: D_PROGRAM[idx[9]!]!.label,
    }),
  },
  'src/call.ts': {
    unit: 'U-CALL',
    fields: [{ name: 'kind', size: D_KIND.length }, ...FRAME_FIELDS, ...WORLD_FIELDS],
    exercise: (idx, u) => {
      const kind = D_KIND[idx[0]!]!;
      const frame = frameFrom(idx, 1);
      const world = worldFrom(idx, 9);
      const call = u['call']!;
      (call['popOperands'] as (k: string, s: bigint[]) => unknown)(kind, [...frame.stack]);
      (call['executeCall'] as (k: string, f: Frame, w: World, r: () => FrameResult) => unknown)(
        kind, frame, world, substitutedRunFrame,
      );
    },
    describe: (idx) => ({ kind: D_KIND[idx[0]!]!, ...describeFrame(idx, 1), world_shape: `W${idx[9]}`, world_code: D_PROGRAM[idx[10]!]!.label }),
  },
  'src/dec.ts': {
    unit: 'U-DEC',
    fields: [{ name: 'code', size: D_PROGRAM.length }, { name: 'pc', size: D_UINT256.length }],
    exercise: (idx, u) => {
      (u['dec']!['decode'] as (c: Uint8Array, pc: number) => unknown)(
        D_PROGRAM[idx[0]!]!.code, Number(D_UINT256[idx[1]!]!),
      );
    },
    describe: (idx) => ({ code: D_PROGRAM[idx[0]!]!.label, pc: String(D_UINT256[idx[1]!]) }),
  },
  'src/jmp.ts': {
    unit: 'U-JMP',
    fields: [{ name: 'code', size: D_PROGRAM.length }, { name: 'target', size: D_UINT256.length }],
    exercise: (idx, u) => {
      const code = D_PROGRAM[idx[0]!]!.code;
      const target = D_UINT256[idx[1]!]!;
      const jmp = u['jmp']!;
      const dests = (jmp['jumpdests'] as (c: Uint8Array) => Set<number>)(code);
      (jmp['isValidTarget'] as (d: Set<number>, t: bigint) => unknown)(dests, target);
      (jmp['shouldBranch'] as (c: bigint) => unknown)(target);
    },
    describe: (idx) => ({ code: D_PROGRAM[idx[0]!]!.label, target: String(D_UINT256[idx[1]!]) }),
  },
  'src/mem.ts': {
    unit: 'U-MEM',
    fields: [
      { name: 'memory', size: D_BYTES.length },
      { name: 'offset', size: D_UINT256.length },
      { name: 'value', size: D_UINT256.length },
    ],
    exercise: (idx, u) => {
      const mem = { bytes: D_BYTES[idx[0]!]! };
      const offset = Number(D_UINT256[idx[1]!]!);
      const value = D_UINT256[idx[2]!]!;
      const m = u['mem']!;
      (m['mstore'] as (mm: unknown, o: number, v: bigint) => void)(mem, offset, value);
      (m['mload'] as (mm: unknown, o: number) => unknown)(mem, offset);
      (m['msize'] as (mm: unknown) => unknown)(mem);
      (m['mslice'] as (mm: unknown, o: number, l: number) => unknown)(mem, offset, Number(value));
      (m['mwrite'] as (mm: unknown, o: number, d: Uint8Array) => void)(mem, offset, D_BYTES[idx[0]!]!);
    },
    describe: (idx) => ({ memory: `bytes[${idx[0]}]`, offset: String(D_UINT256[idx[1]!]), value: String(D_UINT256[idx[2]!]) }),
  },
  'src/sto.ts': {
    unit: 'U-STO',
    fields: [...FRAME_FIELDS, ...WORLD_FIELDS, { name: 'slot', size: D_UINT256.length }, { name: 'value', size: D_UINT256.length }],
    exercise: (idx, u) => {
      const frame = frameFrom(idx, 0);
      const world = worldFrom(idx, 8);
      const slot = D_UINT256[idx[10]!]!;
      const value = D_UINT256[idx[11]!]!;
      const sto = u['sto']!;
      (sto['sstore'] as (w: World, f: Frame, s: bigint, v: bigint) => void)(world, frame, slot, value);
      (sto['sload'] as (w: World, f: Frame, s: bigint) => unknown)(world, frame, slot);
    },
    describe: (idx) => ({ ...describeFrame(idx, 0), world_shape: `W${idx[8]}`, world_code: D_PROGRAM[idx[9]!]!.label, slot: String(D_UINT256[idx[10]!]), value: String(D_UINT256[idx[11]!]) }),
  },
  'src/grd.ts': {
    unit: 'U-GRD',
    fields: [...FRAME_FIELDS, ...WORLD_FIELDS, { name: 'slot', size: D_UINT256.length }, { name: 'value', size: D_UINT256.length }],
    exercise: (idx, u) => {
      (u['grd']!['guardedSstore'] as (w: World, f: Frame, s: bigint, v: bigint) => void)(
        worldFrom(idx, 8), frameFrom(idx, 0), D_UINT256[idx[10]!]!, D_UINT256[idx[11]!]!,
      );
    },
    describe: (idx) => ({ ...describeFrame(idx, 0), world_shape: `W${idx[8]}`, world_code: D_PROGRAM[idx[9]!]!.label, slot: String(D_UINT256[idx[10]!]), value: String(D_UINT256[idx[11]!]) }),
  },
  'src/hlt.ts': {
    unit: 'U-HLT',
    fields: [...FRAME_FIELDS, { name: 'halt', size: D_HALT.length }, { name: 'offset', size: D_UINT256.length }, { name: 'len', size: D_UINT256.length }],
    exercise: (idx, u) => {
      const hlt = u['hlt']!;
      (hlt['halt'] as (f: Frame, k: string, o: number, l: number) => unknown)(
        frameFrom(idx, 0), idx[8] === 0 ? 'RETURN' : 'REVERT',
        Number(D_UINT256[idx[9]!]!), Number(D_UINT256[idx[10]!]!),
      );
      (hlt['exceptionalHalt'] as () => unknown)();
    },
    describe: (idx) => ({ ...describeFrame(idx, 0), halt: String(D_HALT[idx[8]!]), offset: String(D_UINT256[idx[9]!]), len: String(D_UINT256[idx[10]!]) }),
  },
  'src/ret.ts': {
    unit: 'U-RET',
    fields: [...FRAME_FIELDS, { name: 'halt', size: D_HALT.length }, { name: 'result_returndata', size: D_BYTES.length }, { name: 'retOffset', size: D_UINT256.length }, { name: 'retSize', size: D_UINT256.length }],
    exercise: (idx, u) => {
      const frame = frameFrom(idx, 0);
      const result: FrameResult = { halt: D_HALT[idx[8]!]!, returndata: D_BYTES[idx[9]!]! };
      const ret = u['ret']!;
      (ret['applyResult'] as (f: Frame, r: FrameResult, o: number, s: number) => unknown)(
        frame, result, Number(D_UINT256[idx[10]!]!), Number(D_UINT256[idx[11]!]!),
      );
      (ret['returndatasize'] as (f: Frame) => unknown)(frame);
      (ret['returndatacopy'] as (f: Frame, d: number, o: number, l: number) => unknown)(
        frame, Number(D_UINT256[idx[10]!]!), 0, Number(D_UINT256[idx[11]!]!),
      );
    },
    describe: (idx) => ({ ...describeFrame(idx, 0), halt: String(D_HALT[idx[8]!]), result_returndata: `bytes[${idx[9]}]`, retOffset: String(D_UINT256[idx[10]!]), retSize: String(D_UINT256[idx[11]!]) }),
  },
  'src/opcodes.ts': {
    unit: 'U-DEC (opcode predicates)',
    fields: [{ name: 'op', size: 256 }],
    exercise: (idx, u) => {
      const op = idx[0]!;
      const o = u['opcodes']!;
      if ((o['isPush'] as (n: number) => boolean)(op)) (o['pushWidth'] as (n: number) => number)(op);
      if ((o['isDup'] as (n: number) => boolean)(op)) (o['dupIndex'] as (n: number) => number)(op);
      if ((o['isSwap'] as (n: number) => boolean)(op)) (o['swapIndex'] as (n: number) => number)(op);
    },
    describe: (idx) => ({ op: `0x${idx[0]!.toString(16)}` }),
  },
};

// ---------------------------------------------------------------------------
// The run.
// ---------------------------------------------------------------------------
interface Discovery {
  uncovered: { file: string; ordinal: number; line: number; column: number; type: string; arm: number }[];
  arms: Record<string, { type: string; line: number | null; column: number | null }[]>;
}

const discovery: Discovery = JSON.parse(
  readFileSync(join(E1, 'records', 'step6a-uncovered-arms.json'), 'utf8'),
);

const units = loadAll();
const rootRelative = (p: string): string => relative(E1, p);

async function main(): Promise<void> {
const mapped = await armSourcePositions(rootRelative);
const alignment = validateAlignment(discovery.arms, mapped);
const mine = new Map([...mapped].map(([f, arms]) => [f, arms.map((a) => ({ key: a.key, type: a.type }))]));

console.log(`budget                B = ${BUDGET}`);
console.log(`|D_program|             ${D_PROGRAM.length}`);
console.log(`uncovered arms          ${discovery.uncovered.length}`);
console.log(`arm identity            ${alignment.byPosition} by source position, ${alignment.bySibling} by matched sibling, ${alignment.disagree.length} disagree`);
if (alignment.disagree.length > 0) {
  console.log('\nthe ordinal correspondence is not established; no result here would mean anything');
  for (const d of alignment.disagree) console.log(`  ${d}`);
  process.exit(2);
}

interface Witness { id: string; unit: string; arm: string; candidate: number; inputs: Record<string, string> }
const witnesses: Witness[] = [];
const unwitnessed: string[] = [];
let stop: { arm: string; unit: string; candidate: number; error: string } | undefined;

const perUnit = new Map<string, number>();

outer: for (const a of discovery.uncovered) {
  const record = RECORDS[a.file];
  const armName = `${a.file}:${a.line}:${a.column} ${a.type}#${a.arm}`;
  if (record === undefined) {
    unwitnessed.push(`${armName} — no frozen input record for this file`);
    continue;
  }
  const key = mine.get(a.file)?.[a.ordinal]?.key;
  if (key === undefined) {
    unwitnessed.push(`${armName} — arm not present in this instrumentation`);
    continue;
  }

  const sizes = record.fields.map((f) => f.size);
  let n = 0;
  let found: Witness | undefined;
  for (const idx of indexSumOrder(sizes)) {
    if (++n > BUDGET) break;
    const before = snapshot();
    try {
      record.exercise(idx, units);
    } catch (error) {
      const semantic = error instanceof Error && error.constructor.name === 'ExceptionalHalt';
      if (!semantic) {
        // E1-v5 §3.10 — no coverage verdict, so §8.2.2 has no defined continuation.
        stop = { arm: armName, unit: record.unit, candidate: n, error: (error as Error).constructor.name };
        break outer;
      }
    }
    if (covered(before, snapshot()).has(key)) {
      const seq = (perUnit.get(record.unit) ?? 0) + 1;
      perUnit.set(record.unit, seq);
      found = {
        id: `LT-BR-${record.unit}-${String(seq).padStart(3, '0')}`,
        unit: record.unit,
        arm: armName,
        candidate: n,
        inputs: record.describe(idx),
      };
      break;
    }
  }
  if (found) {
    witnesses.push(found);
    continue;
  }
  // §8.2.2: "no candidate covers it within B -> NO_FROZEN_BRANCH_WITNESS, naming the arm and
  // B -> stop the run". The stop is at the FIRST such arm; the procedure does not go on to
  // survey the rest, and a tool that collected them would be answering a different question.
  unwitnessed.push(armName);
  break;
}

console.log(`\nwitnesses emitted       ${witnesses.length}`);
for (const w of witnesses) {
  console.log(`  ${w.id}  ${w.arm}`);
  console.log(`      candidate ${w.candidate}: ${Object.entries(w.inputs).map(([k, v]) => `${k}=${v}`).join(' ')}`);
}
console.log(`unwitnessed arms        ${unwitnessed.length}`);

if (stop) {
  console.log(`\nEVALUATION STOP — E1-v5 §3.10`);
  console.log(`  arm             ${stop.arm}`);
  console.log(`  unit            ${stop.unit}`);
  console.log(`  candidate index ${stop.candidate}`);
  console.log(`  error class     ${stop.error}`);
  console.log(`\nA host-level exception is not a coverage verdict. Neither branch of §8.2.2`);
  console.log(`applies, the procedure has no defined continuation, and no next candidate was tried.`);
  process.exit(1);
}

if (unwitnessed.length > 0) {
  console.log(`\nNO_FROZEN_BRANCH_WITNESS — Step 2 §8.2.2, for ${unwitnessed.length} arm(s):`);
  for (const arm of unwitnessed) console.log(`  ${arm}`);
  console.log(`\nStop the run, preserve the record, continue only as a new preregistration.`);
  console.log(`A hand-written fixture to close this gap is prohibited.`);
  process.exit(1);
}

console.log('\nevery uncovered arm has a witness within the budget');
}

void main();
