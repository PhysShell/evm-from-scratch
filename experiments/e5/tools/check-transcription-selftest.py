#!/usr/bin/env python3
"""
Negative controls for check-transcription.py.

A checker that only ever reports green is decorative. This harness copies the
tree to a temporary directory, reintroduces each defect the checker claims to
catch, and asserts the checker FAILS on the expected assertion.

Every mutation below is a real defect that was present in, or narrowly avoided
by, an earlier revision of the bootstrap artifacts. Four of them (M1, M2, M3, M7)
were found in review AFTER the checker had reported 39/39 green — because it was
asserting weaker properties than the frozen document states. This file exists so
that cannot happen silently again.

Exit 0 = every control fired on the check it was aimed at.
"""
import re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
E5   = ROOT / "experiments/e5"
DOC  = "docs/experiments/E5-finding-certificates-preregistration.md"

def edit(path, old, new):
    def apply(root):
        p = root / path
        s = p.read_text()
        assert s.count(old) == 1, f"anchor not unique in {path}: {old[:60]!r}"
        p.write_text(s.replace(old, new, 1))
    return apply

CONTROLS = [
    ("M1  steps regains minItems: 1  (V7 EMPTY_DERIVATION unreachable)",
     "steps has no minItems/maxItems",
     edit("experiments/e5/schema/E5-CERT-v1.schema.json",
          '"steps": {\n      "type": "array",',
          '"steps": {\n      "type": "array",\n      "minItems": 1,')),

    ("M2  kernel regains a bundleDigest parameter  (K1 breach)",
     "K1 — kernel declared inputs are exactly",
     edit("experiments/e5/contract/verifier-kernel.ts",
          "verify(certificate: Certificate, resolver: FactResolver): Verdict",
          "verify(certificate: Certificate, resolver: FactResolver, bundleDigest: string): Verdict")),

    ("M3  BundleLoader exports a second symbol  (K5 breach)",
     "K5 — BundleLoader exports exactly one symbol",
     edit("experiments/e5/contract/bundle-loader.ts",
          "/** `digest` is sha256",
          "export interface LoadedBundle { resolver: FactResolver; digest: string }\n\n/** `digest` is sha256")),

    ("M4  kernel reaches the loader at depth 2  (K2 breach, invisible to a direct-import check)",
     "K2 — bundle-loader is not in the kernel's TRANSITIVE closure",
     edit("experiments/e5/contract/certificate.ts",
          'import type { FactId, GitObjectSha } from "./facts";',
          'import type { FactId, GitObjectSha } from "./facts";\nimport type { load } from "./bundle-loader";')),

    ("M5  FactResolver gains a collection member  (K3 breach)",
     "K3 — FactResolver declares exactly one operation",
     edit("experiments/e5/contract/fact-resolver.ts",
          "  Resolve(id: FactId): Fact | NotFound;",
          "  Resolve(id: FactId): Fact | NotFound;\n  count(): number;")),

    ("M6  a spec fact's required binding is altered  (§5.4 transcription)",
     "every required-binding and postcondition_id matches",
     edit("experiments/e5/spec-facts/E5-SPEC-FACTS-v1.json",
          '"node": "LITERAL_BOOL",\n      "value": true',
          '"node": "LITERAL_BOOL",\n      "value": false')),

    ("M7  NOT_FOUND becomes a runtime value  (contract/ no longer declaration-only)",
     "fact-resolver.ts emits no runtime value",
     edit("experiments/e5/contract/fact-resolver.ts",
          "export declare const NOT_FOUND: unique symbol;",
          'export const NOT_FOUND = Symbol("NOT_FOUND");')),

    ("M8  ruleset_id becomes const in the cert schema  (V3 UNKNOWN_RULESET unreachable)",
     "ruleset_id is not const",
     edit("experiments/e5/schema/E5-CERT-v1.schema.json",
          '"ruleset_id": {\n      "$comment": "NOT const.',
          '"ruleset_id": {\n      "const": "E5-RULES/v1",\n      "$comment": "NOT const.')),

    ("M9  R2 loses its completeness-witness premise  (§3.2 breach)",
     "that rule requires a CONSTRUCTION_WRITES_COMPLETE premise",
     edit("experiments/e5/ruleset/E5-RULES-v1.json",
          '"kind": "CONSTRUCTION_WRITES_COMPLETE",',
          '"kind": "SEAM_SITE",')),
]

failures = []
for label, expected_check, mutate in CONTROLS:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "docs/experiments").mkdir(parents=True)
        shutil.copy(ROOT / DOC, tmp / DOC)
        shutil.copytree(E5, tmp / "experiments/e5")
        mutate(tmp)
        r = subprocess.run([sys.executable, str(tmp / "experiments/e5/tools/check-transcription.py")],
                           capture_output=True, text=True)
        caught = r.returncode != 0 and any(
            expected_check in ln for ln in r.stdout.splitlines() if ln.strip().startswith("FAIL"))
        print(f"  {'ok  ' if caught else 'FAIL'}  {label}")
        if not caught:
            failures.append((label, expected_check, r.returncode,
                             [l for l in r.stdout.splitlines() if l.strip().startswith("FAIL")]))

print()
print(f"{len(CONTROLS) - len(failures)}/{len(CONTROLS)} negative controls fired on the intended check")
if failures:
    print("\nCONTROLS THAT DID NOT FIRE — the checker is not testing what it claims:")
    for label, exp, rc, got in failures:
        print(f"  - {label}\n      expected a FAIL on: {exp}\n      exit={rc} actual FAILs={got}")
    sys.exit(1)
