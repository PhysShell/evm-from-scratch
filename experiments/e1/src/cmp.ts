/**
 * U-CMP — comparison. E1 Step 2 §3.1, SEM-CMP-1..3. All comparisons unsigned.
 */
export function lt(a: bigint, b: bigint): bigint {
  return a < b ? 1n : 0n;
}

export function gt(a: bigint, b: bigint): bigint {
  return a > b ? 1n : 0n;
}

export function eq(a: bigint, b: bigint): bigint {
  return a === b ? 1n : 0n;
}

export function iszero(a: bigint): bigint {
  return a === 0n ? 1n : 0n;
}
