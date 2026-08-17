/**
 * U-GRD — the static write guard. Step 2 §3.2, SEM-GRD-1..2.
 *
 * The guard reads `frame.static` and acts on it. It does NOT decide what `static` should be:
 * that is the producing side's job (SEM-SEAM-P3/P7/P11), one unit upstream and behind the
 * substitution. Keeping the two apart is the whole shape of the seam under study.
 */
import type { Frame, World } from './domain';
import { ExceptionalHalt } from './domain';
import { sstore } from './sto';

/**
 * SEM-GRD-1: when `static` is set, SSTORE performs no write and halts exceptionally.
 * SEM-GRD-2: when `static` is clear, SSTORE proceeds.
 */
export function guardedSstore(world: World, frame: Frame, slot: bigint, value: bigint): void {
  if (frame.static) {
    // No write, then the halt — in that order, so a caught halt cannot leave a partial write.
    throw new ExceptionalHalt('state write inside a static call');
  }
  sstore(world, frame, slot, value);
}
