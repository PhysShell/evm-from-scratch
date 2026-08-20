/**
 * In-process istanbul instrumentation of `src/`, for the §8.2.2 branch search.
 *
 * The search has to answer "does THIS candidate cover THAT arm", one candidate at a time.
 * Jest's coverage answers it for a whole suite, so it cannot be used here. This loads the
 * production modules through `istanbul-lib-instrument` — the same instrumenter jest's
 * coverage stack is built on, so both enumerate the same arms in the same order.
 *
 * Their POSITIONS do not correspond: this instruments transpiled JavaScript while jest
 * reports TypeScript. Arms are therefore matched by order, and `checkAlignment` verifies that
 * correspondence rather than assuming it.
 *
 * Production code is not modified: it is transpiled and instrumented in memory.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { createInstrumenter } from 'istanbul-lib-instrument';
import * as ts from 'typescript';

const SRC = join(__dirname, '..', 'src');

export interface Coverage {
  path: string;
  branchMap: Record<string, { type: string; loc: { start: { line: number; column: number } }; locations: { start: { line: number; column: number } }[] }>;
  b: Record<string, number[]>;
}

const instrumenter = createInstrumenter({ coverageVariable: '__e1_coverage__', esModules: false });
const registry = new Map<string, Record<string, unknown>>();

/** Minimal CommonJS loader over `src/`. The tree has no external imports. */
function load(name: string): Record<string, unknown> {
  const key = name.replace(/^\.\//, '').replace(/\.ts$/, '');
  const cached = registry.get(key);
  if (cached) return cached;

  const file = join(SRC, `${key}.ts`);
  const source = readFileSync(file, 'utf8');
  const out = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      inlineSourceMap: true,
      inlineSources: true,
    },
    fileName: file,
  });
  // The map is passed because istanbul stores it in the coverage object, where a consumer
  // that wants source positions can use it. It does NOT rewrite branchMap positions, so the
  // positions here remain generated-JS positions — which is why arms are aligned to the
  // discovery run by ORDER (`armsByFile` / `checkAlignment`) and not by position.
  const inputSourceMap = out.sourceMapText === undefined
    ? undefined
    : (JSON.parse(out.sourceMapText) as Record<string, unknown>);
  if (inputSourceMap) inputSourceMap['sources'] = [file];
  const instrumented = instrumenter.instrumentSync(out.outputText, file, inputSourceMap as never);

  const module = { exports: {} as Record<string, unknown> };
  registry.set(key, module.exports);
  const fn = new Function('exports', 'require', 'module', '__filename', '__dirname', instrumented);
  fn(module.exports, (spec: string) => load(spec), module, file, SRC);
  registry.set(key, module.exports);
  return module.exports;
}

/** Load every unit, so every arm exists in the coverage object before the search starts. */
export function loadAll(): Record<string, Record<string, unknown>> {
  const out: Record<string, Record<string, unknown>> = {};
  for (const f of readdirSync(SRC).filter((f) => f.endsWith('.ts')).sort()) {
    out[f.replace(/\.ts$/, '')] = load(f);
  }
  return out;
}

const coverageVar = (): Record<string, Coverage> =>
  ((globalThis as unknown as Record<string, unknown>)['__e1_coverage__'] ?? {}) as Record<string, Coverage>;

/**
 * Ordered arms per file: `{ key, type }` in enumeration order.
 *
 * Positions cannot be compared with the discovery run's. This module instruments TRANSPILED
 * JavaScript, so its `branchMap` carries generated-JS lines, while jest reports TypeScript
 * lines — istanbul stores the source map for a later remap rather than rewriting positions.
 *
 * What does correspond is the ORDER: both are istanbul walking the same program, so the k-th
 * arm of a file is the same arm in both. The discovery extractor records that ordinal, and
 * `checkAlignment` verifies the correspondence instead of assuming it.
 */
export function armsByFile(rootRelative: (p: string) => string): Map<string, { key: string; type: string }[]> {
  const out = new Map<string, { key: string; type: string }[]>();
  for (const [path, cov] of Object.entries(coverageVar())) {
    const arms: { key: string; type: string }[] = [];
    for (const [id, counts] of Object.entries(cov.b)) {
      const meta = cov.branchMap[id]!;
      counts.forEach((_, k) => arms.push({ key: `${path}#${id}#${k}`, type: meta.type }));
    }
    out.set(rootRelative(path), arms);
  }
  return out;
}

/**
 * The alignment is only sound if both instrumentations enumerate the same arms in the same
 * order. That is checkable: compare the per-file type sequences. Returns the files that
 * disagree — an empty list is the licence to use ordinals.
 */
export function checkAlignment(
  mine: Map<string, { key: string; type: string }[]>,
  theirs: Map<string, string[]>,
): string[] {
  const bad: string[] = [];
  for (const [file, types] of theirs) {
    const ours = mine.get(file);
    if (!ours || ours.length !== types.length || ours.some((a, i) => a.type !== types[i])) bad.push(file);
  }
  return bad;
}

/** Snapshot of every arm's hit count, for before/after comparison around one candidate. */
export function snapshot(): Map<string, number> {
  const m = new Map<string, number>();
  for (const [path, cov] of Object.entries(coverageVar())) {
    for (const [id, counts] of Object.entries(cov.b)) {
      counts.forEach((c, k) => m.set(`${path}#${id}#${k}`, c));
    }
  }
  return m;
}

/** Arms whose counter moved between the two snapshots — what this candidate covered. */
export function covered(before: Map<string, number>, after: Map<string, number>): Set<string> {
  const out = new Set<string>();
  for (const [key, value] of after) {
    if (value > (before.get(key) ?? 0)) out.add(key);
  }
  return out;
}
