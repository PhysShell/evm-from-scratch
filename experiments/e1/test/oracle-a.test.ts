/**
 * The level-A oracle slice — E1 Step 0 §1.4, Step 2 §10 step 3.
 *
 * This is the BASELINE CORRECTNESS ORACLE, not a local test. Its job is "is the baseline
 * correct", and it may never be used for coverage, mutation or local-detection evidence
 * (Step 0 §3.2.1). The 213 core local tests are a separate domain and arrive at step 4.
 *
 * The corpus is `evm.json`, authored upstream before this experiment existed. The case
 * indices are not recomputed here — they are read from the M0 manifest, so a drift between
 * what M0 froze and what this run measures shows up as a failure rather than as a quietly
 * different denominator.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from '@jest/globals';
import { run } from '../src/run';
import type { Frame } from '../src/domain';
import { CORPUS_PATH } from './support/paths';

interface Case {
  name: string;
  code: { asm: string; bin: string };
  expect: { stack?: string[]; success: boolean };
}

const corpus: Case[] = JSON.parse(readFileSync(CORPUS_PATH, 'utf8'));
const m0 = JSON.parse(
  readFileSync(join(__dirname, '..', 'manifest', 'M0-protocol.json'), 'utf8'),
) as { oracle_case_indices: { level_a: number[] } };

const LEVEL_A: number[] = m0.oracle_case_indices.level_a;

function hexToBytes(hex: string): Uint8Array {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = Number.parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return out;
}

function freshFrame(code: Uint8Array): Frame {
  return {
    code,
    pc: 0,
    stack: [],
    memory: new Uint8Array(0),
    address: 0n,
    caller: 0n,
    static: false,
    storage_owner: 0n,
    returndata: new Uint8Array(0),
  };
}

describe('level-A oracle slice', () => {
  it('M0 froze exactly 49 level-A cases', () => {
    expect(LEVEL_A).toHaveLength(49);
  });

  it.each(LEVEL_A.map((index) => [index, corpus[index - 1]!.name] as const))(
    'case #%i %s',
    (index) => {
      const testCase = corpus[index - 1]!;
      const result = run(freshFrame(hexToBytes(testCase.code.bin)));

      // `evm.json` reports the stack top-first; `Frame.stack` is bottom-first.
      const expectedStack = (testCase.expect.stack ?? []).map((v) => BigInt(v)).reverse();

      expect(result.success).toBe(testCase.expect.success);
      expect(result.stack).toEqual(expectedStack);
    },
  );
});
