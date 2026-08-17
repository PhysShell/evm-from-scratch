/**
 * U-ARI — arithmetic over uint256. E1 Step 2 §3.1, SEM-ARI-1..4.
 *
 * SEM-ARI-1  operands are popped as `a` then `b`; the result is `a OP b`.
 * SEM-ARI-2  ADD, SUB, MUL wrap modulo 2^256.
 * SEM-ARI-3  DIV with b = 0 yields 0; otherwise floor division.
 * SEM-ARI-4  MOD with b = 0 yields 0; otherwise a mod b.
 */
import { wrap } from './domain';

export function add(a: bigint, b: bigint): bigint {
  return wrap(a + b);
}

export function sub(a: bigint, b: bigint): bigint {
  return wrap(a - b);
}

export function mul(a: bigint, b: bigint): bigint {
  return wrap(a * b);
}

export function div(a: bigint, b: bigint): bigint {
  // Division by zero is not an exceptional halt in the EVM; it yields zero.
  return b === 0n ? 0n : wrap(a / b);
}

export function mod(a: bigint, b: bigint): bigint {
  return b === 0n ? 0n : wrap(a % b);
}
