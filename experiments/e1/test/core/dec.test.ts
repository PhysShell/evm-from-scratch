/**
 * U-DEC — LT-SEM-DEC-*, 66 of the 213 frozen case IDs (Step 2 §8).
 *
 * Inputs follow the frozen §8.1 order: bytes are the shortest satisfying the condition,
 * then 0x42 repeated. Nothing here is an author's choice.
 */
import { describe, expect, it } from '@jest/globals';
import { decode } from '../../src/dec';
import { PUSH0, PUSH1, STOP } from '../../src/opcodes';

const N = Array.from({ length: 32 }, (_, i) => i + 1);

describe('U-DEC', () => {
  // SEM-DEC-1: a non-PUSH opcode decodes with no immediate; next pc is pc+1.
  it('LT-SEM-DEC-1', () => {
    const d = decode(Uint8Array.from([STOP, 0x42]), 0);
    expect(d.op).toBe(STOP);
    expect(d.immediate).toBe(0n);
    expect(d.nextPc).toBe(1);
  });

  // SEM-DEC-2: PUSHn takes the n bytes after the opcode, big-endian; next pc is pc+1+n.
  it.each(N)('LT-SEM-DEC-2/PUSH%i', (n) => {
    const imm = Array.from({ length: n }, () => 0x42);
    const d = decode(Uint8Array.from([PUSH1 + n - 1, ...imm]), 0);
    expect(d.op).toBe(PUSH1 + n - 1);
    expect(d.immediate).toBe(BigInt('0x' + '42'.repeat(n)));
    expect(d.nextPc).toBe(1 + n);
  });

  // SEM-DEC-3: PUSHn with fewer than n bytes remaining is zero-padded on the right.
  it.each(N)('LT-SEM-DEC-3/PUSH%i', (n) => {
    // Supply n-1 bytes; the missing low byte must read as zero, not shift the value.
    const supplied = Array.from({ length: n - 1 }, () => 0x42);
    const d = decode(Uint8Array.from([PUSH1 + n - 1, ...supplied]), 0);
    const expected = n === 1 ? 0n : BigInt('0x' + '42'.repeat(n - 1) + '00');
    expect(d.immediate).toBe(expected);
    expect(d.nextPc).toBe(1 + n);
  });

  // SEM-DEC-4: PUSH0 takes no immediate and yields 0.
  it('LT-SEM-DEC-4', () => {
    const d = decode(Uint8Array.from([PUSH0, 0x42]), 0);
    expect(d.op).toBe(PUSH0);
    expect(d.immediate).toBe(0n);
    expect(d.nextPc).toBe(1);
  });
});
