/**
 * Level-B opcode numbers, declared in the TEST tree.
 *
 * They live here rather than in `src/opcodes.ts` because step 4 must not touch production
 * level-B code (Step 2 §10). A test needs the byte value to build a fixture; the interpreter
 * must still not know what to do with it. Step 5 moves these into `src/` and this file goes
 * away.
 */
export { JUMPDEST, PC, PUSH1, STOP } from '../../src/opcodes';

export const ADDRESS = 0x30;
export const CALLER = 0x33;
export const CALLDATASIZE = 0x36;
export const MLOAD = 0x51;
export const MSTORE = 0x52;
export const SLOAD = 0x54;
export const SSTORE = 0x55;
export const MSIZE = 0x59;
export const GAS = 0x5a;
export const RETURN = 0xf3;
export const REVERT = 0xfd;
export const CALL = 0xf1;
export const STATICCALL = 0xfa;
export const DELEGATECALL = 0xf4;
export const RETURNDATASIZE = 0x3d;
export const RETURNDATACOPY = 0x3e;
