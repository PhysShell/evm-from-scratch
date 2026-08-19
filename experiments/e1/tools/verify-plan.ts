/**
 * Verify a Jest run against the frozen local-test plan.
 *
 * An earlier version of this tool checked less than the record built on it claimed. It
 * compared executed IDs to the frozen list and counted passes and failures — but it had no
 * notion of which case IDs are level A and which are level B, so a COMPENSATING SWAP (one
 * level-A case failing while one level-B case passed) would have kept 166/47 intact and been
 * reported as correct. It also folded results into a Map keyed by title, silently collapsing
 * a duplicated case ID into one entry.
 *
 * What it now establishes:
 *
 *   1. executed IDs == the frozen 213, with no missing and no extra
 *   2. each frozen ID executed EXACTLY ONCE — no duplicates collapsed
 *   3. no status other than passed/failed — a skipped case is not a result
 *   4. passed IDs == the level-A set, failed IDs == the level-B set (with --expect-red)
 *   5. every failure is attributable to its own case, not to a suite that died first
 *
 * The level-A/level-B classification in (4) is DERIVED from the frozen Step 2 document —
 * §3.1 is level A, every other §3.x section is level B — and then amended by E1-v2/A1. It is
 * not a list written here by looking at a result. The Step 2 blob is itself pinned by sha in
 * the manifest and checked by `manifest-replay`, so the derivation's input is verified
 * upstream rather than trusted.
 *
 * Usage:  jest --json --outputFile=<f> ; ts-node tools/verify-plan.ts <f> [--expect-red]
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

interface JestReport {
  testResults: Array<{
    failureMessage?: string | null;
    assertionResults: Array<{ title: string; status: string; failureMessages?: string[] }>;
  }>;
}

interface Manifest {
  test_plan: { core_case_ids: string[] };
  amendment?: { id: string; postcondition: string; from_level: string; to_level: string };
}

const E1 = join(__dirname, '..');
const ROOT = join(E1, '..', '..');

/**
 * Amendment E1-v2/A1, held here as a literal for the same reason the freeze base is:
 * a manifest must not supply the criteria it is judged by. The manifest's declaration is
 * checked against this, never used in its place.
 */
const AMENDMENT = { id: 'E1-v2/A1', postcondition: 'SEM-RUN-4', from_level: 'A', to_level: 'B' };
const STEP2_PATH = 'docs/experiments/E1-step2-semantics-and-plan.md';

const reportPath = process.argv[2];
if (reportPath === undefined) {
  console.error('usage: verify-plan.ts <jest-json> [--expect-red]');
  process.exit(2);
}
const expectRed = process.argv.includes('--expect-red');

const report: JestReport = JSON.parse(readFileSync(reportPath, 'utf8'));
const manifestName = process.env['E1_MANIFEST'] ?? 'M0-v3-protocol.json';
const manifest: Manifest = JSON.parse(readFileSync(join(E1, 'manifest', manifestName), 'utf8'));

const problems: string[] = [];
const note = (s: string): void => {
  problems.push(s);
};

// ---------------------------------------------------------------------------
// Level classification, derived from the frozen Step 2 document.
// ---------------------------------------------------------------------------
function derivePostconditionLevels(): Map<string, 'A' | 'B'> {
  const doc = readFileSync(join(ROOT, STEP2_PATH), 'utf8');
  const levels = new Map<string, 'A' | 'B'>();
  let section = '';
  for (const line of doc.split('\n')) {
    const heading = /^###\s+3\.(\d+)/.exec(line);
    if (heading) section = `3.${heading[1]}`;
    const row = /^\|\s*`(SEM-[A-Z0-9-]+)`\s*\|/.exec(line);
    if (row && section !== '') {
      // §3.1 is the level-A table; every other §3.x section is level B.
      levels.set(row[1]!, section === '3.1' ? 'A' : 'B');
    }
  }
  return levels;
}

const levels = derivePostconditionLevels();
if (levels.size === 0) note(`could not derive any postcondition levels from ${STEP2_PATH}`);

// Amendment: the manifest's declaration must match the literal, then the literal is applied.
const declared = manifest.amendment;
if (declared === undefined) {
  note('manifest declares no amendment; E1-v2/A1 is required from M0-v2 onward');
} else if (
  declared.id !== AMENDMENT.id ||
  declared.postcondition !== AMENDMENT.postcondition ||
  declared.from_level !== AMENDMENT.from_level ||
  declared.to_level !== AMENDMENT.to_level
) {
  note(`manifest amendment ${JSON.stringify(declared)} does not match the frozen ${JSON.stringify(AMENDMENT)}`);
}
if (levels.get(AMENDMENT.postcondition) !== AMENDMENT.from_level) {
  note(
    `${AMENDMENT.postcondition} is filed under level ${levels.get(AMENDMENT.postcondition)} in Step 2, ` +
      `but amendment ${AMENDMENT.id} moves it from level ${AMENDMENT.from_level} — the amendment no longer applies`,
  );
}
levels.set(AMENDMENT.postcondition, AMENDMENT.to_level as 'A' | 'B');

/** `LT-SEM-DEC-2/PUSH1` -> `SEM-DEC-2`. */
const postconditionOf = (caseId: string): string => caseId.replace(/^LT-/, '').split('/')[0]!;

const frozen = manifest.test_plan.core_case_ids;
const frozenSet = new Set(frozen);
const levelA = new Set(frozen.filter((id) => levels.get(postconditionOf(id)) === 'A'));
const levelB = new Set(frozen.filter((id) => levels.get(postconditionOf(id)) === 'B'));
const unclassified = frozen.filter((id) => !levels.has(postconditionOf(id)));
if (unclassified.length) note(`${unclassified.length} frozen case ID(s) map to no Step 2 postcondition: ${unclassified.slice(0, 5).join(', ')}…`);

// ---------------------------------------------------------------------------
// The run itself. Results are kept as a LIST, so duplicates cannot collapse.
// ---------------------------------------------------------------------------
const results: Array<{ id: string; status: string; messages: string[] }> = [];
for (const suite of report.testResults) {
  for (const t of suite.assertionResults) {
    results.push({ id: t.title, status: t.status, messages: t.failureMessages ?? [] });
  }
}

const counts = new Map<string, number>();
for (const r of results) counts.set(r.id, (counts.get(r.id) ?? 0) + 1);
const duplicates = [...counts].filter(([, n]) => n > 1).map(([id, n]) => `${id} ×${n}`);
if (duplicates.length) note(`${duplicates.length} case ID(s) executed more than once: ${duplicates.slice(0, 5).join(', ')}…`);

const missing = frozen.filter((id) => !counts.has(id));
const extra = [...counts.keys()].filter((id) => !frozenSet.has(id));
if (missing.length) note(`${missing.length} frozen case ID(s) never executed: ${missing.slice(0, 5).join(', ')}…`);
if (extra.length) note(`${extra.length} executed test(s) are not in the frozen plan: ${extra.slice(0, 5).join(', ')}…`);

const otherStatus = results.filter((r) => r.status !== 'passed' && r.status !== 'failed');
if (otherStatus.length) note(`${otherStatus.length} case(s) neither passed nor failed (${[...new Set(otherStatus.map((r) => r.status))].join(', ')}) — a skipped case is not a result`);

// A suite that dies before running anything reports a failureMessage and no assertions,
// hiding how many cases it contained and why each would have failed.
const collapsed = report.testResults.filter((s) => s.failureMessage && s.assertionResults.length === 0);
if (collapsed.length) note(`${collapsed.length} suite(s) failed before executing any case — those failures are not attributable`);

const passed = new Set(results.filter((r) => r.status === 'passed').map((r) => r.id));
const failed = new Set(results.filter((r) => r.status === 'failed').map((r) => r.id));

const sameSet = (a: Set<string>, b: Set<string>): boolean =>
  a.size === b.size && [...a].every((x) => b.has(x));

console.log(`manifest          ${manifestName}`);
console.log(`frozen plan       ${frozen.length}   (level A ${levelA.size}, level B ${levelB.size}, derived from Step 2 §3 + ${AMENDMENT.id})`);
console.log(`executed          ${results.length}`);
console.log(`passed            ${passed.size}`);
console.log(`failed            ${failed.size}`);
console.log(`names match plan  ${missing.length === 0 && extra.length === 0}`);
console.log(`each executed 1×  ${duplicates.length === 0}`);
console.log(`attributable      ${collapsed.length === 0}`);

if (expectRed) {
  console.log(`passed == level A ${sameSet(passed, levelA)}`);
  console.log(`failed == level B ${sameSet(failed, levelB)}`);
  if (!sameSet(passed, levelA)) {
    const aFailing = [...levelA].filter((id) => !passed.has(id));
    const bPassing = [...passed].filter((id) => !levelA.has(id));
    if (aFailing.length) note(`level-A case(s) not passing: ${aFailing.slice(0, 8).join(', ')}`);
    if (bPassing.length) note(`level-B case(s) passing, which the step-4 red state forbids: ${bPassing.slice(0, 8).join(', ')}`);
  }
  if (!sameSet(failed, levelB)) {
    const unexpected = [...failed].filter((id) => !levelB.has(id));
    if (unexpected.length) note(`unexpected failure(s) outside level B: ${unexpected.slice(0, 8).join(', ')}`);
  }
  const silent = results.filter((r) => r.status === 'failed' && r.messages.length === 0);
  if (silent.length) note(`${silent.length} failure(s) carry no message`);
} else {
  console.log(`all green         ${failed.size === 0 && passed.size === frozen.length}`);
  if (failed.size !== 0) note(`${failed.size} case(s) failed: ${[...failed].slice(0, 8).join(', ')}`);
}

if (problems.length) {
  console.log('\nPROBLEMS\n  ' + problems.join('\n  '));
  process.exit(1);
}
console.log('\nthe realised suite is exactly the frozen plan, in the expected state');
