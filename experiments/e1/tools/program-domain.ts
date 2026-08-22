/**
 * `D_program` — an ATTEMPT at the canonical finite program domain, E1-v5 §3.2 through §3.7.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════════
 * NONCONFORMANCE WARNING — THIS DOMAIN DOES NOT IMPLEMENT FROZEN §3.4
 *
 * §3.4 assigns the `address` operand of CALL / STATICCALL / DELEGATECALL to the §8.2.1 ADDRESS
 * domain. `render` pushes operands k = 0 … need-1, so k = need-1 ends on top, and
 * `popOperands` consumes top-first in the §2 order `gas, address, …`. The address therefore
 * belongs at k = need-2 — 5 for CALL, 4 for STATICCALL and DELEGATECALL. `addressOperand` is
 * 1 for all three, so the address-domain value lands in `retOffset` and the `address` operand
 * receives a plain uint256. Decoded at j = 1:
 *
 *     popOperands binds   address     0x1
 *                         retOffset   0x1000000000000000000000000000000000000aaa
 *
 * This is wrong at the level of the program BYTES, so every consumer inherits it, and
 * `d_program_digest` in M0-v5 is the digest of a domain that is not the frozen one.
 *
 * NOT REPAIRED. Correcting it changes the rendered bytes and hence the digest, which E1-v5's
 * disposition (`STOP_PROTOCOL_POSTFREEZE_CHAIN_NONCONFORMANT`) forbids after measurement.
 * E1-v6 must derive operand roles from one frozen operand schema fixing pop-order and type
 * together, and check a generated CALL block structurally rather than let the generator
 * confirm itself. See `docs/experiments/E1-v5-STOP.md` §4 and §9(f).
 *
 * Binding rule 5's replay does NOT catch this: it recomputes the digest by calling this same
 * generator, so it establishes self-agreement, not conformance to §3.2–§3.7.
 * ══════════════════════════════════════════════════════════════════════════════════════════
 *
 * Two prohibitions from §6.1 are structural rather than advisory, and are visible in the
 * imports:
 *
 *   - it reads NO file. Every input is a literal below or an opcode byte from `src/opcodes`.
 *   - it imports nothing from `records/`. In particular `step6a-uncovered-arms.json` is not
 *     an input to the construction of this domain, and a `D_program` that changed when that
 *     file changed would violate the preregistration and invalidate the run.
 *
 * The Σ literals live here for the same reason the freeze base does: the thing being checked
 * must not supply the criteria it is judged by.
 */
import { MAX_UINT256 } from '../src/domain';
import * as OP from '../src/opcodes';

// ---------------------------------------------------------------------------
// §3.2 The instruction alphabet Σ.
//
// Membership AND order are Step 0 §1.1 followed by §1.2, as written. Those sections are
// literal opcode lists; reading them in order needs no interpretation, and no opcode outside
// them may enter Σ.
// ---------------------------------------------------------------------------
export interface Ins {
  name: string;
  op: number;
  /** §3.3 — the stack state the frozen postconditions require before ι means anything. */
  need: number;
  /** Immediate width, non-zero only for PUSHn. */
  imm: number;
  /** Index of the operand §2 declares `address`, or -1. Only the CALL family has one. */
  addressOperand: number;
}

const i = (name: string, op: number, need: number, imm = 0, addressOperand = -1): Ins =>
  ({ name, op, need, imm, addressOperand });

const pushN = (n: number): Ins => i(`PUSH${n}`, OP.PUSH0 + n, 0, n);
const dupN = (n: number): Ins => i(`DUP${n}`, OP.DUP1 + n - 1, n);        // SEM-STK-4: depth n
const swapN = (n: number): Ins => i(`SWAP${n}`, OP.SWAP1 + n - 1, n + 1); // SEM-STK-5: depth n+1

const range = (n: number): number[] => Array.from({ length: n }, (_, k) => k + 1);

export const SIGMA: Ins[] = [
  // ---- Step 0 §1.1, in the order that section lists them ----
  i('STOP', OP.STOP, 0),
  i('PUSH0', OP.PUSH0, 0),
  ...range(32).map(pushN),
  i('POP', OP.POP, 1),
  i('ADD', OP.ADD, 2), i('SUB', OP.SUB, 2), i('MUL', OP.MUL, 2),
  i('DIV', OP.DIV, 2), i('MOD', OP.MOD, 2),
  i('LT', OP.LT, 2), i('GT', OP.GT, 2), i('EQ', OP.EQ, 2), i('ISZERO', OP.ISZERO, 1),
  ...range(16).map(dupN),
  ...range(16).map(swapN),
  i('JUMP', OP.JUMP, 1), i('JUMPI', OP.JUMPI, 2), i('JUMPDEST', OP.JUMPDEST, 0),
  i('PC', OP.PC, 0),
  // ---- Step 0 §1.2, in the order that section lists them ----
  i('MSTORE', OP.MSTORE, 2), i('MLOAD', OP.MLOAD, 1), i('MSIZE', OP.MSIZE, 0),
  i('SLOAD', OP.SLOAD, 1), i('SSTORE', OP.SSTORE, 2),
  i('RETURN', OP.RETURN, 2), i('REVERT', OP.REVERT, 2),
  i('RETURNDATASIZE', OP.RETURNDATASIZE, 0), i('RETURNDATACOPY', OP.RETURNDATACOPY, 3),
  i('CALL', OP.CALL, 7, 0, 1),                 // SEM-CALL-1: gas, ADDRESS, value, ...
  i('STATICCALL', OP.STATICCALL, 6, 0, 1),     // SEM-CALL-2: gas, ADDRESS, ...
  i('DELEGATECALL', OP.DELEGATECALL, 6, 0, 1), // SEM-CALL-3: gas, ADDRESS, ...
  i('ADDRESS', OP.ADDRESS, 0), i('CALLER', OP.CALLER, 0), i('GAS', OP.GAS, 0),
];

/**
 * §3.6 — ι such that a frozen §3 postcondition says it halts or transfers control.
 * At most one of these executes per program, which is why the choice is a domain dimension
 * (§3.7) rather than a block. Listed in Σ order.
 */
const TERMINAL_NAMES = ['STOP', 'JUMP', 'JUMPI', 'RETURN', 'REVERT'];

export const TERMINALS: Ins[] = SIGMA.filter((x) => TERMINAL_NAMES.includes(x.name));
/** Σ minus the terminal tier minus the JUMPDEST anchor. */
export const PLAIN: Ins[] = SIGMA.filter(
  (x) => !TERMINAL_NAMES.includes(x.name) && x.name !== 'JUMPDEST',
);

// ---------------------------------------------------------------------------
// §3.4 Operand values, supplied by declared type from the frozen §8.2.1 domains.
// ---------------------------------------------------------------------------
const AAA = 0x1000000000000000000000000000000000000aaan;
const C42 = 0x1000000000000000000000000000000000000c42n;
const DAD = 0x1000000000000000000000000000000000000dadn;

/** The frozen §8.2.1 `address` domain. Cycled where the shared index runs past it. */
const D_ADDRESS = [0n, AAA, C42, DAD];

/**
 * The frozen §8.2.1 `uint256` domain, then `⟨jd⟩`.
 *
 * `⟨jd⟩` is a symbol resolved at render time to the trailing JUMPDEST's offset. It is in the
 * domain because SEM-JMP-2's VALID_TARGET names a jump to a member of the jumpdest set and no
 * numeral can name one; it is appended AFTER the six because §8.1 and §8.2.1 both order
 * numeric domains boundary-first and `⟨jd⟩` is not a numeric boundary.
 */
const JD = Symbol('jd');
const D_UINT256: (bigint | typeof JD)[] = [0n, 1n, 2n, MAX_UINT256, 2n ** 255n, 3n, JD];

export const OPERAND_INDICES = D_UINT256.length; // 7

// ---------------------------------------------------------------------------
// §3.5 Canonical encoding.
// ---------------------------------------------------------------------------
const be32 = (v: bigint): number[] => {
  const out = new Array<number>(32).fill(0);
  let x = v;
  for (let k = 31; k >= 0; k--) {
    out[k] = Number(x & 0xffn);
    x >>= 8n;
  }
  return out;
};

/** Every block's width is operand-independent, so `⟨jd⟩` resolves in one pass, not a fixpoint. */
const blockWidth = (x: Ins): number => x.need * 33 + 1 + x.imm;

/** §3.6 — p(j, t) = plain blocks in Σ order ++ one terminal block ++ the JUMPDEST anchor. */
export function render(j: number, t: Ins): Uint8Array {
  const blocks = [...PLAIN, t];
  const length = blocks.reduce((acc, b) => acc + blockWidth(b), 0) + 1;

  const raw = D_UINT256[j]!;
  const word = raw === JD ? BigInt(length - 1) : (raw as bigint);
  const address = D_ADDRESS[j % D_ADDRESS.length]!;

  const bytes: number[] = [];
  for (const b of blocks) {
    for (let k = 0; k < b.need; k++) {
      bytes.push(OP.PUSH32, ...be32(k === b.addressOperand ? address : word));
    }
    bytes.push(b.op);
    for (let k = 0; k < b.imm; k++) bytes.push(0x42); // §8.1 rule 4
  }
  bytes.push(OP.JUMPDEST); // the ⟨jd⟩ anchor, §3.6

  if (bytes.length !== length) {
    throw new Error(`length model disagrees with render: ${bytes.length} != ${length}`);
  }
  return Uint8Array.from(bytes);
}

export interface Member {
  index: number;
  label: string;
  code: Uint8Array;
}

/**
 * §3.7 — the domain and its order.
 *
 *   0        ε                 SEM-RUN-3 has no other witness
 *   1..35    p(j, t)           j slowest in §3.4 order, t fastest in Σ order
 *   36       p_trunc           PUSH32 with no immediate: the single byte 0x7f
 */
export function buildDomain(): Member[] {
  const members: Member[] = [{ index: 0, label: 'ε', code: new Uint8Array(0) }];
  let index = 1;
  for (let j = 0; j < OPERAND_INDICES; j++) {
    for (const t of TERMINALS) {
      const raw = D_UINT256[j]!;
      const shown = raw === JD ? '⟨jd⟩' : (raw as bigint).toString();
      members.push({ index, label: `p(${shown}, ${t.name})`, code: render(j, t) });
      index++;
    }
  }
  members.push({ index, label: 'p_trunc', code: Uint8Array.from([OP.PUSH32]) });
  return members;
}

/**
 * SEM-JMP-1 — every offset holding `0x5B` that is not inside a PUSH immediate.
 *
 * §3.9 proves this is the singleton `{|p| - 1}` for every generated member, which is what
 * makes every jump forward and bounds each frame at `|Σ| + 1` dispatches. M0-v5 asserts it
 * rather than trusting it (binding rule 5).
 */
export function jumpdests(code: Uint8Array): number[] {
  const out: number[] = [];
  let pc = 0;
  while (pc < code.length) {
    const op = code[pc]!;
    if (op === OP.JUMPDEST) out.push(pc);
    pc += OP.isPush(op) ? 1 + OP.pushWidth(op) : 1;
  }
  return out;
}

/** True iff the trailing anchor is the sole member of the jumpdest set — §3.9. */
export function soleTrailingJumpdest(code: Uint8Array): boolean {
  if (code.length === 0) return true; // ε has no jumpdest and no jump
  const dests = jumpdests(code);
  if (dests.length === 0) return code[code.length - 1] !== OP.JUMPDEST;
  return dests.length === 1 && dests[0] === code.length - 1;
}
