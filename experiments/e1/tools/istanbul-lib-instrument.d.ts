/** Minimal shim: the package ships no types and adding @types would move the frozen toolchain. */
declare module 'istanbul-lib-instrument' {
  export function createInstrumenter(opts?: Record<string, unknown>): {
    instrumentSync(code: string, filename: string, inputSourceMap?: unknown): string;
  };
}
