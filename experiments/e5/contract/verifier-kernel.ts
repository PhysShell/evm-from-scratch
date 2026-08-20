/**
 * VerifierKernel entry signature — §9.3.
 *
 * DECLARATION ONLY. No body exists yet, and none may run before E5-M0 is
 * committed (§14.3, §14.5).
 *
 * SCOPE: the kernel is ladder steps V7–V10 and the rule engine. Steps V1–V6 —
 * including the V6 bundle-digest comparison — belong to the shell
 * (./verifier-shell), which is why the loader returns a digest alongside the
 * resolver.
 *
 * K1 (§9.3, mechanical): the declared inputs are EXACTLY
 * (Certificate, FactResolver). The bundle type, the map type, the parser module
 * and the digest module do not appear among them. §3.3 puts it plainly: the
 * kernel "has no name for the bundle, the map, the parser or the digest" — so a
 * digest parameter is a breach of K1 even though it is only a string. An earlier
 * revision of this file took a third `bundleDigest` argument and was wrong.
 *
 * K2 (§9.3, mechanical): this module's TRANSITIVE dependency closure must not
 * contain bundle-loader, the bundle/map type, the parser, or the digest
 * implementation.
 */
import type { Certificate } from "./certificate";
import type { FactResolver } from "./fact-resolver";
import type { Verdict } from "./verdict";

/** Deterministic on identical inputs (§9.1). */
export declare function verify(certificate: Certificate, resolver: FactResolver): Verdict;
