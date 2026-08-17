/**
 * State model — E1 Step 2 §2.
 *
 * Field order in these declarations is NORMATIVE: Step 2 §8.2.1 enumerates composite
 * records by "the field order §2 declares". Reordering a field here changes the
 * branch-search candidate stream, and therefore changes a decision-rule input.
 *
 * Level A uses only the subset of `Frame` its semantics can observe; the remaining
 * fields arrive with Baseline B and are declared here so the order never has to move.
 */

export const WORD_BITS = 256n;
export const WORD_MOD = 1n << WORD_BITS;
export const MAX_UINT256 = WORD_MOD - 1n;
export const MAX_STACK_DEPTH = 1024;

export type Address = bigint;

/** Step 2 §2 — `FrameResult`. */
export type Halt = 'NORMAL' | 'EXCEPTIONAL';

export interface FrameResult {
  halt: Halt;
  returndata: Uint8Array;
}

/**
 * Step 2 §2 — `Frame`. Declaration order is the §8.2.1 enumeration order.
 */
export interface Frame {
  code: Uint8Array;
  pc: number;
  stack: bigint[];
  memory: Uint8Array;
  address: Address;
  caller: Address;
  static: boolean;
  storage_owner: Address;
  returndata: Uint8Array;
}

/** Truncate to a 256-bit word. Every arithmetic result passes through this. */
export function wrap(v: bigint): bigint {
  const m = v % WORD_MOD;
  return m < 0n ? m + WORD_MOD : m;
}

/**
 * An exceptional halt raised from inside a unit. The interpreter loop converts it into a
 * `FrameResult`; a local test observes it directly as the unit's own output.
 *
 * `SEM-HLT-3`: any exceptional halt other than `REVERT` carries no returndata.
 */
export class ExceptionalHalt extends Error {
  constructor(readonly cause_: string) {
    super(`exceptional halt: ${cause_}`);
    this.name = 'ExceptionalHalt';
  }
}

/** Step 2 §2 — `World`. Owned state, not a substituted collaborator (§1.3). */
export interface Account {
  code: Uint8Array;
  storage: Map<bigint, bigint>;
}
export type World = Map<Address, Account>;

/** Step 2 §2 — `TxContext`. Field order is normative (§8.2.1). */
export interface TxContext {
  to?: Address;
  from?: Address;
}

/** Owned memory: a mutable holder, so its after-state is the unit's observable output. */
export interface Memory {
  bytes: Uint8Array;
}
