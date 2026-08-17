/**
 * The level-B oracle slice — E1 Step 0 §1.4, Step 2 §10 step 5.
 *
 * 65 cases: the 71 level-B in-subset cases less the 6 composition witnesses, which are
 * excluded from the oracle's green-suite requirement so that "baseline correct" and "defect
 * detected" are never the same measurement.
 *
 * This is the BASELINE CORRECTNESS ORACLE. It answers "is the baseline correct" and nothing
 * else. Turning green does not convert it into coverage, mutation or local-detection
 * evidence — Step 0 §3.2.1 bars that, and a suite does not acquire new powers by passing.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from '@jest/globals';
import { run } from '../src/run';
import { rootFrame } from '../src/entry';
import type { World } from '../src/domain';
import { CORPUS_PATH } from './support/paths';

interface Case {
  name: string;
  code: { asm: string; bin: string };
  state?: Record<string, { code?: { bin?: string } }>;
  tx?: { to?: string; from?: string };
  expect: { stack?: string[]; success: boolean };
}

const corpus: Case[] = JSON.parse(readFileSync(CORPUS_PATH, 'utf8'));
const MANIFEST = process.env['E1_MANIFEST'] ?? 'M0-v3-protocol.json';
const m0 = JSON.parse(
  readFileSync(join(__dirname, '..', 'manifest', MANIFEST), 'utf8'),
) as { oracle_case_indices: { level_b_oracle: number[] } };

const LEVEL_B: number[] = m0.oracle_case_indices.level_b_oracle;

function hexToBytes(hex: string): Uint8Array {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = Number.parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return out;
}

function buildWorld(testCase: Case): World {
  const world: World = new Map();
  for (const [address, account] of Object.entries(testCase.state ?? {})) {
    world.set(BigInt(address), {
      code: hexToBytes(account.code?.bin ?? ''),
      storage: new Map(),
    });
  }
  return world;
}

describe('level-B oracle slice', () => {
  it('M0 froze exactly 65 level-B oracle cases', () => {
    expect(LEVEL_B).toHaveLength(65);
  });

  it.each(LEVEL_B.map((index) => [index, corpus[index - 1]!.name] as const))(
    'case #%i %s',
    (index) => {
      const testCase = corpus[index - 1]!;
      const world = buildWorld(testCase);
      const tx = {
        ...(testCase.tx?.to !== undefined ? { to: BigInt(testCase.tx.to) } : {}),
        ...(testCase.tx?.from !== undefined ? { from: BigInt(testCase.tx.from) } : {}),
      };
      const frame = rootFrame(hexToBytes(testCase.code.bin), tx);
      // The executing account's own code is also part of the world it may be called back into.
      if (!world.has(frame.address)) {
        world.set(frame.address, { code: frame.code, storage: new Map() });
      }

      const result = run(frame, world);
      const expectedStack = (testCase.expect.stack ?? []).map((v) => BigInt(v)).reverse();

      expect(result.success).toBe(testCase.expect.success);
      expect(result.stack).toEqual(expectedStack);
    },
  );
});
