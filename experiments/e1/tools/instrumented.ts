/**
 * In-process istanbul instrumentation of `src/`, for the §8.2.2 branch search.
 *
 * The search has to answer "does THIS candidate cover THAT arm", one candidate at a time.
 * Jest's coverage answers it for a whole suite, so it cannot be used here. This loads the
 * production modules through `istanbul-lib-instrument` — the same instrumenter jest's
 * coverage stack is built on, so both enumerate the same arms in the same order.
 *
 * Their POSITIONS do not correspond in the branchMap: this instruments transpiled JavaScript
 * while jest reports TypeScript. Arms are matched by ordinal, and `validateAlignment` below
 * establishes that correspondence ARM BY ARM by mapping each position back through the
 * transpiler's source map — a per-file comparison of istanbul `type` sequences was tried
 * first and rejected, because a permutation among adjacent same-typed arms passes it.
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
/** Raw source map per file, kept so arm positions can be mapped back to TypeScript. */
const sourceMaps = new Map<string, string>();

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
      sourceMap: true,
    },
    fileName: file,
  });
  // The map is passed because istanbul stores it in the coverage object, where a consumer
  // that wants source positions can use it. It does NOT rewrite branchMap positions, so the
  // positions in `branchMap` remain generated-JS positions. The map is therefore ALSO kept in
  // `sourceMaps` above, because that is what `armSourcePositions` reads: arms are targeted by
  // ordinal, and `validateAlignment` establishes that ordinal arm by arm by mapping each
  // generated-JS position back to TypeScript through this map and comparing it with the
  // position the discovery run recorded for the same ordinal.
  const inputSourceMap = out.sourceMapText === undefined
    ? undefined
    : (JSON.parse(out.sourceMapText) as Record<string, unknown>);
  if (inputSourceMap) {
    inputSourceMap['sources'] = [file];
    sourceMaps.set(file, JSON.stringify(inputSourceMap));
  }
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

/**
 * Map every instrumented arm's generated-JS position back to its TypeScript position.
 *
 * This is the independent check that the ordinal correspondence is real. Its rejected
 * predecessor — since deleted — compared per-file sequences of istanbul `type` strings, which
 * a permutation among adjacent same-typed arms would pass; `jmp.ts` alone opens
 * `binary-expr, binary-expr, if, if`, so that was not a hypothetical. Mapping each arm's own
 * position through the source map and comparing it with the position the discovery run
 * recorded for the same ordinal establishes arm identity one arm at a time instead.
 */
export async function armSourcePositions(
  rootRelative: (p: string) => string,
): Promise<Map<string, { key: string; type: string; line: number; column: number }[]>> {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { SourceMapConsumer } = require('source-map') as {
    SourceMapConsumer: new (m: string) => Promise<{
      originalPositionFor(p: { line: number; column: number }): { line: number | null; column: number | null };
      destroy?: () => void;
    }>;
  };

  const out = new Map<string, { key: string; type: string; line: number; column: number }[]>();
  for (const [path, cov] of Object.entries(coverageVar())) {
    const raw = sourceMaps.get(path);
    if (raw === undefined) continue;
    const consumer = await new SourceMapConsumer(raw);
    const arms: { key: string; type: string; line: number; column: number }[] = [];
    for (const [id, counts] of Object.entries(cov.b)) {
      const meta = cov.branchMap[id]!;
      counts.forEach((_, k) => {
        const loc = meta.locations?.[k] ?? meta.loc;
        const original = consumer.originalPositionFor({ line: loc.start.line, column: loc.start.column });
        arms.push({
          key: `${path}#${id}#${k}`,
          type: meta.type,
          line: original.line ?? -1,
          column: original.column ?? -1,
        });
      });
    }
    consumer.destroy?.();
    out.set(rootRelative(path), arms);
  }
  return out;
}

export interface AlignmentReport {
  byPosition: number;
  bySibling: number;
  disagree: string[];
}

/**
 * Establish, arm by arm, that the k-th arm of a file is the same arm in both instrumentations.
 *
 * Every result the search produces targets arms by ordinal, so nothing it reports means
 * anything unless this holds. Two ways an arm can be identified, counted separately so a
 * record can never claim more positional evidence than exists:
 *
 *   by position   the mapped TypeScript position equals the one the discovery run recorded
 *   by sibling    istanbul gives an `if`'s implicit else NO location on either side, so
 *                 position cannot identify it. It is arm #1 of a branch entry whose arm #0
 *                 sits immediately before it and did match by position, which determines it.
 */
export function validateAlignment(
  discoveryArms: Record<string, { type: string; line: number | null; column: number | null }[]>,
  mapped: Map<string, { key: string; type: string; line: number; column: number }[]>,
): AlignmentReport {
  const positionless = (p: { line: number | null }): boolean =>
    p.line === null || p.line === undefined || p.line < 0;

  let byPosition = 0;
  let bySibling = 0;
  const disagree: string[] = [];

  for (const [file, theirs] of Object.entries(discoveryArms)) {
    const mine = mapped.get(file) ?? [];
    for (let i = 0; i < Math.max(mine.length, theirs.length); i++) {
      const a = mine[i];
      const b = theirs[i];
      if (a === undefined || b === undefined || a.type !== b.type) {
        disagree.push(
          `${file}#${i}  instrumented=${a ? `${a.type}@${a.line}:${a.column}` : '(absent)'}` +
          `  discovery=${b ? `${b.type}@${b.line}:${b.column}` : '(absent)'}`,
        );
        continue;
      }
      if (!positionless(a) && !positionless(b)) {
        if (a.line === b.line && a.column === b.column) byPosition++;
        else disagree.push(`${file}#${i}  instrumented=${a.type}@${a.line}:${a.column}  discovery=${b.type}@${b.line}:${b.column}`);
        continue;
      }
      const pm = mine[i - 1];
      const pt = theirs[i - 1];
      const siblingMatched = i > 0
        && pm !== undefined && pt !== undefined
        && pm.type === 'if' && pt.type === 'if'
        && !positionless(pm) && !positionless(pt)
        && pm.line === pt.line && pm.column === pt.column;
      if (siblingMatched && positionless(a) && positionless(b)) bySibling++;
      else disagree.push(`${file}#${i}  positionless ${a.type} arm without a positionally matched sibling`);
    }
  }
  return { byPosition, bySibling, disagree };
}
