/**
 * Proposition shapes — transcription of preregistration §6.1, closed set.
 * Propositions are the ONLY things a step may derive and the ONLY things a
 * certificate may declare as its conclusion. There is no free-text conclusion.
 */
import type { BindingExpr, FrameField, GitObjectSha, SiteId } from "./facts";

/** P1 */
export interface SeamFieldBoundAs {
  shape: "SEAM_FIELD_BOUND_AS";
  source_revision: GitObjectSha;
  site: SiteId;
  field: FrameField;
  binding: BindingExpr;
}

/** P2 — reachable only through R2, under a completeness witness (§3.2). */
export interface SeamFieldNotBound {
  shape: "SEAM_FIELD_NOT_BOUND";
  source_revision: GitObjectSha;
  spec_revision: GitObjectSha;
  site: SiteId;
  field: FrameField;
}

/** P3 */
export interface SeamFieldMisbound {
  shape: "SEAM_FIELD_MISBOUND";
  source_revision: GitObjectSha;
  spec_revision: GitObjectSha;
  site: SiteId;
  field: FrameField;
  required: BindingExpr;
  actual: BindingExpr;
}

/** P4 — E5's primary claim shape. */
export interface BoundaryDefectPresent {
  shape: "BOUNDARY_DEFECT_PRESENT";
  source_revision: GitObjectSha;
  spec_revision: GitObjectSha;
  site: SiteId;
  field: FrameField;
  kind: "ABSENCE" | "MISBINDING";
}

export type Proposition =
  | SeamFieldBoundAs
  | SeamFieldNotBound
  | SeamFieldMisbound
  | BoundaryDefectPresent;
