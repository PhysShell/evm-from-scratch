/**
 * Verifier shell — the front end of the ladder, §9.2 V1–V6.
 *
 * DECLARATION ONLY. No body exists yet, and none may run before E5-M0 is
 * committed (§14.3, §14.5).
 *
 * The frozen architecture (§9.3) puts ladder steps V7–V10 and the rule engine in
 * the kernel, which receives exactly (Certificate, FactResolver) and has no name
 * for the bundle, the map, the parser or the digest. Everything before that —
 * parsing the certificate (V1), schema_version (V2), ruleset_id (V3), conclusion
 * shape (V4), parsing the bundle (V5) and comparing the bundle digest (V6) —
 * lives here, in the only place allowed to hold a digest and a loader.
 *
 * That split is why BundleLoader returns (resolver, digest): the shell keeps the
 * digest for V6 and passes only the resolver inward.
 *
 * The shell is NOT exempt from independence: §11.2 S1–S4 apply to the verifier
 * as a whole, this module included. Only the §9.3 capability checks K1–K5 are
 * kernel-scoped.
 */
import type { Verdict } from "./verdict";

/**
 * Deterministic on identical input bytes (§9.1, §11.2 S3).
 * Returns the same two shapes as the kernel — there is no third outcome (§2.3).
 */
export declare function verifyCertificate(
  certificateBytes: Uint8Array,
  bundleBytes: Uint8Array
): Verdict;
