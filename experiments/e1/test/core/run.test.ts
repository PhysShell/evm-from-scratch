/**
 * U-RUN — LT-SEM-RUN-*, 4 of the 213 frozen case IDs.
 *
 * RUN-1..3 are level A. RUN-4 is level B under amendment E1-v2/A1: GAS is a level-B opcode
 * (Step 0 §1.2), so at step 4 this case is expected RED. It needs no missing module — U-RUN
 * exists and simply does not dispatch GAS yet, which is the honest reading of "outside the
 * level-A subset".
 */
import { describe, expect, it } from '@jest/globals';
import { run } from '../../src/run';
import type { Frame } from '../../src/domain';
import { MAX_UINT256 } from '../../src/domain';
import { GAS, JUMPDEST, PC, PUSH1, STOP } from './opcodes-b';

function frame(code: number[]): Frame {
  return {
    code: Uint8Array.from(code),
    pc: 0,
    stack: [],
    memory: new Uint8Array(0),
    address: 0n,
    caller: 0n,
    static: false,
    storage_owner: 0n,
    returndata: new Uint8Array(0),
  };
}

describe('U-RUN', () => {
  // SEM-RUN-1: PC pushes the offset of the PC opcode itself, not of the next instruction.
  it('LT-SEM-RUN-1', () => {
    const r = run(frame([JUMPDEST, PC]));
    expect(r.success).toBe(true);
    expect(r.stack).toEqual([1n]);
  });

  // SEM-RUN-2: STOP halts normally.
  it('LT-SEM-RUN-2', () => {
    const r = run(frame([PUSH1, 0x42, STOP, PUSH1, 0x43]));
    expect(r.success).toBe(true);
    expect(r.stack).toEqual([0x42n]); // the code after STOP must not run
  });

  // SEM-RUN-3: execution running past the end of code halts normally.
  it('LT-SEM-RUN-3', () => {
    const r = run(frame([PUSH1, 0x42]));
    expect(r.success).toBe(true);
    expect(r.stack).toEqual([0x42n]);
  });

  // SEM-RUN-4: GAS pushes MAX_UINT256. LEVEL B — expected red at step 4.
  it('LT-SEM-RUN-4', () => {
    const r = run(frame([GAS]));
    expect(r.success).toBe(true);
    expect(r.stack).toEqual([MAX_UINT256]);
  });
});
