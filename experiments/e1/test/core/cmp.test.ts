/**
 * U-CMP — LT-SEM-CMP-*, 8 of the 213 frozen case IDs.
 *
 * Each comparison carries both semantic halves (§3.0 rule ii). That split is what forces
 * control C1b — `LT` implemented as `<=` — to be caught: a plan testing only `GT`, or only
 * the true half, would have left it green.
 */
import { describe, expect, it } from '@jest/globals';
import { eq, gt, iszero, lt } from '../../src/cmp';
import { MAX_UINT256 } from '../../src/domain';

describe('U-CMP', () => {
  // SEM-CMP-1: LT/GT compare unsigned and yield 1 or 0.
  it('LT-SEM-CMP-1/LT_TRUE', () => {
    expect(lt(1n, 2n)).toBe(1n);
  });
  it('LT-SEM-CMP-1/LT_FALSE', () => {
    // Equality must be FALSE for a strict `<`. This is the case that separates `<` from `<=`.
    expect(lt(1n, 1n)).toBe(0n);
    expect(lt(2n, 1n)).toBe(0n);
  });
  it('LT-SEM-CMP-1/GT_TRUE', () => {
    expect(gt(2n, 1n)).toBe(1n);
  });
  it('LT-SEM-CMP-1/GT_FALSE', () => {
    expect(gt(1n, 1n)).toBe(0n);
    expect(gt(1n, 2n)).toBe(0n);
  });

  // SEM-CMP-2: EQ yields 1 iff the operands are equal.
  it('LT-SEM-CMP-2/EQUAL', () => {
    expect(eq(0n, 0n)).toBe(1n);
    expect(eq(MAX_UINT256, MAX_UINT256)).toBe(1n);
  });
  it('LT-SEM-CMP-2/UNEQUAL', () => {
    expect(eq(0n, 1n)).toBe(0n);
  });

  // SEM-CMP-3: ISZERO yields 1 iff the operand is 0.
  it('LT-SEM-CMP-3/ZERO', () => {
    expect(iszero(0n)).toBe(1n);
  });
  it('LT-SEM-CMP-3/NONZERO', () => {
    expect(iszero(1n)).toBe(0n);
    expect(iszero(MAX_UINT256)).toBe(0n);
  });
});
