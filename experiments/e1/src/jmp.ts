/**
 * U-JMP — JUMPDEST analysis and jump validity. E1 Step 2 §3.1, SEM-JMP-1..3.
 */
import { JUMPDEST, isPush, pushWidth } from './opcodes';

/**
 * SEM-JMP-1: the jumpdest set is every offset holding 0x5B that is NOT inside a PUSH
 * immediate.
 *
 * The scan walks instruction-wise rather than byte-wise, which is the whole content of
 * the rule: a 0x5B occurring as PUSH data is data, not a destination.
 */
export function jumpdests(code: Uint8Array): Set<number> {
  const dests = new Set<number>();
  let pc = 0;
  while (pc < code.length) {
    const op = code[pc] ?? 0;
    if (op === JUMPDEST) {
      dests.add(pc);
    }
    pc += isPush(op) ? 1 + pushWidth(op) : 1;
  }
  return dests;
}

/** SEM-JMP-2: a target inside the set is valid; one outside it is not. */
export function isValidTarget(dests: Set<number>, target: bigint): boolean {
  if (target > BigInt(Number.MAX_SAFE_INTEGER)) {
    return false;
  }
  return dests.has(Number(target));
}

/** SEM-JMP-3: JUMPI transfers control iff its condition operand is non-zero. */
export function shouldBranch(condition: bigint): boolean {
  return condition !== 0n;
}
