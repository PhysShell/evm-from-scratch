/**
 * Verifier output vocabulary — §2.3, §9.4.
 *
 * Shared by the shell (V1–V6) and the kernel (V7–V10) so that neither needs to
 * import the other merely for a type.
 */

/** §9.4 — closed set. There is no OTHER and no UNKNOWN_ERROR. */
export type ReasonCode =
  | "MALFORMED_CERTIFICATE" | "UNKNOWN_SCHEMA_VERSION" | "UNKNOWN_RULESET"
  | "UNKNOWN_CONCLUSION_SHAPE" | "MALFORMED_BUNDLE" | "BUNDLE_DIGEST_MISMATCH"
  | "EMPTY_DERIVATION" | "UNKNOWN_RULE" | "PREMISE_ARITY_MISMATCH"
  | "PREMISE_NOT_FOUND" | "PREMISE_FORWARD_REFERENCE" | "FACT_ID_NOT_CONTENT_DERIVED"
  | "REVISION_MISMATCH" | "PREMISE_KIND_MISMATCH" | "PREMISE_IDENTITY_MISMATCH"
  | "RULE_PRECONDITION_UNSATISFIED" | "STEP_PROPOSITION_MISMATCH" | "CONCLUSION_MISMATCH";

/**
 * §2.3 — exactly two shapes. No ABSTAIN, no INDETERMINATE, no WARN.
 * Abstention is a right of the PRODUCER, which may decline to claim. A checker
 * handed a certificate has been asked a closed question and must answer it
 * deterministically on the bytes it was given.
 */
export type Verdict =
  | { verdict: "VALID" }
  | { verdict: "INVALID"; reason_code: ReasonCode; step_index?: number };
