/**
 * Runtime unit loading, so a not-yet-built unit fails ATTRIBUTABLY.
 *
 * At Step 2 §10 step 4 the frozen plan's 47 level-B tests must be red because the units do
 * not exist until step 5. Written with static `import`, that would be a TypeScript
 * resolution error: Jest would refuse to run the file at all, and the evidence would read
 * "suite failed to compile" instead of naming which 47 case IDs failed and why. A reader
 * auditing the red state would then have to take the count on trust.
 *
 * Loading at test-execution time keeps every case ID individually reported. It also costs
 * nothing at step 5: once the module exists, `loadUnit` returns it and the same frozen test
 * turns green without being touched.
 *
 * This is NOT a level-B stub. Nothing here supplies behaviour — it only converts a missing
 * module into a legible failure.
 */
export function loadUnit<T>(moduleName: string): T {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    return require(`../../src/${moduleName}`) as T;
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    throw new Error(
      `unit src/${moduleName}.ts is not implemented — it arrives at Step 2 §10 step 5. ` +
        `Under step 4 this failure is the expected, recorded state. (${reason})`,
    );
  }
}
