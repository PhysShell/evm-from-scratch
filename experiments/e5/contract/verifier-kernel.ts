/**
 * VerifierKernel entry signature — §9.1, §9.2, §9.3.
 *
 * DECLARATION ONLY. No body exists yet, and none may run before E5-M0 is
 * committed (§14.3, §14.5).
 *
 * K1 (§9.3, mechanical): the kernel's declared inputs are EXACTLY
 * (Certificate, FactResolver). The bundle type, the map type, the parser module
 * and the digest module do not appear among them.
 *
 * K2 (§9.3, mechanical): this module's transitive dependency closure must not
 * contain bundle-loader.ts, the bundle/map type, the parser, or the digest
 * implementation. It imports ./certificate and ./fact-resolver and nothing else.
 *
 * The verifier's output vocabulary is exactly two shapes (§2.3). There is no
 * ABSTAIN, no INDETERMINATE, no WARN: abstention is a right of the PRODUCER,
 * which may decline to claim. A checker handed a certificate has been asked a
 * closed question and must answer it deterministically on the bytes it was given.
 */
import type { Certificate } from "./certificate";
import type { FactResolver } from "./fact-resolver";

/** §9.4 — closed set. There is no OTHER and no UNKNOWN_ERROR. */
export type ReasonCode =
  | "MALFORMED_CERTIFICATE" | "UNKNOWN_SCHEMA_VERSION" | "UNKNOWN_RULESET"
  | "UNKNOWN_CONCLUSION_SHAPE" | "MALFORMED_BUNDLE" | "BUNDLE_DIGEST_MISMATCH"
  | "EMPTY_DERIVATION" | "UNKNOWN_RULE" | "PREMISE_ARITY_MISMATCH"
  | "PREMISE_NOT_FOUND" | "PREMISE_FORWARD_REFERENCE" | "FACT_ID_NOT_CONTENT_DERIVED"
  | "REVISION_MISMATCH" | "PREMISE_KIND_MISMATCH" | "PREMISE_IDENTITY_MISMATCH"
  | "RULE_PRECONDITION_UNSATISFIED" | "STEP_PROPOSITION_MISMATCH" | "CONCLUSION_MISMATCH";

export type Verdict =
  | { verdict: "VALID" }
  | { verdict: "INVALID"; reason_code: ReasonCode; step_index?: number };

/**
 * Deterministic on identical input bytes (§9.1). The digest is passed in
 * because the kernel may not compute it: that is the loader's job (§3.3).
 */
export declare function verify(
  certificate: Certificate,
  resolver: FactResolver,
  bundleDigest: string
): Verdict;
