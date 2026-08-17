/**
 * Manifest replay — E1 Step 2 §10 step 3 ("manifest replay demonstrated").
 *
 * Recomputes, from primary sources, every value M0 claims to have frozen, and reports a
 * disagreement rather than trusting the record. This is the mechanism that makes the
 * staged append-only manifest of Step 0 §8 checkable instead of merely promised: if a
 * governing document, the corpus, the plan listing or the toolchain moves after M0 was
 * written, replay says so.
 *
 * Exit 0 = every recomputed value matches M0. Exit 1 = at least one does not.
 */
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const E1 = join(__dirname, '..');
const ROOT = join(E1, '..', '..');

interface M0 {
  governing_documents: Record<string, { path: string; blob_sha: string }>;
  oracle_case_indices: {
    level_a: number[];
    level_b_in_subset: number[];
    composition_witnesses: number[];
    level_b_oracle: number[];
  };
  toolchain: Record<string, string>;
  test_plan: {
    core_case_ids: string[];
    plan_core_digest: string;
    c2_control_core_digest: string;
    c2_control_assertion: string;
  };
}

const m0: M0 = JSON.parse(readFileSync(join(E1, 'manifest', 'M0-protocol.json'), 'utf8'));

const failures: string[] = [];
function check(label: string, actual: unknown, expected: unknown): void {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(`${ok ? 'ok  ' : 'FAIL'}  ${label}`);
  if (!ok) {
    failures.push(`${label}\n    recomputed: ${JSON.stringify(actual)}\n    in M0:      ${JSON.stringify(expected)}`);
  }
}

// 1. Governing documents, by git blob sha.
for (const [key, doc] of Object.entries(m0.governing_documents)) {
  const sha = execFileSync('git', ['hash-object', doc.path], { cwd: ROOT, encoding: 'utf8' }).trim();
  check(`document ${key} blob sha`, sha, doc.blob_sha);
}

// 2. Oracle case indices, recomputed from the corpus rather than re-read from M0.
const LEVEL_A_OPS = new Set<string>([
  'STOP', 'POP', 'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'LT', 'GT', 'EQ', 'ISZERO',
  'JUMP', 'JUMPI', 'JUMPDEST', 'PC',
  ...Array.from({ length: 33 }, (_, i) => `PUSH${i}`),
  ...Array.from({ length: 16 }, (_, i) => `DUP${i + 1}`),
  ...Array.from({ length: 16 }, (_, i) => `SWAP${i + 1}`),
]);
const LEVEL_B_OPS = new Set<string>([
  ...LEVEL_A_OPS,
  'MSTORE', 'MLOAD', 'MSIZE', 'SLOAD', 'SSTORE', 'RETURN', 'REVERT',
  'RETURNDATASIZE', 'RETURNDATACOPY', 'CALL', 'STATICCALL', 'DELEGATECALL',
  'ADDRESS', 'CALLER', 'GAS',
]);

interface Case {
  code: { asm: string };
  state?: Record<string, { code?: { asm?: string } }>;
}
const corpus: Case[] = JSON.parse(readFileSync(join(ROOT, 'evm.json'), 'utf8'));

const mnemonics = (asm: string): string[] =>
  asm.split('\n').map((l) => l.trim()).filter(Boolean).map((l) => l.split(/\s+/)[0]!);

/**
 * In-subset requires the nested callee code in `state` to be in-subset too, not only the
 * outer asm — Step 0 §1.4. The seam fixtures carry callee bytecode there.
 */
const inSubset = (c: Case, ops: Set<string>): boolean =>
  mnemonics(c.code.asm).every((m) => ops.has(m)) &&
  Object.values(c.state ?? {}).every((a) => mnemonics(a.code?.asm ?? '').every((m) => ops.has(m)));

const levelA = corpus.flatMap((c, i) => (inSubset(c, LEVEL_A_OPS) ? [i + 1] : []));
const levelB = corpus.flatMap((c, i) => (inSubset(c, LEVEL_B_OPS) ? [i + 1] : []));
const witnesses = m0.oracle_case_indices.composition_witnesses;
const levelBOracle = levelB.filter((i) => !witnesses.includes(i));

check('oracle level A', levelA, m0.oracle_case_indices.level_a);
check('oracle level B in-subset', levelB, m0.oracle_case_indices.level_b_in_subset);
check('oracle level B less witnesses', levelBOracle, m0.oracle_case_indices.level_b_oracle);
check('every witness is in-subset', witnesses.filter((w) => levelB.includes(w)), witnesses);

// 3. Plan digests, recomputed from M0's own ID listing.
const sha256 = (s: string): string => createHash('sha256').update(s).digest('hex');
const ids = [...m0.test_plan.core_case_ids].sort();
check('plan_core_digest', sha256(ids.join('\n') + '\n'), m0.test_plan.plan_core_digest);
check(
  'c2_control_core_digest',
  sha256([...ids, m0.test_plan.c2_control_assertion].sort().join('\n') + '\n'),
  m0.test_plan.c2_control_core_digest,
);
check('the two domains differ by exactly the C2 assertion', ids.includes(m0.test_plan.c2_control_assertion), false);

// 4. Toolchain, from the lockfile rather than from intent.
const lock = JSON.parse(readFileSync(join(E1, 'package-lock.json'), 'utf8')) as {
  packages: Record<string, { version?: string }>;
};
for (const [name, version] of Object.entries(m0.toolchain)) {
  check(`toolchain ${name}`, lock.packages[`node_modules/${name}`]?.version, version);
}

console.log(
  failures.length === 0
    ? '\nmanifest replay: M0 agrees with every primary source'
    : `\nmanifest replay: ${failures.length} DISAGREEMENT(S)\n\n${failures.join('\n\n')}`,
);
process.exit(failures.length === 0 ? 0 : 1);
