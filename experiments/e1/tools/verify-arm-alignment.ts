/**
 * Independent validation of the arm correspondence the branch search depends on.
 *
 * The search targets discovery arms by ORDINAL, so the identity of every witness and of the
 * stopping arm rests on the k-th arm of a file being the same arm in both instrumentations.
 *
 * `checkAlignment` compares per-file type SEQUENCES, and that is too weak to establish it: a
 * permutation among adjacent same-typed arms passes unchanged, and `src/jmp.ts` alone opens
 * `binary-expr, binary-expr, if, if`. Re-running the search does not help either, because the
 * rerun goes through the same matcher.
 *
 * This checks each arm on its own. It takes the in-memory `branchMap` position — which is a
 * generated-JS position — maps it back through the transpiler's source map, and compares the
 * result with the TypeScript position the discovery run recorded for that same ordinal. Every
 * arm must agree on type, line and column.
 *
 * Exit 0 = every arm agrees, and the ordinal correspondence is established rather than assumed.
 * Exit 1 = at least one does not, and no result that targets arms by ordinal may be relied on.
 */
import { readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { loadAll, armSourcePositions, validateAlignment } from './instrumented';

const E1 = join(__dirname, '..');

interface Discovery {
  arms: Record<string, { type: string; line: number | null; column: number | null }[]>;
}

async function main(): Promise<void> {
  const discovery: Discovery = JSON.parse(
    readFileSync(join(E1, 'records', 'step6a-uncovered-arms.json'), 'utf8'),
  );

  loadAll();
  const mapped = await armSourcePositions((p) => relative(E1, p));

  const { byPosition, bySibling, disagree } = validateAlignment(discovery.arms, mapped);

  const agree = byPosition + bySibling;
  console.log(`arm identity, one arm at a time, via the transpiler source map`);
  console.log(`  matched by source position          ${byPosition}`);
  console.log(`  positionless implicit-else arms,`);
  console.log(`  identified by a matched sibling      ${bySibling}`);
  console.log(`  disagree                             ${disagree.length}`);
  for (const d of disagree) console.log(`    ${d}`);

  if (disagree.length > 0) {
    console.log(
      `\nThe ordinal correspondence is NOT established. Any result that targets arms by\n` +
      `ordinal — every witness and every stop — is unsupported until this agrees.`,
    );
    process.exit(1);
  }
  console.log(`\nordinal correspondence established for all ${agree} arms`);
}

void main();
