/**
 * U-RUN — the interpreter loop, level A only. E1 Step 2 §3.1, SEM-RUN-1..4.
 *
 * Baseline A carries NO cross-component seam (Step 0 §1.1). There is no `U-CALL` to
 * substitute here, and none may be added at this step: Step 2 §10 step 3 forbids seam
 * code. Level-B opcodes are therefore not dispatched at all — an opcode outside the frozen
 * level-A set halts exceptionally, which is the honest reading of "outside the subset"
 * rather than a claim that it is unimplemented.
 */
import { ExceptionalHalt, Frame, MAX_UINT256 } from './domain';
import { decode } from './dec';
import { dup, pop, push, swap } from './stack';
import { add, div, mod, mul, sub } from './ari';
import { eq, gt, iszero, lt } from './cmp';
import { isValidTarget, jumpdests, shouldBranch } from './jmp';
import {
  ADD,
  DIV,
  EQ,
  GT,
  ISZERO,
  JUMP,
  JUMPDEST,
  JUMPI,
  LT,
  MOD,
  MUL,
  PC,
  POP,
  STOP,
  SUB,
  dupIndex,
  isDup,
  isPush,
  isSwap,
  swapIndex,
} from './opcodes';

export interface RunResult {
  success: boolean;
  /** Bottom-first, matching `Frame.stack`. */
  stack: bigint[];
}

/**
 * Execute a level-A frame to completion.
 *
 * SEM-RUN-2  STOP halts normally.
 * SEM-RUN-3  running past the end of code halts normally.
 * SEM-RUN-4  GAS pushes MAX_UINT256 — level B, but the constant lives in §1.2 and is
 *            re-exported here so Baseline B does not re-derive it.
 */
export function run(frame: Frame): RunResult {
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

      if (isPush(op)) {
        push(stack, instruction.immediate);
        continue;
      }
      if (isDup(op)) {
        dup(stack, dupIndex(op));
        continue;
      }
      if (isSwap(op)) {
        swap(stack, swapIndex(op));
        continue;
      }

      switch (op) {
        case STOP:
          return { success: true, stack };
        case POP:
          pop(stack);
          break;
        case ADD:
          push(stack, add(pop(stack), pop(stack)));
          break;
        case SUB:
          push(stack, sub(pop(stack), pop(stack)));
          break;
        case MUL:
          push(stack, mul(pop(stack), pop(stack)));
          break;
        case DIV:
          push(stack, div(pop(stack), pop(stack)));
          break;
        case MOD:
          push(stack, mod(pop(stack), pop(stack)));
          break;
        case LT:
          push(stack, lt(pop(stack), pop(stack)));
          break;
        case GT:
          push(stack, gt(pop(stack), pop(stack)));
          break;
        case EQ:
          push(stack, eq(pop(stack), pop(stack)));
          break;
        case ISZERO:
          push(stack, iszero(pop(stack)));
          break;
        case JUMPDEST:
          break;
        case JUMP: {
          const target = pop(stack);
          if (!isValidTarget(dests, target)) {
            throw new ExceptionalHalt('jump to a non-JUMPDEST');
          }
          pc = Number(target);
          break;
        }
        case JUMPI: {
          const target = pop(stack);
          const condition = pop(stack);
          if (shouldBranch(condition)) {
            if (!isValidTarget(dests, target)) {
              throw new ExceptionalHalt('jumpi to a non-JUMPDEST');
            }
            pc = Number(target);
          }
          break;
        }
        case PC:
          // SEM-RUN-1: the offset of the PC opcode itself, not of the next instruction.
          push(stack, BigInt(opPc));
          break;
        default:
          throw new ExceptionalHalt(`opcode 0x${op.toString(16)} is outside the level-A subset`);
      }
    }
    return { success: true, stack };
  } catch (error) {
    if (error instanceof ExceptionalHalt) {
      return { success: false, stack };
    }
    throw error;
  }
}

/** SEM-RUN-4. Level B dispatches this; level A only pins the value. */
export const GAS_VALUE = MAX_UINT256;
