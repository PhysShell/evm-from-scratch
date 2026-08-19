/**
 * U-ARI — LT-SEM-ARI-*, 15 of the 213 frozen case IDs.
 *
 * Operands are drawn in the frozen §8.1 rule-1 order: 0, 1, 2, 2^256-1, 2^255, then 3.
 */
import { describe, expect, it } from '@jest/globals';
import { add, div, mod, mul, sub } from '../../src/ari';
import { MAX_UINT256 } from '../../src/domain';

const OPS = { ADD: add, SUB: sub, MUL: mul, DIV: div, MOD: mod } as const;

describe('U-ARI', () => {
  // SEM-ARI-1: operands are popped as `a` then `b`; the result is `a OP b`.
  // Operand ORDER is what this postcondition asserts, so each case uses an asymmetric pair
  // whose result differs under the two orderings.
  const ORDER: Array<[keyof typeof OPS, bigint, bigint, bigint]> = [
    ['ADD', 2n, 1n, 3n],
    ['SUB', 2n, 1n, 1n], // 1 - 2 would wrap to MAX; 2 - 1 = 1 distinguishes them
    ['MUL', 2n, 3n, 6n],
    ['DIV', 2n, 1n, 2n], // 1 / 2 = 0; 2 / 1 = 2
    ['MOD', 3n, 2n, 1n], // 2 % 3 = 2; 3 % 2 = 1
  ];
  it.each(ORDER)('LT-SEM-ARI-1/%s', (name, a, b, expected) => {
    expect(OPS[name](a, b)).toBe(expected);
  });

  // SEM-ARI-2: ADD, SUB, MUL wrap modulo 2^256.
  const WRAP: Array<[keyof typeof OPS, bigint, bigint, bigint]> = [
    ['ADD', MAX_UINT256, 1n, 0n],
    ['SUB', 0n, 1n, MAX_UINT256],
    ['MUL', 2n ** 255n, 2n, 0n],
  ];
  it.each(WRAP)('LT-SEM-ARI-2/%s_WRAP', (name, a, b, expected) => {
    expect(OPS[name](a, b)).toBe(expected);
  });
  const NO_WRAP: Array<[keyof typeof OPS, bigint, bigint, bigint]> = [
    ['ADD', 1n, 2n, 3n],
    ['SUB', 2n, 1n, 1n],
    ['MUL', 2n, 3n, 6n],
  ];
  it.each(NO_WRAP)('LT-SEM-ARI-2/%s_NO_WRAP', (name, a, b, expected) => {
    expect(OPS[name](a, b)).toBe(expected);
  });

  // SEM-ARI-3: DIV with b = 0 yields 0; otherwise floor division.
  it('LT-SEM-ARI-3/ZERO_DIVISOR', () => {
    expect(div(1n, 0n)).toBe(0n);
  });
  it('LT-SEM-ARI-3/NONZERO_DIVISOR', () => {
    expect(div(3n, 2n)).toBe(1n); // floor, not rounding
  });

  // SEM-ARI-4: MOD with b = 0 yields 0; otherwise a mod b.
  it('LT-SEM-ARI-4/ZERO_DIVISOR', () => {
    expect(mod(1n, 0n)).toBe(0n);
  });
  it('LT-SEM-ARI-4/NONZERO_DIVISOR', () => {
    expect(mod(3n, 2n)).toBe(1n);
  });
});
