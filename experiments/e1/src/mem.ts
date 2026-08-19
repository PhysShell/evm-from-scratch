/**
 * U-MEM — byte-addressed memory. Step 2 §3.2, SEM-MEM-1..3.
 *
 * Memory is OWNED STATE (§1.3): handed in and mutated in place, so its after-state is this
 * unit's own observable output.
 */
import type { Memory } from './domain';
import { WORD_MOD } from './domain';

const WORD = 32;

/** Grow to cover `[0, end)`, rounded up to a whole word. Never shrinks. */
function ensure(mem: Memory, end: number): void {
  const needed = Math.ceil(end / WORD) * WORD;
  if (mem.bytes.length >= needed) return;
  const grown = new Uint8Array(needed);
  grown.set(mem.bytes);
  mem.bytes = grown;
}

/** SEM-MEM-1: MSTORE writes 32 big-endian bytes at the given offset. */
export function mstore(mem: Memory, offset: number, value: bigint): void {
  ensure(mem, offset + WORD);
  let v = ((value % WORD_MOD) + WORD_MOD) % WORD_MOD;
  for (let i = WORD - 1; i >= 0; i--) {
    mem.bytes[offset + i] = Number(v & 0xffn);
    v >>= 8n;
  }
}

/**
 * SEM-MEM-2: MLOAD reads 32 bytes; never-written bytes read as 0.
 *
 * A read TOUCHES memory and therefore expands it — SEM-MEM-3 says MSIZE is the highest
 * *touched* offset, and reading is touching. Upstream #94 pins it: `PUSH1 0 / MLOAD / POP /
 * MSIZE` expects 32, with the hint "the first 32-byte section has been accessed".
 */
export function mload(mem: Memory, offset: number): bigint {
  ensure(mem, offset + WORD);
  let v = 0n;
  for (let i = 0; i < WORD; i++) {
    // A read past the end is zero — the zero-extension is the rule, not a guard.
    v = (v << 8n) | BigInt(mem.bytes[offset + i] ?? 0);
  }
  return v;
}

/** SEM-MEM-3: MSIZE is the highest touched offset rounded up to a multiple of 32. */
export function msize(mem: Memory): number {
  return Math.ceil(mem.bytes.length / WORD) * WORD;
}

/** Raw byte access used by RETURN/REVERT and the returndata copy. Reads past the end are 0. */
export function mslice(mem: Memory, offset: number, len: number): Uint8Array {
  const out = new Uint8Array(len);
  for (let i = 0; i < len; i++) out[i] = mem.bytes[offset + i] ?? 0;
  return out;
}

/** Write raw bytes, growing as needed. Used by the returndata copy. */
export function mwrite(mem: Memory, offset: number, data: Uint8Array): void {
  if (data.length === 0) return;
  ensure(mem, offset + data.length);
  mem.bytes.set(data, offset);
}
