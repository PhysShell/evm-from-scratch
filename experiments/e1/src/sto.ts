/**
 * U-STO — the storage accessor. Step 2 §3.2, SEM-STO-1..4.
 *
 * `World` is OWNED STATE (§1.3), not a substituted collaborator: it is handed in and mutated,
 * and its after-state is this unit's observable output. That is what makes SEM-STO-* and
 * SEM-GRD-* locally decidable at all.
 *
 * Every access is keyed by the frame's `storage_owner` — never by `address`. The two differ
 * under DELEGATECALL (SEM-SEAM-P12), which is precisely why the field exists.
 */
import type { Account, Frame, World } from './domain';

function account(world: World, owner: bigint): Account {
  let acc = world.get(owner);
  if (acc === undefined) {
    acc = { code: new Uint8Array(0), storage: new Map() };
    world.set(owner, acc);
  }
  return acc;
}

/** SEM-STO-1: SSTORE writes to the storage of the frame's `storage_owner`. */
export function sstore(world: World, frame: Frame, slot: bigint, value: bigint): void {
  account(world, frame.storage_owner).storage.set(slot, value);
}

/**
 * SEM-STO-2: SLOAD reads from the storage of the frame's `storage_owner`.
 * SEM-STO-3: a never-written slot reads as 0.
 *
 * SEM-STO-4 needs no code: there is no journalling, so an exceptional halt cannot undo a
 * write. The absence is the semantics (Step 2 §3.2), not an omission.
 */
export function sload(world: World, frame: Frame, slot: bigint): bigint {
  return world.get(frame.storage_owner)?.storage.get(slot) ?? 0n;
}
