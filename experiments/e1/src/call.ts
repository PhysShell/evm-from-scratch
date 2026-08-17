/**
 * U-CALL — the CALL-family opcode handler. Step 2 §3.3 and §3.4.
 *
 * THIS UNIT CONTAINS THE SEAM. Frame construction lives inside it and is not a separately
 * exported function — that is the load-bearing decomposition choice of Step 2 §1.2, taken
 * because the EVM specification defines CALL/STATICCALL/DELEGATECALL as single operations
 * and knows no frame factory. The constructed frame reaches the outside world only as the
 * argument handed to the substituted `runFrame`.
 *
 * The implementation here is CLEAN. No defect from the Step 0 §6 catalog is injected; that
 * is step 8, on separate revisions.
 */
import type { Frame, FrameResult, World } from './domain';
import { pop } from './stack';
import { applyResult } from './ret';

export type Kind = 'CALL' | 'STATICCALL' | 'DELEGATECALL';

/**
 * SEM-CALL-1..3: arity and pop order, matching upstream fixtures #140 / #146 / #147.
 * `CALL` alone carries `value` (SEM-CALL-6).
 */
const OPERANDS: Record<Kind, readonly string[]> = {
  CALL: ['gas', 'address', 'value', 'argsOffset', 'argsSize', 'retOffset', 'retSize'],
  STATICCALL: ['gas', 'address', 'argsOffset', 'argsSize', 'retOffset', 'retSize'],
  DELEGATECALL: ['gas', 'address', 'argsOffset', 'argsSize', 'retOffset', 'retSize'],
};

/** Pops the kind's operands off the caller's stack, top first, in the frozen order. */
export function popOperands(kind: Kind, stack: bigint[]): Record<string, bigint> {
  const out: Record<string, bigint> = {};
  for (const name of OPERANDS[kind]) out[name] = pop(stack);
  return out;
}

/**
 * Build the callee frame — SEM-SEAM-P1..P15, as a full kind × field matrix so no cell is
 * left implicit.
 *
 * Internal on purpose (§1.2). Exporting it would put the constructed frame inside the
 * declared local interface and change what the projection hides.
 */
function calleeFrame(kind: Kind, caller: Frame, called: bigint, world: World): Frame {
  const code = world.get(called)?.code ?? new Uint8Array(0); // P13, every kind

  // P1/P5/P9 address, P2/P6/P10 caller, P3/P7/P11 static, P4/P8/P12 storage_owner.
  const identity =
    kind === 'DELEGATECALL'
      ? {
          address: caller.address,             // P9  — the CURRENT frame's address
          caller: caller.caller,               // P10 — inherited, not the current address
          static: caller.static,               // P11
          storage_owner: caller.storage_owner, // P12 — the CURRENT frame's owner
        }
      : {
          address: called,                     // P1 / P5
          caller: caller.address,              // P2 / P6
          static: kind === 'STATICCALL' ? true : caller.static, // P7 forces true; P3 inherits
          storage_owner: called,               // P4 / P8
        };

  return {
    code,
    pc: 0,                              // P14
    stack: [],                          // P15
    memory: new Uint8Array(0),          // P15 — and SEM-CALL-7: no calldata in this model
    ...identity,
    returndata: new Uint8Array(0),      // P15
  };
}

/**
 * Run one call. `runFrame` is U-RUN, substituted in local tests (§1.3) — the only
 * substitution in the seam's neighbourhood.
 *
 * SEM-CALL-5: `gas` is consumed and otherwise ignored.
 * SEM-CALL-7: `argsOffset`/`argsSize` are consumed and otherwise ignored — the model has no
 *             calldata, so a callee cannot observe call input.
 * SEM-CALL-8: `retOffset`/`retSize` bound the copy that U-RET performs.
 */
export function executeCall(
  kind: Kind,
  frame: Frame,
  world: World,
  runFrame: (calleeFrame: Frame) => FrameResult,
): void {
  const ops = popOperands(kind, frame.stack);
  const result = runFrame(calleeFrame(kind, frame, ops['address']!, world));
  applyResult(frame, result, Number(ops['retOffset']!), Number(ops['retSize']!));
}
