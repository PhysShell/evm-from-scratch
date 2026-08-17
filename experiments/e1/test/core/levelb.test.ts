/**
 * The remaining 46 level-B case IDs of the frozen plan — Step 2 §8.
 *
 * EXPECTED RED at step 4. Each unit is loaded at test-execution time (see
 * test/support/units.ts) so a missing module fails THIS case ID rather than preventing Jest
 * from running the file, which would collapse 46 attributable failures into one compile
 * error. Nothing here stubs level-B behaviour.
 *
 * Each block declares the API shape it expects. Those shapes are the contract step 5
 * implements; these frozen tests then turn green without being edited.
 */
import { describe, expect, it } from '@jest/globals';
import { loadUnit } from '../support/units';
import type { Frame } from '../../src/domain';
import { MAX_UINT256 } from '../../src/domain';

const AAA = 0x1000000000000000000000000000000000000aaan;
const C42 = 0x1000000000000000000000000000000000000c42n;
const DAD = 0x1000000000000000000000000000000000000dadn;

function frameWith(over: Partial<Frame>): Frame {
  return {
    code: new Uint8Array(0), pc: 0, stack: [], memory: new Uint8Array(0),
    address: 0n, caller: 0n, static: false, storage_owner: 0n,
    returndata: new Uint8Array(0), ...over,
  };
}

// ---------------------------------------------------------------- U-MEM
interface MemApi {
  mstore(mem: { bytes: Uint8Array }, offset: number, value: bigint): void;
  mload(mem: { bytes: Uint8Array }, offset: number): bigint;
  msize(mem: { bytes: Uint8Array }): number;
}
describe('U-MEM (level B — expected red at step 4)', () => {
  const mem = () => loadUnit<MemApi>('mem');

  it('LT-SEM-MEM-1', () => {
    const m = { bytes: new Uint8Array(0) };
    mem().mstore(m, 0, 0x42n);
    expect(m.bytes.slice(0, 32)).toEqual(
      Uint8Array.from([...new Array<number>(31).fill(0), 0x42]),
    );
  });
  it('LT-SEM-MEM-2/WRITTEN', () => {
    const m = { bytes: new Uint8Array(0) };
    mem().mstore(m, 0, 0x42n);
    expect(mem().mload(m, 0)).toBe(0x42n);
  });
  it('LT-SEM-MEM-2/UNWRITTEN', () => {
    expect(mem().mload({ bytes: new Uint8Array(0) }, 0)).toBe(0n);
  });
  it('LT-SEM-MEM-3', () => {
    const m = { bytes: new Uint8Array(0) };
    expect(mem().msize(m)).toBe(0);
    mem().mstore(m, 0, 0x42n);
    expect(mem().msize(m)).toBe(32); // rounded up to a multiple of 32
  });
});

// ---------------------------------------------------------------- U-STO
type World = Map<bigint, { code: Uint8Array; storage: Map<bigint, bigint> }>;
interface StoApi {
  sstore(world: World, frame: Frame, slot: bigint, value: bigint): void;
  sload(world: World, frame: Frame, slot: bigint): bigint;
}
describe('U-STO (level B — expected red at step 4)', () => {
  const sto = () => loadUnit<StoApi>('sto');
  const world = (): World => new Map([[AAA, { code: new Uint8Array(0), storage: new Map() }]]);

  it('LT-SEM-STO-1', () => {
    const w = world();
    sto().sstore(w, frameWith({ storage_owner: AAA }), 0n, 0x42n);
    expect(w.get(AAA)?.storage.get(0n)).toBe(0x42n);
  });
  it('LT-SEM-STO-2', () => {
    const w = world();
    w.get(AAA)!.storage.set(0n, 0x42n);
    expect(sto().sload(w, frameWith({ storage_owner: AAA }), 0n)).toBe(0x42n);
  });
  it('LT-SEM-STO-3', () => {
    expect(sto().sload(world(), frameWith({ storage_owner: AAA }), 0n)).toBe(0n);
  });
  it('LT-SEM-STO-4', () => {
    // No journalling: an exceptional halt does not undo a write already performed.
    const w = world();
    sto().sstore(w, frameWith({ storage_owner: AAA }), 0n, 0x42n);
    expect(w.get(AAA)?.storage.get(0n)).toBe(0x42n);
  });
});

// ---------------------------------------------------------------- U-GRD
interface GrdApi {
  guardedSstore(world: World, frame: Frame, slot: bigint, value: bigint): void;
}
describe('U-GRD (level B — expected red at step 4)', () => {
  const grd = () => loadUnit<GrdApi>('grd');
  const world = (): World => new Map([[AAA, { code: new Uint8Array(0), storage: new Map() }]]);

  it('LT-SEM-GRD-1', () => {
    // static set: no write lands, and the halt is exceptional.
    //
    // The unit is loaded OUTSIDE the `toThrow` assertion on purpose. Loaded inside it, a
    // missing module would satisfy the assertion and this case would report GREEN in the
    // step-4 red state — a false pass, and the one shape of that mistake this suite can
    // make. Here a missing module throws before the assertion and fails the case.
    const g = grd();
    const w = world();
    expect(() =>
      g.guardedSstore(w, frameWith({ storage_owner: AAA, static: true }), 0n, 0x42n),
    ).toThrow();
    expect(w.get(AAA)?.storage.get(0n)).toBeUndefined();
  });
  it('LT-SEM-GRD-2', () => {
    const w = world();
    grd().guardedSstore(w, frameWith({ storage_owner: AAA, static: false }), 0n, 0x42n);
    expect(w.get(AAA)?.storage.get(0n)).toBe(0x42n);
  });
});

// ---------------------------------------------------------------- U-HLT
interface FrameResult { halt: 'NORMAL' | 'EXCEPTIONAL'; returndata: Uint8Array }
interface HltApi {
  halt(frame: Frame, kind: 'RETURN' | 'REVERT', offset: number, len: number): FrameResult;
  exceptionalHalt(): FrameResult;
}
describe('U-HLT (level B — expected red at step 4)', () => {
  const hlt = () => loadUnit<HltApi>('hlt');
  const withMemory = frameWith({ memory: Uint8Array.from([0x42, 0x43]) });

  it('LT-SEM-HLT-1', () => {
    const r = hlt().halt(withMemory, 'RETURN', 0, 2);
    expect(r.halt).toBe('NORMAL');
    expect(r.returndata).toEqual(Uint8Array.from([0x42, 0x43]));
  });
  it('LT-SEM-HLT-2', () => {
    const r = hlt().halt(withMemory, 'REVERT', 0, 2);
    expect(r.halt).toBe('EXCEPTIONAL');
    expect(r.returndata).toEqual(Uint8Array.from([0x42, 0x43]));
  });
  it('LT-SEM-HLT-3', () => {
    const r = hlt().exceptionalHalt();
    expect(r.halt).toBe('EXCEPTIONAL');
    expect(r.returndata).toEqual(new Uint8Array(0));
  });
});

// ---------------------------------------------------------------- U-ENTRY
interface TxContext { to?: bigint; from?: bigint }
interface EntryApi {
  rootFrame(code: Uint8Array, tx: TxContext): Frame;
}
describe('U-ENTRY (level B — expected red at step 4)', () => {
  const entry = () => loadUnit<EntryApi>('entry');
  const CODE = Uint8Array.from([0x42]);

  it('LT-SEM-ROOT-1', () => {
    expect(entry().rootFrame(CODE, {}).code).toEqual(CODE);
  });
  it('LT-SEM-ROOT-2/PRESENT', () => {
    expect(entry().rootFrame(CODE, { to: AAA }).address).toBe(AAA);
  });
  it('LT-SEM-ROOT-2/ABSENT', () => {
    expect(entry().rootFrame(CODE, {}).address).toBe(0n);
  });
  it('LT-SEM-ROOT-3/PRESENT', () => {
    expect(entry().rootFrame(CODE, { from: DAD }).caller).toBe(DAD);
  });
  it('LT-SEM-ROOT-3/ABSENT', () => {
    expect(entry().rootFrame(CODE, {}).caller).toBe(0n);
  });
  it('LT-SEM-ROOT-4', () => {
    const f = entry().rootFrame(CODE, { to: AAA });
    expect(f.storage_owner).toBe(f.address);
  });
  it('LT-SEM-ROOT-5', () => {
    expect(entry().rootFrame(CODE, {}).static).toBe(false);
  });
  it('LT-SEM-ROOT-6', () => {
    expect(entry().rootFrame(CODE, {}).pc).toBe(0);
  });
  it('LT-SEM-ROOT-7', () => {
    const f = entry().rootFrame(CODE, {});
    expect(f.stack).toEqual([]);
    expect(f.memory).toEqual(new Uint8Array(0));
    expect(f.returndata).toEqual(new Uint8Array(0));
  });
});

// ---------------------------------------------------------------- U-CALL
type Kind = 'CALL' | 'STATICCALL' | 'DELEGATECALL';
interface CallApi {
  /** Pops the kind's operands off the caller's stack, in pop order, and returns them. */
  popOperands(kind: Kind, stack: bigint[]): Record<string, bigint>;
  /** Runs the call with `runFrame` substituted; returns nothing observable but the caller. */
  executeCall(
    kind: Kind, frame: Frame, world: World,
    runFrame: (calleeFrame: Frame) => FrameResult,
  ): void;
}
describe('U-CALL (level B — expected red at step 4)', () => {
  const call = () => loadUnit<CallApi>('call');
  const KINDS: Kind[] = ['CALL', 'STATICCALL', 'DELEGATECALL'];
  const world = (): World => new Map([[C42, { code: Uint8Array.from([0x00]), storage: new Map() }]]);
  const noop = (): FrameResult => ({ halt: 'NORMAL', returndata: new Uint8Array(0) });

  // SEM-CALL-1..3: arity and pop order, matching upstream fixtures #140/#146/#147.
  it('LT-SEM-CALL-1', () => {
    // CALL pops gas, address, value, argsOffset, argsSize, retOffset, retSize — top first.
    const stack = [7n, 6n, 5n, 4n, 3n, C42, 1n]; // bottom..top
    const ops = call().popOperands('CALL', stack);
    expect(ops).toMatchObject({
      gas: 1n, address: C42, value: 3n, argsOffset: 4n, argsSize: 5n, retOffset: 6n, retSize: 7n,
    });
    expect(stack).toEqual([]);
  });
  it('LT-SEM-CALL-2', () => {
    const stack = [6n, 5n, 4n, 3n, C42, 1n];
    expect(call().popOperands('STATICCALL', stack)).toMatchObject({
      gas: 1n, address: C42, argsOffset: 3n, argsSize: 4n, retOffset: 5n, retSize: 6n,
    });
    expect(stack).toEqual([]);
  });
  it('LT-SEM-CALL-3', () => {
    const stack = [6n, 5n, 4n, 3n, C42, 1n];
    expect(call().popOperands('DELEGATECALL', stack)).toMatchObject({
      gas: 1n, address: C42, argsOffset: 3n, argsSize: 4n, retOffset: 5n, retSize: 6n,
    });
    expect(stack).toEqual([]);
  });

  // SEM-CALL-4: the `address` operand designates the called account.
  it.each(KINDS)('LT-SEM-CALL-4/%s', (kind) => {
    const c = call();
    let seen: Frame | undefined;
    const stack = kind === 'CALL' ? [0n, 0n, 0n, 0n, 0n, C42, 0n] : [0n, 0n, 0n, 0n, C42, 0n];
    c.executeCall(kind, frameWith({ stack, address: AAA, storage_owner: AAA }), world(),
      (f) => { seen = f; return noop(); });
    // The called account supplies the callee's code whatever the kind.
    expect(seen?.code).toEqual(Uint8Array.from([0x00]));
  });

  // SEM-CALL-5: the gas operand is consumed and otherwise ignored.
  it.each(KINDS)('LT-SEM-CALL-5/%s', (kind) => {
    const c = call();
    const stack = kind === 'CALL'
      ? [0n, 0n, 0n, 0n, 0n, C42, MAX_UINT256]
      : [0n, 0n, 0n, 0n, C42, MAX_UINT256];
    const before = stack.length;
    const ops = c.popOperands(kind, [...stack]);
    expect(ops['gas']).toBe(MAX_UINT256);
    expect(before - (kind === 'CALL' ? 7 : 6)).toBe(0); // arity consumed the gas slot
  });

  // SEM-CALL-6: CALL's value operand is consumed and no value is transferred.
  it('LT-SEM-CALL-6', () => {
    const c = call();
    const stack = [0n, 0n, 0n, 0n, 0x42n, C42, 0n];
    expect(c.popOperands('CALL', stack)['value']).toBe(0x42n);
    expect(stack).toEqual([]);
  });

  // SEM-CALL-7: argsOffset/argsSize are consumed and otherwise ignored — no calldata.
  it.each(KINDS)('LT-SEM-CALL-7/%s', (kind) => {
    const c = call();
    let seen: Frame | undefined;
    const stack = kind === 'CALL' ? [0n, 0n, 2n, 1n, 0n, C42, 0n] : [0n, 0n, 2n, 1n, C42, 0n];
    c.executeCall(kind, frameWith({ stack, memory: Uint8Array.from([0xaa, 0xbb, 0xcc]) }),
      world(), (f) => { seen = f; return noop(); });
    // The model has no calldata: the callee cannot observe call input.
    expect(seen?.memory).toEqual(new Uint8Array(0));
  });

  // SEM-CALL-8: retOffset/retSize bound the returndata copy performed by U-RET.
  it.each(KINDS)('LT-SEM-CALL-8/%s', (kind) => {
    const c = call();
    const caller = frameWith({
      stack: kind === 'CALL' ? [1n, 0n, 0n, 0n, 0n, C42, 0n] : [1n, 0n, 0n, 0n, C42, 0n],
    });
    c.executeCall(kind, caller, world(),
      () => ({ halt: 'NORMAL', returndata: Uint8Array.from([0x42, 0x43]) }));
    expect(caller.memory[0]).toBe(0x42); // retOffset 0, retSize 1 — one byte only
    expect(caller.memory[1] ?? 0).toBe(0);
  });
});

// ---------------------------------------------------------------- U-RET
interface RetApi {
  applyResult(frame: Frame, result: FrameResult, retOffset: number, retSize: number): void;
  returndatasize(frame: Frame): bigint;
  returndatacopy(frame: Frame, destOffset: number, offset: number, len: number): void;
}
describe('U-RET (level B — expected red at step 4)', () => {
  const ret = () => loadUnit<RetApi>('ret');
  const data = Uint8Array.from([0x42, 0x43]);

  // SEM-RET-1: 1 for NORMAL, 0 for EXCEPTIONAL. The EXCEPTIONAL half is what forces D4 red.
  it('LT-SEM-RET-1/NORMAL', () => {
    const f = frameWith({});
    ret().applyResult(f, { halt: 'NORMAL', returndata: data }, 0, 0);
    expect(f.stack[f.stack.length - 1]).toBe(1n);
  });
  it('LT-SEM-RET-1/EXCEPTIONAL', () => {
    const f = frameWith({});
    ret().applyResult(f, { halt: 'EXCEPTIONAL', returndata: data }, 0, 0);
    expect(f.stack[f.stack.length - 1]).toBe(0n);
  });

  // SEM-RET-2: copies min(retSize, |returndata|) bytes to memory at retOffset.
  it('LT-SEM-RET-2/FULL', () => {
    const f = frameWith({});
    ret().applyResult(f, { halt: 'NORMAL', returndata: data }, 0, 2);
    expect(f.memory.slice(0, 2)).toEqual(data);
  });
  it('LT-SEM-RET-2/TRUNCATED', () => {
    const f = frameWith({});
    ret().applyResult(f, { halt: 'NORMAL', returndata: data }, 0, 1);
    expect(f.memory[0]).toBe(0x42);
    expect(f.memory[1] ?? 0).toBe(0);
  });

  // SEM-RET-3 / SEM-RET-4.
  it('LT-SEM-RET-3', () => {
    expect(ret().returndatasize(frameWith({ returndata: data }))).toBe(2n);
  });
  it('LT-SEM-RET-4', () => {
    const f = frameWith({ returndata: data });
    ret().returndatacopy(f, 0, 0, 2);
    expect(f.memory.slice(0, 2)).toEqual(data);
  });
});

// ------------------------------------------------- consuming side, inside U-RUN
describe('U-RUN consuming side (level B — expected red at step 4)', () => {
  // SEM-SEAM-C1/C2 need no missing module: U-RUN exists and does not dispatch ADDRESS or
  // CALLER yet, so each fails on its own case ID.
  const { run } = loadUnit<{ run(f: Frame): { success: boolean; stack: bigint[] } }>('run');

  it('LT-SEM-SEAM-C1', () => {
    const r = run(frameWith({ code: Uint8Array.from([0x30]), address: AAA }));
    expect(r.success).toBe(true);
    expect(r.stack).toEqual([AAA]);
  });
  it('LT-SEM-SEAM-C2', () => {
    const r = run(frameWith({ code: Uint8Array.from([0x33]), caller: DAD }));
    expect(r.success).toBe(true);
    expect(r.stack).toEqual([DAD]);
  });
});
