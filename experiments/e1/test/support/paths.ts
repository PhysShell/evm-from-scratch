/**
 * Path resolution that survives the Stryker sandbox.
 *
 * Stryker copies the project into `.stryker-tmp/sandbox-XXXX/` and runs tests from there,
 * so a relative hop to the repository root resolves somewhere else entirely. Walking up
 * until the corpus appears works from both the real tree and the sandbox, and — unlike
 * copying `evm.json` into this directory — keeps exactly one corpus with no drift.
 */
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';

export function findUp(filename: string, from: string = __dirname): string {
  let dir = from;
  for (;;) {
    const candidate = join(dir, filename);
    if (existsSync(candidate)) return candidate;
    const parent = dirname(dir);
    if (parent === dir) {
      throw new Error(`could not locate ${filename} above ${from}`);
    }
    dir = parent;
  }
}

export const CORPUS_PATH = findUp('evm.json');
