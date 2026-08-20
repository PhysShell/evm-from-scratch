# E5 — bootstrap artifacts

**Status: pre-`E5-M0`. Nothing here has been executed, and the extractor,
producer and verifier bodies do not exist.**

The authority for everything in this directory is
[`docs/experiments/E5-finding-certificates-preregistration.md`](../../docs/experiments/E5-finding-certificates-preregistration.md),
frozen at merge `bf6506daceca0c152b234993bc63d1f7b9a5a5ae`, blob
`b4f78b572a3de5cdd446524e32f9ec85a264ea5c`. These files are a **mechanical
transcription** of it. They may not add, remove, widen or improve anything. A
disagreement between a file here and the document is a defect *here*.

`tools/check-transcription.py` re-derives the frozen tables from the document
and diffs them against these artifacts. Run it before trusting any of this.

## Why these files exist before `E5-M0`

`E5-M0` (§14.3) must record a digest over the ruleset artifact, the
`E5-FACTS/v1` and `E5-CERT/v1` schema digests, and the `FactResolver` interface
declaration and `BundleLoader` exported signature "by reference and digest". It
cannot be the first file: the things it digests must exist first.

The manifests are **append-only** — an earlier stage is never rewritten — so
`E5-M0` must not be committed until these artifacts are final. If review changes
a schema, `M0`'s digests change, and rewriting a committed `M0` would be a
protocol violation rather than an edit.

## What is here

| path | transcribed from |
|---|---|
| `schema/E5-FACTS-v1.schema.json` | §5.2, §5.3, §5.5 |
| `schema/E5-CERT-v1.schema.json` | §6.1, §6.2, §6.3 |
| `ruleset/E5-RULES-v1.json` | §6.1, §7.2, §7.4, §9.4 |
| `spec-facts/E5-SPEC-FACTS-v1.json` | §5.4 — the 27 frozen spec facts |
| `contract/facts.ts`, `propositions.ts`, `certificate.ts` | §5, §6 — data types |
| `contract/fact-resolver.ts` | §3.3, §9.3 — the capability boundary |
| `contract/bundle-loader.ts` | §3.3, §9.3 — exported surface only |
| `contract/verifier-kernel.ts` | §9.1–§9.4 — entry signature only |

`contract/*.ts` are **declarations, no bodies**. That is deliberate: `M0` then
pins the *contract* rather than the *code*, so writing the bodies later does not
invalidate `M0`.

## What is deliberately NOT here

- no extractor, producer or verifier body;
- no fixtures, no bundles, no certificates;
- no `E5-M0`, and no `E5-M1`.

**No `E5-M1` will be created while `E5_INPUT_SET` is empty.** Every committed
`E5-M1` is a permanent element of the total run chain (§14.3). Opening a first
run purely to record `BLOCKED_NO_ELIGIBLE_E1_INPUT` would write a useless
attempt into that chain forever. The implementation can be finished without one;
the first `run_id` waits for an eligible E1 specimen.

## Transcription decisions

Places where the frozen document left a representation choice. Each is a
*representation* decision only — none changes what verifies.

**T1 — language.** TypeScript for the contract declarations. §11.3 leaves the
language unfrozen and states it is not a tuning surface. Everything with
protocol weight (schemas, ruleset, spec facts) is JSON and language-neutral;
only the `contract/*.ts` declarations are TypeScript, so the cost of overturning
T1 is small and local.

**T2 — the `Scope` closed set.** §5.3 calls `scope` "drawn from a closed set"
and enumerates only `FRAME_CONSTRUCTION` as recognised, while requiring a
non-recognised value to be *well-formed* so that adversarial case A13c fails at
the R2 precondition (`RULE_PRECONDITION_UNSATISFIED`) rather than at parse time.
The set is therefore the minimum the frozen matrix forces:
`{FRAME_CONSTRUCTION, ROOT_FRAME_CONSTRUCTION}`.

**T3 — `Span` shape.** §5.3 requires `SEAM_SITE` to carry `source_file` and
`span`, and §5.1 forbids any rule, constraint or conclusion from reading them.
Shape chosen as 1-based line/column, purely for human provenance. Nothing reads
it, so nothing depends on the choice.

**T4 — schemas stay permissive where the ladder needs them to.** §9.2 gives
distinct reason codes to conditions a strict schema would swallow into
`MALFORMED_CERTIFICATE`. So `schema_version` and `ruleset_id` are **not**
`const`, `rule_id` is **not** an enum, `premises` has **no** length constraint,
and `conclusion` is structural rather than a `oneOf` over P1–P4 — each with a
`$comment` naming the check it protects (V2, V3, V8, V9a, V4). Tightening any of
them is a transcription defect, not an improvement, and the checker fails on it.

## An implementation constraint worth knowing before code is written

§11.2 `S2(iii)` forbids the verifier's dependency closure from containing
**dynamic code evaluation**, and §9.3 `K4` forbids reflection or dynamic member
access in the kernel.

Most mainstream JSON Schema validators compile schemas into functions at runtime
via `new Function` — Ajv does this by default. Using one in the verifier would
breach `S2(iii)` and fail the independence test (§12.2 `G2`,
`FAIL_INDEPENDENCE`) for a reason that has nothing to do with certificates.

The verifier must therefore use ahead-of-time generated validation code (e.g.
Ajv's standalone mode, with the generated source committed), or a non-compiling
validator, or hand-written structural checks. This does not constrain the
*producer* or the *extractor*, which are outside the independence surface.

## Next steps, in order

1. hostile review of these artifacts against the frozen document — transcription
   errors only, no design changes;
2. `E5-M0`, committed once the artifacts are final;
3. extractor / producer / verifier bodies — authorable now, **runnable only
   after `M0` is committed** (§14.3, §14.5);
4. `E5-M1` and a first `run_id` only when an eligible E1 specimen exists.
