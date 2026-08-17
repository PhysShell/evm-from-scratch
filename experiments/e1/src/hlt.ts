/**
 * U-HLT — halting. Step 2 §3.2, SEM-HLT-1..3.
 */
import type { Frame, FrameResult } from './domain';
import { mslice } from './mem';

/**
 * SEM-HLT-1: RETURN yields NORMAL with returndata memory[offset .. offset+len).
 * SEM-HLT-2: REVERT yields EXCEPTIONAL with the same returndata.
 *
 * REVERT is the one exceptional halt that carries data; that asymmetry is Step 2 §2.
 */
export function halt(
  frame: Frame,
  kind: 'RETURN' | 'REVERT',
  offset: number,
  len: number,
): FrameResult {
  const returndata = mslice({ bytes: frame.memory }, offset, len);
  return { halt: kind === 'RETURN' ? 'NORMAL' : 'EXCEPTIONAL', returndata };
}

/** SEM-HLT-3: any other exceptional halt yields empty returndata. */
export function exceptionalHalt(): FrameResult {
  return { halt: 'EXCEPTIONAL', returndata: new Uint8Array(0) };
}
