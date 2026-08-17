/**
 * U-DEC — instruction decode. E1 Step 2 §3.1, SEM-DEC-1..4.
 */
import { isPush, pushWidth } from './opcodes';

export interface Instruction {
  /** The opcode byte at the decoded offset. */
  op: number;
  /** Big-endian immediate, zero for a non-PUSH and for PUSH0. */
  immediate: bigint;
  /** Program counter of the next instruction. */
  nextPc: number;
}

/**
 * SEM-DEC-1  a non-PUSH opcode decodes with no immediate; next pc is pc+1.
 * SEM-DEC-2  PUSHn takes the n bytes after the opcode, big-endian; next pc is pc+1+n.
 * SEM-DEC-3  PUSHn with fewer than n bytes remaining is zero-padded on the right.
 * SEM-DEC-4  PUSH0 takes no immediate and yields 0.
 */
export function decode(code: Uint8Array, pc: number): Instruction {
  const op = code[pc] ?? 0;
  if (!isPush(op)) {
    return { op, immediate: 0n, nextPc: pc + 1 };
  }

  const width = pushWidth(op);
  let immediate = 0n;
  for (let i = 0; i < width; i++) {
    // SEM-DEC-3: a byte past the end of code reads as zero, which is exactly
    // right-padding the immediate. Reading it as `?? 0` rather than truncating keeps
    // the value big-endian-correct instead of silently shifting it.
    immediate = (immediate << 8n) | BigInt(code[pc + 1 + i] ?? 0);
  }
  return { op, immediate, nextPc: pc + 1 + width };
}
