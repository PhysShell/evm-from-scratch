/**
 * U-RUN — the interpreter loop. Step 2 §3.1 and §3.5.
 *
 * At step 5 this dispatches the frozen level-B subset as well. `U-CALL` is a substituted
 * collaborator in local tests (§1.3); here it is handed `execute` itself as `runFrame`, which
 * is the real composition the witnesses exercise.
 *
 * The implementation is CLEAN — no defect from the Step 0 §6 catalog is present.
 */
import { ExceptionalHalt, MAX_UINT256 } from './domain';
import type { Frame, FrameResult, World } from './domain';
import { decode } from './dec';
import { dup, pop, push, swap } from './stack';
import { add, div, mod, mul, sub } from './ari';
import { eq, gt, iszero, lt } from './cmp';
import { isValidTarget, jumpdests, shouldBranch } from './jmp';
import { mload, msize, mstore } from './mem';
import { sload } from './sto';
import { guardedSstore } from './grd';
import { exceptionalHalt, halt } from './hlt';
import { applyResult, returndatacopy, returndatasize } from './ret';
import { executeCall, type Kind } from './call';
import {
  ADD, ADDRESS, CALL, CALLER, DELEGATECALL, DIV, EQ, GAS, GT, ISZERO, JUMP, JUMPDEST, JUMPI,
  LT, MLOAD, MOD, MSIZE, MSTORE, MUL, PC, POP, RETURN, RETURNDATACOPY, RETURNDATASIZE, REVERT,
  SLOAD, SSTORE, STATICCALL, STOP, SUB,
  dupIndex, isDup, isPush, isSwap, swapIndex,
} from './opcodes';

export interface RunResult {
  success: boolean;
  /** Bottom-first, matching `Frame.stack`. */
  stack: bigint[];
}

const CALL_KIND: Record<number, Kind> = {
  [CALL]: 'CALL',
  [STATICCALL]: 'STATICCALL',
  [DELEGATECALL]: 'DELEGATECALL',
};

/** Execute a frame to completion, yielding the `FrameResult` its caller observes. */
export function execute(frame: Frame, world: World): FrameResult {
  const dests = jumpdests(frame.code);
  const stack = frame.stack;
  let pc = frame.pc;

  try {
    // SEM-RUN-3: the loop condition IS the rule — falling off the end is a normal halt.
    while (pc < frame.code.length) {
      const instruction = decode(frame.code, pc);
      const op = instruction.op;
      const opPc = pc;
      pc = instruction.nextPc;

      if (isPush(op)) { push(stack, instruction.immediate); continue; }
      if (isDup(op)) { dup(stack, dupIndex(op)); continue; }
      if (isSwap(op)) { swap(stack, swapIndex(op)); continue; }

      const kind = CALL_KIND[op];
      if (kind !== undefined) {
        frame.pc = pc;
        executeCall(kind, frame, world, (callee) => execute(callee, world));
        continue;
      }

      switch (op) {
        case STOP:
          return { halt: 'NORMAL', returndata: new Uint8Array(0) };
        case POP: pop(stack); break;
        case ADD: push(stack, add(pop(stack), pop(stack))); break;
        case SUB: push(stack, sub(pop(stack), pop(stack))); break;
        case MUL: push(stack, mul(pop(stack), pop(stack))); break;
        case DIV: push(stack, div(pop(stack), pop(stack))); break;
        case MOD: push(stack, mod(pop(stack), pop(stack))); break;
        case LT: push(stack, lt(pop(stack), pop(stack))); break;
        case GT: push(stack, gt(pop(stack), pop(stack))); break;
        case EQ: push(stack, eq(pop(stack), pop(stack))); break;
        case ISZERO: push(stack, iszero(pop(stack))); break;
        case JUMPDEST: break;

        case JUMP: {
          const target = pop(stack);
          if (!isValidTarget(dests, target)) throw new ExceptionalHalt('jump to a non-JUMPDEST');
          pc = Number(target);
          break;
        }
        case JUMPI: {
          const target = pop(stack);
          const condition = pop(stack);
          if (shouldBranch(condition)) {
            if (!isValidTarget(dests, target)) throw new ExceptionalHalt('jumpi to a non-JUMPDEST');
            pc = Number(target);
          }
          break;
        }
        // SEM-RUN-1: the offset of the PC opcode itself, not of the next instruction.
        case PC: push(stack, BigInt(opPc)); break;

        // ---- level B ----
        case GAS: push(stack, MAX_UINT256); break;          // SEM-RUN-4
        case ADDRESS: push(stack, frame.address); break;    // SEM-SEAM-C1
        case CALLER: push(stack, frame.caller); break;      // SEM-SEAM-C2

        case MSTORE: {
          const offset = pop(stack);
          const value = pop(stack);
          const mem = { bytes: frame.memory };
          mstore(mem, Number(offset), value);
          frame.memory = mem.bytes;
          break;
        }
        case MLOAD: {
          // The holder is written back because MLOAD expands memory (SEM-MEM-2/3).
          const mem = { bytes: frame.memory };
          const value = mload(mem, Number(pop(stack)));
          frame.memory = mem.bytes;
          push(stack, value);
          break;
        }
        case MSIZE: push(stack, BigInt(msize({ bytes: frame.memory }))); break;

        case SLOAD: push(stack, sload(world, frame, pop(stack))); break;
        case SSTORE: {
          const slot = pop(stack);
          const value = pop(stack);
          guardedSstore(world, frame, slot, value);
          break;
        }

        case RETURN:
        case REVERT: {
          const offset = pop(stack);
          const len = pop(stack);
          return halt(frame, op === RETURN ? 'RETURN' : 'REVERT', Number(offset), Number(len));
        }

        case RETURNDATASIZE: push(stack, returndatasize(frame)); break;
        case RETURNDATACOPY: {
          const destOffset = pop(stack);
          const offset = pop(stack);
          const len = pop(stack);
          returndatacopy(frame, Number(destOffset), Number(offset), Number(len));
          break;
        }

        default:
          throw new ExceptionalHalt(`opcode 0x${op.toString(16)} is outside the frozen subset`);
      }
    }
    return { halt: 'NORMAL', returndata: new Uint8Array(0) };
  } catch (error) {
    // SEM-HLT-3: an exceptional halt other than REVERT carries no returndata.
    if (error instanceof ExceptionalHalt) return exceptionalHalt();
    throw error;
  }
}

/**
 * Top-level entry. `world` defaults to empty so the level-A oracle, whose fixtures carry no
 * state, calls this unchanged.
 */
export function run(frame: Frame, world: World = new Map()): RunResult {
  const result = execute(frame, world);
  return { success: result.halt === 'NORMAL', stack: frame.stack };
}

/** SEM-RUN-4. Re-exported so the constant has one home. */
export const GAS_VALUE = MAX_UINT256;

export { applyResult };
