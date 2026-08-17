/**
 * U-STK — LT-SEM-STK-*, 68 of the 213 frozen case IDs.
 *
 * Index 0 is the BOTTOM of the stack; the top is the last element. Depths follow the frozen
 * §8.1 rule 5: the smallest depth that exercises the stated rule.
 */
import { describe, expect, it } from '@jest/globals';
import { dup, pop, push, swap } from '../../src/stack';
import { ExceptionalHalt, MAX_STACK_DEPTH } from '../../src/domain';

const N16 = Array.from({ length: 16 }, (_, i) => i + 1);

describe('U-STK', () => {
  // SEM-STK-1: push increases depth by 1; the pushed value is the new top.
  it('LT-SEM-STK-1', () => {
    const s: bigint[] = [];
    push(s, 1n);
    expect(s).toEqual([1n]);
    push(s, 2n);
    expect(s).toEqual([1n, 2n]);
  });

  // SEM-STK-2: pop decreases depth by 1 and yields the previous top.
  it('LT-SEM-STK-2', () => {
    const s = [1n, 2n];
    expect(pop(s)).toBe(2n);
    expect(s).toEqual([1n]);
  });

  // SEM-STK-3: pop on an empty stack halts exceptionally.
  it('LT-SEM-STK-3', () => {
    expect(() => pop([])).toThrow(ExceptionalHalt);
  });

  // SEM-STK-4: DUPn copies the n-th item from the top to the top; depth increases by 1.
  it.each(N16)('LT-SEM-STK-4/DUP%i', (n) => {
    // Smallest depth exercising DUPn is exactly n. Values are the §8.1 uint256 order.
    const values = [0n, 1n, 2n, 2n ** 256n - 1n, 2n ** 255n, 3n];
    const s = Array.from({ length: n }, (_, i) => values[i % values.length]!);
    const expectedTop = s[s.length - n]!;
    dup(s, n);
    expect(s).toHaveLength(n + 1);
    expect(s[s.length - 1]).toBe(expectedTop);
  });

  // SEM-STK-5: SWAPn exchanges the top with the (n+1)-th item; depth is unchanged.
  it.each(N16)('LT-SEM-STK-5/SWAP%i', (n) => {
    // Smallest depth exercising SWAPn is n+1.
    const s = Array.from({ length: n + 1 }, (_, i) => BigInt(i));
    const beforeTop = s[s.length - 1]!;
    const beforeOther = s[s.length - 1 - n]!;
    swap(s, n);
    expect(s).toHaveLength(n + 1);
    expect(s[s.length - 1]).toBe(beforeOther);
    expect(s[s.length - 1 - n]).toBe(beforeTop);
  });

  // SEM-STK-6: DUPn / SWAPn with insufficient depth halts exceptionally.
  it.each(N16)('LT-SEM-STK-6/DUP%i', (n) => {
    const s = Array.from({ length: n - 1 }, (_, i) => BigInt(i));
    expect(() => dup(s, n)).toThrow(ExceptionalHalt);
  });
  it.each(N16)('LT-SEM-STK-6/SWAP%i', (n) => {
    const s = Array.from({ length: n }, (_, i) => BigInt(i));
    expect(() => swap(s, n)).toThrow(ExceptionalHalt);
  });

  // SEM-STK-7: a push beyond depth 1024 halts exceptionally.
  it('LT-SEM-STK-7', () => {
    const s = Array.from({ length: MAX_STACK_DEPTH }, () => 0n);
    expect(() => push(s, 1n)).toThrow(ExceptionalHalt);
  });
});
