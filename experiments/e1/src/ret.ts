/**
 * U-RET — applying a returned FrameResult to the calling frame. Step 2 §3.5, SEM-RET-1..4.
 *
 * This unit sees a `FrameResult` it is handed; it never runs the callee. The halt status it
 * receives is the callee's, and turning that into the caller's success flag is SEM-RET-1 —
 * a SURVIVING postcondition, which is why defect D4 is predicted to be caught locally.
 */
import type { Frame, FrameResult } from './domain';
import { push } from './stack';
import { mwrite } from './mem';

/**
 * SEM-RET-1: the caller pushes 1 for NORMAL and 0 for EXCEPTIONAL.
 * SEM-RET-2: the caller copies min(retSize, |returndata|) bytes to memory at retOffset.
 */
export function applyResult(
  frame: Frame,
  result: FrameResult,
  retOffset: number,
  retSize: number,
): void {
  // The callee's returndata is observable to the caller afterwards (SEM-RET-3/4), whether or
  // not any of it was copied into memory.
  frame.returndata = result.returndata;

  const len = Math.min(retSize, result.returndata.length);
  if (len > 0) {
    const mem = { bytes: frame.memory };
    mwrite(mem, retOffset, result.returndata.subarray(0, len));
    frame.memory = mem.bytes;
  }

  push(frame.stack, result.halt === 'NORMAL' ? 1n : 0n);
}

/** SEM-RET-3: RETURNDATASIZE is the length of the most recent result's returndata. */
export function returndatasize(frame: Frame): bigint {
  return BigInt(frame.returndata.length);
}

/** SEM-RET-4: RETURNDATACOPY copies from that returndata into memory. */
export function returndatacopy(
  frame: Frame,
  destOffset: number,
  offset: number,
  len: number,
): void {
  const slice = new Uint8Array(len);
  for (let i = 0; i < len; i++) slice[i] = frame.returndata[offset + i] ?? 0;
  const mem = { bytes: frame.memory };
  mwrite(mem, destOffset, slice);
  frame.memory = mem.bytes;
}
