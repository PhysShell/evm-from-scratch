/**
 * U-STK — the stack. E1 Step 2 §3.1, SEM-STK-1..7.
 *
 * The stack is `owned state` in the sense of Step 2 §1.3: it is handed in and mutated,
 * and its after-state is the unit's own observable output.
 *
 * Index 0 is the BOTTOM of the stack; the top is the last element. `evm.json` reports the
 * top first, so the oracle harness reverses — see test/oracle-a.test.ts.
 */
import { ExceptionalHalt, MAX_STACK_DEPTH } from './domain';

/** SEM-STK-1, SEM-STK-7. */
export function push(stack: bigint[], value: bigint): void {
  if (stack.length >= MAX_STACK_DEPTH) {
    throw new ExceptionalHalt('stack overflow');
  }
  stack.push(value);
}

/** SEM-STK-2, SEM-STK-3. */
export function pop(stack: bigint[]): bigint {
  const top = stack.pop();
  if (top === undefined) {
    throw new ExceptionalHalt('stack underflow');
  }
  return top;
}

/** SEM-STK-4, SEM-STK-6: DUPn copies the n-th item from the top to the top. */
export function dup(stack: bigint[], n: number): void {
  const value = stack[stack.length - n];
  if (value === undefined) {
    throw new ExceptionalHalt('stack underflow');
  }
  push(stack, value);
}

/** SEM-STK-5, SEM-STK-6: SWAPn exchanges the top with the (n+1)-th item. */
export function swap(stack: bigint[], n: number): void {
  const topIndex = stack.length - 1;
  const otherIndex = stack.length - 1 - n;
  const top = stack[topIndex];
  const other = stack[otherIndex];
  if (top === undefined || other === undefined) {
    throw new ExceptionalHalt('stack underflow');
  }
  stack[topIndex] = other;
  stack[otherIndex] = top;
}
