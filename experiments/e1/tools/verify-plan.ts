/**
 * Verify a Jest run against the frozen local-test plan.
 *
 * Answers three questions the eye cannot answer from a summary line:
 *
 *   1. did the suite execute EXACTLY the frozen case IDs — no missing, no extra?
 *   2. which of them passed and which failed?
 *   3. is every failure attributable to a case ID, or did a suite fail to compile and take
 *      its cases down with it?
 *
 * (3) is the one that matters at Step 2 §10 step 4. The frozen plan requires the 47 level-B
 * cases to be red; "test suite failed to compile" would also be red, while proving nothing
 * about how many cases there were or why each failed.
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

const reportPath = process.argv[2];
if (reportPath === undefined) {
  console.error('usage: verify-plan.ts <jest-json> [--expect-red]');
  process.exit(2);
}
const expectRed = process.argv.includes('--expect-red');

const report: JestReport = JSON.parse(readFileSync(reportPath, 'utf8'));
const manifestName = process.env['E1_MANIFEST'] ?? 'M0-v3-protocol.json';
const manifest = JSON.parse(
  readFileSync(join(__dirname, '..', 'manifest', manifestName), 'utf8'),
) as { test_plan: { core_case_ids: string[] } };

const frozen = new Set(manifest.test_plan.core_case_ids);
const executed = new Map<string, string>();
for (const suite of report.testResults) {
  for (const t of suite.assertionResults) executed.set(t.title, t.status);
}

const problems: string[] = [];
const missing = [...frozen].filter((id) => !executed.has(id));
const extra = [...executed.keys()].filter((id) => !frozen.has(id));
if (missing.length) problems.push(`${missing.length} frozen case ID(s) never executed: ${missing.slice(0, 5).join(', ')}…`);
if (extra.length) problems.push(`${extra.length} executed test(s) are not in the frozen plan: ${extra.slice(0, 5).join(', ')}…`);

// A suite that dies before running anything reports a failureMessage and no assertions. That
// is exactly the shape this tool exists to reject: it hides how many cases existed.
const collapsed = report.testResults.filter((s) => s.failureMessage && s.assertionResults.length === 0);
if (collapsed.length) problems.push(`${collapsed.length} suite(s) failed before executing any case — failures are not attributable`);

const passed = [...executed].filter(([, s]) => s === 'passed').map(([id]) => id);
const failed = [...executed].filter(([, s]) => s === 'failed').map(([id]) => id);

console.log(`frozen plan      ${frozen.size}`);
console.log(`executed         ${executed.size}`);
console.log(`passed           ${passed.length}`);
console.log(`failed           ${failed.length}`);
console.log(`names match plan ${missing.length === 0 && extra.length === 0}`);
console.log(`attributable     ${collapsed.length === 0}`);

if (expectRed) {
  // Every failure must name its own case and carry a reason, not a compile error.
  const unattributed = report.testResults.flatMap((s) =>
    s.assertionResults
      .filter((t) => t.status === 'failed' && (t.failureMessages ?? []).length === 0)
      .map((t) => t.title),
  );
  if (unattributed.length) problems.push(`${unattributed.length} failure(s) carry no message`);
}

if (problems.length) {
  console.log('\nPROBLEMS\n  ' + problems.join('\n  '));
  process.exit(1);
}
console.log('\nthe realised suite is exactly the frozen plan');
