/**
 * Certificate schema E5-CERT/v1 — transcription of preregistration §6.2, §6.3.
 *
 * Identity is the tuple (schema_version, ruleset_id, spec_revision,
 * source_revision, fact_bundle_digest, conclusion) — §6.3. Nothing here is
 * keyed on message text, labels, file paths or line spans (§5.1).
 */
import type { FactId, GitObjectSha } from "./facts";
import type { Proposition } from "./propositions";

/** sha256 hex — §5.5. */
export type Sha256Hex = string;

/** §6.2 — 1-based; "must be < this step's index" is checked at V9b, not typed. */
export type PremiseRef = { fact: FactId } | { step: number };

export interface ProofStep {
  rule_id: string;
  /** Order is significant; slots are positional. */
  premises: PremiseRef[];
  /** The producer's claim. NEVER authority — recomputed and compared at V9h. */
  derived: Proposition;
}

export interface Certificate {
  /** Not narrowed to a literal: V2 checks the value -> UNKNOWN_SCHEMA_VERSION. */
  schema_version: string;
  /** Not narrowed to a literal: V3 checks the value -> UNKNOWN_RULESET. */
  ruleset_id: string;
  spec_revision: GitObjectSha;
  source_revision: GitObjectSha;
  fact_bundle_digest: Sha256Hex;
  conclusion: Proposition;
  /** Ordered, non-empty. */
  steps: ProofStep[];
}
