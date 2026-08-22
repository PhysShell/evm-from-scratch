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
import { buildDomain, soleTrailingJumpdest, SIGMA, PLAIN, TERMINALS } from './program-domain';
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
  /** E1-v3 §3. Absent in M0 and M0-v2, which predate the rule and stay replayable. */
  freeze_merge_sha?: string;
  freeze_base_sha?: string;
  freeze_path?: string;
  experiment_version?: string;
  /** E1-v5 binding rule 5. `D_program` is a decision-rule input, so it is replayed. */
  program_domain?: {
    member_count: number;
    sigma_size: number;
    plain_blocks: number;
    terminal_variants: number;
    d_program_digest: string;
  };
}

// Overridable so E1-v1's stopped manifest stays replayable for audit.
const MANIFEST = process.env['E1_MANIFEST'] ?? 'M0-v3-protocol.json';
const m0: M0 = JSON.parse(readFileSync(join(E1, 'manifest', MANIFEST), 'utf8'));
console.log(`manifest: ${MANIFEST}\n`);

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

// 5. Freeze-event identity and ordering — E1-v3 §3.1(a)-(e) and §3.2 rule 4.
//
//    Ancestry alone is NOT sufficient and was the defect in v3's first draft: it proves the
//    named sha precedes the measurement, not that it IS the merge that introduced the
//    preregistration. The merge of PR #2 satisfies ancestry; so does this document's own PR
//    head. Both are checked against here.
function git(args: string[]): { ok: boolean; out: string } {
  try {
    return { ok: true, out: execFileSync('git', args, { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim() };
  } catch {
    return { ok: false, out: '' };
  }
}

/**
 * Constants of the E1-v3 preregistration, held HERE and not read from the manifest.
 *
 * A first implementation took these out of M0 and fed them to the predicate, which is
 * self-certification a third time over: a manifest naming its own base and its own path can
 * satisfy a predicate parameterised by them. The manifest's declarations are checked
 * against these literals; the predicate is evaluated with the literals.
 */
/**
 * One row per version that defines a freeze event. `experiment_version` selects the row.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════════
 * NONCONFORMANCE WARNING — THE SELECTOR IS SUPPLIED BY THE ARTEFACT BEING CHECKED
 *
 * The paragraph that stood here claimed this was safe: "a manifest that named the wrong
 * version would be judged against that version's base and path, and its own freeze merge
 * introduces neither. Mis-declaring fails the predicate; it cannot weaken it."
 *
 * That holds only for an INCOHERENT mis-declaration. A coherent one passes. A manifest that
 * moves `experiment_version`, `freeze_base_sha`, `freeze_path` and `freeze_merge_sha` together
 * to a genuine older freeze is judged against that older version's literals, satisfies (a)-(e)
 * and the ancestry check, and replays fully green — while its program-domain block still
 * prints under the newer version's heading. Demonstrated with an E1-v3-declaring manifest
 * carrying the v5 program-domain block: every line ok, ending "M0 agrees with every primary
 * source", certifying the v3 freeze.
 *
 * The literals below are correctly held outside the manifest. What is NOT held outside it is
 * the choice of WHICH ROW APPLIES — and that choice decides which literals the manifest is
 * measured against. This is the same defect class the comment above was written to prevent.
 *
 * NOT REPAIRED, per E1-v5's disposition (`STOP_PROTOCOL_POSTFREEZE_CHAIN_NONCONFORMANT`).
 * E1-v6 must fix the verifier's expected version outside the manifest it checks — the blunt
 * option being a separate `verify-m0-v6.ts` with a literal `EXPECTED_VERSION`. See
 * `docs/experiments/E1-v5-STOP.md` §3.1 and §9(g).
 *
 * SECOND DEFECT, same shape — a MANDATORY OBLIGATION IS SKIPPABLE. The whole binding-rule-5
 * section below is guarded by `if (m0.program_domain)`, although frozen §4.2 rule 5 says
 * M0-v5 MUST recompute D_program. A v5 manifest that simply omits the block loses the member
 * count, the digest and the structural assertion, and this script still exits 0 printing
 * "M0 agrees with every primary source" — demonstrated, with no warning of any kind. So the
 * artefact under test controls not only WHICH CRITERIA apply to it but WHETHER A MANDATORY
 * OBLIGATION EXISTS AT ALL. NOT REPAIRED; E1-v6 §9(g) requires every version-mandatory block
 * to be demanded fail-closed.
 *
 * Neither defect unsettles the E1-v5 freeze `f670258`: its topology and the §4.1 predicate are
 * establishable directly from the commit graph, without trusting any manifest.
 * ══════════════════════════════════════════════════════════════════════════════════════════
 */
const FREEZE_LITERALS: Record<string, { base: string; path: string; clause: string }> = {
  'E1-v3': {
    base: 'fbef84cd4a925345d3aa65c2e02d9d7502bea787',
    path: 'docs/experiments/E1-v3-preregistration.md',
    clause: 'E1-v3 §3.1',
  },
  'E1-v5': {
    base: '8f5aaeda667b2fecd7963f53806811b24cc36607',
    path: 'docs/experiments/E1-v5-preregistration.md',
    clause: 'E1-v5 §4.1',
  },
};

if (m0.freeze_merge_sha) {
  const freeze = m0.freeze_merge_sha;
  const literals = FREEZE_LITERALS[m0.experiment_version ?? ''];
  if (literals === undefined) {
    failures.push(`no frozen freeze literals for experiment_version ${m0.experiment_version}`);
    console.log(`\nfreeze event: UNKNOWN VERSION ${m0.experiment_version}`);
    process.exit(1);
  }
  console.log(`\nfreeze event ${freeze.slice(0, 12)} — ${literals.clause}`);

  // What the manifest DECLARES must equal the frozen literals...
  check('manifest freeze_base_sha matches the frozen literal', m0.freeze_base_sha, literals.base);
  if (m0.freeze_path !== undefined) {
    check('manifest freeze_path matches the frozen literal', m0.freeze_path, literals.path);
  }

  // ...and the predicate is evaluated with the literals, never with those declarations.
  const base = literals.base;
  const path = literals.path;

  // (a) exactly two parents
  const parents = git(['rev-list', '--parents', '-n1', freeze]);
  check('freeze (a) is a two-parent merge', parents.ok && parents.out.split(/\s+/).length === 3, true);

  // (b) first parent is the reviewed base
  check('freeze (b) first parent is the frozen base', git(['rev-parse', `${freeze}^1`]).out, base);

  // (c) the preregistration did NOT exist before the merge
  check('freeze (c) path absent at ^1', git(['cat-file', '-e', `${freeze}^1:${path}`]).ok, false);

  // (d) it was supplied by the merged side
  check('freeze (d) path present at ^2', git(['cat-file', '-e', `${freeze}^2:${path}`]).ok, true);

  // (e) the content main carries is the content that was merged
  const merged = git(['rev-parse', `${freeze}^2:${path}`]).out;
  const landed = git(['rev-parse', `${freeze}:${path}`]).out;
  check('freeze (e) merged blob is the landed blob', landed !== '' && landed === merged, true);

  // Ordering. The measured target is the ACTUAL CHECKOUT, not a field in M0 — M0-v3 lives
  // inside the commit being measured, so a target read from it would describe its own
  // container. The measurement record writes the resulting sha down afterwards.
  const target = git(['rev-parse', 'HEAD']).out;
  console.log(`     measured target (HEAD) ${target.slice(0, 12)}`);
  check('freeze ordering: HEAD is a descendant of the freeze', git(['merge-base', '--is-ancestor', freeze, target]).ok, true);
} else {
  console.log('\nfreeze event: not declared by this manifest (M0 / M0-v2 predate E1-v3 §3)');
}

// 6. `D_program` replay — E1-v5 binding rule 5.
//
//    The candidate domain is a decision-rule input exactly as the digests are, so it is
//    recomputed from the frozen §3.2-§3.7 specification rather than trusted. The
//    sole-trailing-jumpdest assertion is §3.9's proof made checkable: it is what bounds each
//    frame at |Σ| + 1 dispatches and makes every jump forward.
if (m0.program_domain) {
  console.log('\nprogram domain — E1-v5 §3.7, binding rule 5');
  const domain = buildDomain();
  const hex = (u: Uint8Array): string => Buffer.from(u).toString('hex');
  const digest = sha256(domain.map((mem) => `${mem.index}\t${mem.label}\t${hex(mem.code)}`).join('\n'));

  check('|Σ| from Step 0 §1.1 + §1.2', SIGMA.length, m0.program_domain.sigma_size);
  check('plain blocks per program', PLAIN.length, m0.program_domain.plain_blocks);
  check('terminal variants', TERMINALS.length, m0.program_domain.terminal_variants);
  check('|D_program|', domain.length, m0.program_domain.member_count);
  check('d_program_digest', digest, m0.program_domain.d_program_digest);

  const violations = domain.filter((mem) => !soleTrailingJumpdest(mem.code));
  check(
    `§3.9 sole trailing jumpdest, all ${domain.length} members`,
    violations.map((mem) => mem.label),
    [],
  );
}

console.log(
  failures.length === 0
    ? '\nmanifest replay: M0 agrees with every primary source'
    : `\nmanifest replay: ${failures.length} DISAGREEMENT(S)\n\n${failures.join('\n\n')}`,
);
process.exit(failures.length === 0 ? 0 : 1);
