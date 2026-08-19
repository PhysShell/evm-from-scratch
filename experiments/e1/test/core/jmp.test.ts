/**
 * U-JMP — LT-SEM-JMP-*, 6 of the 213 frozen case IDs.
 */
import { describe, expect, it } from '@jest/globals';
import { isValidTarget, jumpdests, shouldBranch } from '../../src/jmp';
import { JUMPDEST, PUSH1 } from '../../src/opcodes';

describe('U-JMP', () => {
  // SEM-JMP-1: the jumpdest set is every offset holding 0x5B NOT inside a PUSH immediate.
  it('LT-SEM-JMP-1/AT_TOP_LEVEL', () => {
    // 0x5B as an instruction, at offsets 0 and 2.
    expect(jumpdests(Uint8Array.from([JUMPDEST, 0x00, JUMPDEST]))).toEqual(new Set([0, 2]));
  });
  it('LT-SEM-JMP-1/INSIDE_PUSH_IMMEDIATE', () => {
    // PUSH1 0x5B — the 0x5B at offset 1 is data, not a destination.
    expect(jumpdests(Uint8Array.from([PUSH1, JUMPDEST]))).toEqual(new Set());
  });

  // SEM-JMP-2: JUMP transfers to an offset in the set, and halts exceptionally otherwise.
  it('LT-SEM-JMP-2/VALID_TARGET', () => {
    expect(isValidTarget(jumpdests(Uint8Array.from([JUMPDEST])), 0n)).toBe(true);
  });
  it('LT-SEM-JMP-2/INVALID_TARGET', () => {
    const dests = jumpdests(Uint8Array.from([PUSH1, JUMPDEST]));
    expect(isValidTarget(dests, 1n)).toBe(false); // inside the immediate
    expect(isValidTarget(dests, 2n ** 255n)).toBe(false); // far out of range
  });

  // SEM-JMP-3: JUMPI transfers control iff its condition operand is non-zero.
  it('LT-SEM-JMP-3/TAKEN', () => {
    expect(shouldBranch(1n)).toBe(true);
    expect(shouldBranch(2n ** 255n)).toBe(true);
  });
  it('LT-SEM-JMP-3/NOT_TAKEN', () => {
    expect(shouldBranch(0n)).toBe(false);
  });
});
