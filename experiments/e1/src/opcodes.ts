/**
 * The frozen level-A opcode set — E1 Step 0 §1.1.
 *
 * Level-B opcodes are deliberately absent: Step 2 §10 step 3 forbids seam code, and an
 * opcode that is not in this table is not "unimplemented", it is out of the frozen subset
 * and decodes to nothing.
 */
export const STOP = 0x00;
export const ADD = 0x01;
export const MUL = 0x02;
export const SUB = 0x03;
export const DIV = 0x04;
export const MOD = 0x06;
export const LT = 0x10;
export const GT = 0x11;
export const EQ = 0x14;
export const ISZERO = 0x15;
export const POP = 0x50;
export const JUMP = 0x56;
export const JUMPI = 0x57;
export const PC = 0x58;
export const JUMPDEST = 0x5b;
export const PUSH0 = 0x5f;
export const PUSH1 = 0x60;
export const PUSH32 = 0x7f;
export const DUP1 = 0x80;
export const DUP16 = 0x8f;
export const SWAP1 = 0x90;
export const SWAP16 = 0x9f;

export function isPush(op: number): boolean {
  return op >= PUSH0 && op <= PUSH32;
}

/** Immediate width of a PUSH opcode. `PUSH0` takes none — `SEM-DEC-4`. */
export function pushWidth(op: number): number {
  return op - PUSH0;
}

export function isDup(op: number): boolean {
  return op >= DUP1 && op <= DUP16;
}

export function isSwap(op: number): boolean {
  return op >= SWAP1 && op <= SWAP16;
}

/** `DUPn` -> n, `SWAPn` -> n. */
export function dupIndex(op: number): number {
  return op - DUP1 + 1;
}

export function swapIndex(op: number): number {
  return op - SWAP1 + 1;
}

// ---------------------------------------------------------------------------
// Level B — Step 0 §1.2. Added at Step 2 §10 step 5.
//
// `test/core/opcodes-b.ts` keeps its own copy and is deliberately NOT deleted: removing it
// would mean editing frozen test imports, and the red -> green transition has to be a
// transformation of production code alone.
// ---------------------------------------------------------------------------
export const RETURNDATASIZE = 0x3d;
export const RETURNDATACOPY = 0x3e;
export const ADDRESS = 0x30;
export const CALLER = 0x33;
export const MLOAD = 0x51;
export const MSTORE = 0x52;
export const SLOAD = 0x54;
export const SSTORE = 0x55;
export const MSIZE = 0x59;
export const GAS = 0x5a;
export const CALL = 0xf1;
export const DELEGATECALL = 0xf4;
export const STATICCALL = 0xfa;
export const RETURN = 0xf3;
export const REVERT = 0xfd;
