/**
 * BundleLoader exported surface — §3.3, §9.3.
 *
 * DECLARATION ONLY. No body exists yet, and none may run before E5-M0 is
 * committed (§14.3, §14.5).
 *
 * This is the ONLY module that ever holds the fact bundle. It does exactly
 * three things and hands the kernel none of them:
 *
 *   1. parses the bundle bytes into a PRIVATE fact_id -> Fact map
 *      (a duplicate fact_id key is a parse failure — V5, MALFORMED_BUNDLE);
 *   2. computes the bundle digest over the canonical serialization (§5.5);
 *   3. constructs a FactResolver over that private map.
 *
 * K5 (§9.3, mechanical): this module exports EXACTLY ONE symbol, with exactly
 * this signature, and no other operation over the map escapes it.
 *
 * This module is deliberately NOT imported by verifier-kernel.ts (K2). It is
 * also the one residual review obligation in the whole design (§9.3, §17.2):
 * K1-K5 make the kernel structurally incapable of enumerating the bundle, but
 * nothing mechanical proves that `load`'s body computes the digest it claims.
 * That is one function with one signature and no other job — a residue, not an
 * elimination. Closing it fully would need a verified toolchain, which E5 does
 * not have and does not claim.
 */
import type { FactResolver } from "./fact-resolver";

export interface LoadedBundle {
  resolver: FactResolver;
  /** sha256(JCS(bundle)) — §5.5, lowercase hex. */
  digest: string;
}

export declare function load(bytes: Uint8Array): LoadedBundle;
