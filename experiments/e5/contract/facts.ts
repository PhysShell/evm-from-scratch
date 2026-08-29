/**
 * E5 fact data types — transcription of preregistration §5.1, §5.2, §5.3.
 * Pure data. No behaviour, no collection type, no bundle.
 *
 * Authority: docs/experiments/E5-finding-certificates-preregistration.md
 * at blob b4f78b572a3de5cdd446524e32f9ec85a264ea5c.
 */

/** sha256 hex of JCS(fact without its fact_id) — §5.5. */
export type FactId = string;

/** A git object name (SHA-1, 40 hex): commit sha or blob sha — §5.1. */
export type GitObjectSha = string;

/** §5.1 — the three U-CALL construction sites, and only those. */
export type SiteId = "U-CALL/CALL" | "U-CALL/STATICCALL" | "U-CALL/DELEGATECALL";

/** §5.2, in Step 2 §2 field order. */
export type FrameField =
  | "code" | "pc" | "stack" | "memory"
  | "address" | "caller" | "static" | "storage_owner" | "returndata";

/**
 * §5.3. Only FRAME_CONSTRUCTION is in RECOGNISED_SCOPE; ROOT_FRAME_CONSTRUCTION
 * must be WELL-FORMED so adversarial case A13c fails at the R2 precondition
 * rather than at parse time. See README transcription decision T2.
 */
export type Scope = "FRAME_CONSTRUCTION" | "ROOT_FRAME_CONSTRUCTION";

/** §5.2 — closed algebra. UNMODELLED is mandatory honesty, never a fallback. */
export type BindingExpr =
  | { node: "CALLEE_ADDRESS" }
  | { node: "CURRENT_FRAME"; field: FrameField }
  | { node: "CODE_AT"; of: BindingExpr }
  | { node: "LITERAL_BOOL"; value: boolean }
  | { node: "ZERO" }
  | { node: "EMPTY" }
  | { node: "UNMODELLED"; token: string };

/** Provenance only. §5.1 forbids any rule or constraint from reading it. */
export interface Span {
  start_line: number;
  start_column: number;
  end_line: number;
  end_column: number;
}

export interface SpecRequiredBinding {
  fact_id: FactId;
  kind: "SPEC_REQUIRED_BINDING";
  spec_revision: GitObjectSha;
  site: SiteId;
  field: FrameField;
  postcondition_id: string;
  required: BindingExpr;
}

export interface SeamSite {
  fact_id: FactId;
  kind: "SEAM_SITE";
  source_revision: GitObjectSha;
  site: SiteId;
  source_file: string;
  span: Span;
}

export interface ConstructionWrite {
  fact_id: FactId;
  kind: "CONSTRUCTION_WRITE";
  source_revision: GitObjectSha;
  site: SiteId;
  field: FrameField;
  bound_to: BindingExpr;
}

/**
 * The completeness witness of §3.2. `recorded_fields` is the explicit closed
 * domain over which R2's negation is taken — never the bundle.
 * §5.6: the extractor must not emit this for a site it did not enumerate exhaustively.
 */
export interface ConstructionWritesComplete {
  fact_id: FactId;
  kind: "CONSTRUCTION_WRITES_COMPLETE";
  source_revision: GitObjectSha;
  site: SiteId;
  scope: Scope;
  recorded_fields: FrameField[];
}

export interface FrameFieldDefault {
  fact_id: FactId;
  kind: "FRAME_FIELD_DEFAULT";
  source_revision: GitObjectSha;
  field: FrameField;
  default: BindingExpr;
}

/**
 * §5.3 — closed set. There is NO fact kind meaning "field f is not written",
 * and no rule may introduce one. The only route to a negative proposition is
 * R2, through a completeness witness.
 */
export type Fact =
  | SpecRequiredBinding
  | SeamSite
  | ConstructionWrite
  | ConstructionWritesComplete
  | FrameFieldDefault;
