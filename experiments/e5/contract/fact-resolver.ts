/**
 * The capability boundary of §9.3 / §3.3.
 *
 * This interface is the ENTIRE surface through which the verifier kernel can
 * reach fact data. It is opaque by construction: it is not a collection, it
 * cannot be enumerated, counted, filtered or searched, and it can never return
 * more than one Fact.
 *
 * That is what makes §3.1 structural rather than promised. The kernel cannot
 * observe that something is missing and conclude anything from it, for the same
 * reason a program cannot read a file it has no handle to: it is never given one.
 * The only thing an unresolvable id can produce is INVALID(PREMISE_NOT_FOUND).
 *
 * K3 (§9.3, mechanical): this interface declares EXACTLY ONE operation and
 * exposes no iterator, no length or count, no key set, no collection-valued
 * member, and no operation returning more than one Fact. Adding any such member
 * is a breach of the frozen capability boundary and is adjudicated as
 * FAIL_SOUNDNESS via A12b (§12.2 G3) — not as a convenience.
 */
import type { Fact, FactId } from "./facts";

export const NOT_FOUND = Symbol("NOT_FOUND");
export type NotFound = typeof NOT_FOUND;

export interface FactResolver {
  Resolve(id: FactId): Fact | NotFound;
}
