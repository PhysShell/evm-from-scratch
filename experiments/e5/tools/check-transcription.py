#!/usr/bin/env python3
"""
E5 transcription checker.

Re-derives the frozen tables directly from
docs/experiments/E5-finding-certificates-preregistration.md and diffs them
against the bootstrap artifacts in experiments/e5/. Its only job is to catch
TRANSCRIPTION errors: places where an artifact disagrees with the frozen
document. It is not empowered to judge the document.

This is NOT the extractor and NOT the verifier. It reads no specimen source,
touches nothing under experiments/e1/, and running it is not an E5 run — so it
is not gated on E5-M0 (§14.3, §14.5).

Exit 0 = artifacts agree with the frozen document.
"""
import hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC  = ROOT / "docs/experiments/E5-finding-certificates-preregistration.md"
E5   = ROOT / "experiments/e5"
EXPECTED_DOC_BLOB = "b4f78b572a3de5cdd446524e32f9ec85a264ea5c"

fails, checks = [], 0
def check(name, ok, detail=""):
    global checks
    checks += 1
    if not ok:
        fails.append(f"{name}: {detail}")
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if not ok else ""))

def jcs(o):
    if isinstance(o, dict):
        return "{" + ",".join(jcs(k) + ":" + jcs(v)
                              for k, v in sorted(o.items(), key=lambda kv: [ord(c) for c in kv[0]])) + "}"
    if isinstance(o, list):  return "[" + ",".join(jcs(x) for x in o) + "]"
    if isinstance(o, bool):  return "true" if o else "false"
    if isinstance(o, str):   return json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    if isinstance(o, int):   return str(o)
    raise TypeError(type(o))

def parse_binding(t):
    """Parse a §5.4 `required` cell into the BindingExpr JSON form."""
    t = t.strip().strip("`")
    if t == "CALLEE_ADDRESS":                       return {"node": "CALLEE_ADDRESS"}
    if t == "ZERO":                                 return {"node": "ZERO"}
    if t == "EMPTY":                                return {"node": "EMPTY"}
    m = re.fullmatch(r"CURRENT_FRAME\((\w+)\)", t)
    if m:  return {"node": "CURRENT_FRAME", "field": m.group(1)}
    m = re.fullmatch(r"LITERAL_BOOL\((true|false)\)", t)
    if m:  return {"node": "LITERAL_BOOL", "value": m.group(1) == "true"}
    m = re.fullmatch(r"CODE_AT\((.+)\)", t)
    if m:  return {"node": "CODE_AT", "of": parse_binding(m.group(1))}
    raise ValueError(f"unparseable binding cell: {t!r}")

doc = DOC.read_text(encoding="utf-8")
def section(num):
    m = re.search(rf"^### {re.escape(num)} .*?$(.*?)^### ", doc, re.M | re.S)
    if not m: raise SystemExit(f"section {num} not found")
    return m.group(1)

print("E5 transcription check — authority:", DOC.relative_to(ROOT))
print()

# ---------------------------------------------------------------- §5.4 spec facts
print("§5.4  the 27 frozen spec facts")
sites = ["U-CALL/CALL", "U-CALL/STATICCALL", "U-CALL/DELEGATECALL"]
expected = {}
for line in section("5.4").splitlines():
    m = re.match(r"\|\s*(`[^`]+`|\*each site\*)\s*\|\s*`(\w+)`\s*\|\s*`([^`]+)`\s*\|\s*`([\w-]+)`\s*\|", line)
    if not m: continue
    site_cell, field, req, pid = m.groups()
    targets = sites if site_cell == "*each site*" else [site_cell.strip("`")]
    for s in targets:
        expected[(s, field)] = (parse_binding(req), pid)
check("table yields 27 (site, field) rows", len(expected) == 27, f"got {len(expected)}")

actual_raw = json.loads((E5 / "spec-facts/E5-SPEC-FACTS-v1.json").read_text())
actual = {(f["site"], f["field"]): (f["required"], f["postcondition_id"]) for f in actual_raw.values()}
check("artifact has 27 facts", len(actual_raw) == 27, f"got {len(actual_raw)}")
check("subjects match the table exactly", set(actual) == set(expected),
      f"only-in-artifact={sorted(set(actual)-set(expected))} only-in-doc={sorted(set(expected)-set(actual))}")
mismatched = [k for k in sorted(set(actual) & set(expected)) if actual[k] != expected[k]]
check("every required-binding and postcondition_id matches", not mismatched,
      "; ".join(f"{k}: doc={jcs(expected[k][0])}/{expected[k][1]} art={jcs(actual[k][0])}/{actual[k][1]}" for k in mismatched))

spec_rev = re.search(r"`spec_revision = ([0-9a-f]{40})`", section("5.4")).group(1)
check("spec_revision matches §5.4", all(f["spec_revision"] == spec_rev for f in actual_raw.values()), spec_rev)
bad_id = [k for k, f in actual_raw.items()
          if k != f["fact_id"]
          or hashlib.sha256(jcs({a: b for a, b in f.items() if a != "fact_id"}).encode()).hexdigest() != f["fact_id"]]
check("every fact_id is content-derived per §5.5", not bad_id, str(bad_id[:3]))

# ---------------------------------------------------------------- §5.2 algebra
print("\n§5.2  BindingExpr algebra and FrameField order")
s52 = section("5.2")
ff_doc = re.findall(r"\b(code|pc|stack|memory|address|caller|static|storage_owner|returndata)\b",
                    s52.split("BindingExpr :=")[0])
ff_doc = list(dict.fromkeys(ff_doc))
facts_schema = json.loads((E5 / "schema/E5-FACTS-v1.schema.json").read_text())
check("FrameField set and ORDER match the doc",
      facts_schema["$defs"]["FrameField"]["enum"] == ff_doc,
      f"doc={ff_doc} schema={facts_schema['$defs']['FrameField']['enum']}")
nodes_doc = set(re.findall(r"^\s*[|]\s*(\w+)", s52.split("BindingExpr :=")[1].split("```")[0], re.M)) \
          | {"CALLEE_ADDRESS"}
nodes_schema = {v["properties"]["node"]["const"] for v in facts_schema["$defs"]["BindingExpr"]["oneOf"]}
check("BindingExpr constructors match", nodes_doc == nodes_schema,
      f"doc-only={nodes_doc-nodes_schema} schema-only={nodes_schema-nodes_doc}")

# ---------------------------------------------------------------- §5.3 fact kinds
print("\n§5.3  fact kinds")
kinds_doc = set(re.findall(r"^\| `(\w+)` \| (?:spec|source) \|", section("5.3"), re.M))
kinds_schema = {facts_schema["$defs"][r["$ref"].split("/")[-1]]["properties"]["kind"]["const"]
                for r in facts_schema["$defs"]["Fact"]["oneOf"]}
check("fact kinds match §5.3", kinds_doc == kinds_schema,
      f"doc-only={kinds_doc-kinds_schema} schema-only={kinds_schema-kinds_doc}")
check("no fact kind means 'not written'",
      not any("NOT" in k or "ABSENT" in k or "MISSING" in k for k in kinds_schema), str(kinds_schema))

# ---------------------------------------------------------------- §6.1 propositions
print("\n§6.1  proposition shapes")
rules = json.loads((E5 / "ruleset/E5-RULES-v1.json").read_text())
props_doc = set(re.findall(r"^P\d\s+(\w+)", section("6.1"), re.M))
props_art = {k for k in rules["propositions"] if not k.startswith("$")}
check("proposition shapes match §6.1", props_doc == props_art,
      f"doc-only={props_doc-props_art} artifact-only={props_art-props_doc}")

# ---------------------------------------------------------------- §7.2 ruleset
print("\n§7.2  ruleset")
s72 = section("7.2")
arity_doc = {m.group(1): int(m.group(2)) for m in re.finditer(r"\*\*`(R\d)` — `\w+`\*\* · arity (\d)", s72)}
arity_art = {r["rule_id"]: r["arity"] for r in rules["rules"]}
check("rule ids and arities match §7.2", arity_doc == arity_art, f"doc={arity_doc} artifact={arity_art}")
check("slot count equals declared arity for every rule",
      all(len(r["slots"]) == r["arity"] for r in rules["rules"]))
names_doc = dict(re.findall(r"\*\*`(R\d)` — `(\w+)`\*\*", s72))
check("rule names match", names_doc == {r["rule_id"]: r["name"] for r in rules["rules"]})
bcf_doc = re.search(r"BOUNDARY_CARRIED_FIELDS = \{ ([^}]+) \}", s72).group(1)
bcf_doc = [x.strip() for x in bcf_doc.split(",")]
check("BOUNDARY_CARRIED_FIELDS matches §7.2 verbatim",
      rules["constants"]["BOUNDARY_CARRIED_FIELDS"] == bcf_doc,
      f"doc={bcf_doc} artifact={rules['constants']['BOUNDARY_CARRIED_FIELDS']}")
check("RECOGNISED_SCOPE is exactly {FRAME_CONSTRUCTION}",
      rules["constants"]["RECOGNISED_SCOPE"] == ["FRAME_CONSTRUCTION"])
neg = [r for r in rules["rules"] if r["derives"]["shape"] == "SEAM_FIELD_NOT_BOUND"]
check("exactly one negative-conclusion rule (§7.3)", len(neg) == 1, f"got {[r['rule_id'] for r in neg]}")
check("that rule requires a CONSTRUCTION_WRITES_COMPLETE premise (§3.2)",
      any(s["kind"] == "CONSTRUCTION_WRITES_COMPLETE" for s in neg[0]["slots"]) if neg else False)
check("its negation is over the witness payload, never the bundle",
      any("not_member_of" in p and p["not_member_of"]["collection"] == "F"
          for p in neg[0]["preconditions"]) if neg else False)
for rid in ("R3", "R5"):
    r = next(x for x in rules["rules"] if x["rule_id"] == rid)
    check(f"{rid} requires both compared bindings fully modelled (§5.2)",
          sum(1 for p in r["preconditions"] if "fully_modelled" in p) == 2)
for rid in ("R4", "R5"):
    r = next(x for x in rules["rules"] if x["rule_id"] == rid)
    check(f"{rid} requires f in BOUNDARY_CARRIED_FIELDS",
          any(p.get("member_of_constant", {}).get("constant") == "BOUNDARY_CARRIED_FIELDS"
              for p in r["preconditions"]))

# ---------------------------------------------------------------- §9.4 reason codes
print("\n§9.4  reason code vocabulary")
s94 = re.search(r"^### 9\.4 .*?```text(.*?)```", doc, re.M | re.S).group(1)
codes_doc = set(re.findall(r"\b([A-Z][A-Z_]{4,})\b", s94))
check("ruleset reason_codes match §9.4 exactly", set(rules["reason_codes"]) == codes_doc,
      f"doc-only={codes_doc-set(rules['reason_codes'])} artifact-only={set(rules['reason_codes'])-codes_doc}")
kernel_ts = (E5 / "contract/verifier-kernel.ts").read_text()
codes_ts = set(re.findall(r'"([A-Z][A-Z_]{4,})"', kernel_ts.split("export type ReasonCode")[1].split(";")[0]))
check("verifier-kernel.ts ReasonCode union matches §9.4", codes_ts == codes_doc,
      f"doc-only={codes_doc-codes_ts} ts-only={codes_ts-codes_doc}")

# ------------------------------------------------- ladder reachability (schema permissiveness)
print("\n§9.2  ladder reachability — schemas must stay permissive where a code exists")
cert_schema = json.loads((E5 / "schema/E5-CERT-v1.schema.json").read_text())
p = cert_schema["properties"]
check("schema_version is not const (V2 UNKNOWN_SCHEMA_VERSION stays reachable)", "const" not in p["schema_version"])
check("ruleset_id is not const (V3 UNKNOWN_RULESET stays reachable)", "const" not in p["ruleset_id"])
check("conclusion is structural, not a oneOf over P1..P4 (V4 stays reachable)",
      "oneOf" not in cert_schema["$defs"]["Proposition"])
step = cert_schema["$defs"]["ProofStep"]["properties"]
check("rule_id is not an enum (V8 UNKNOWN_RULE stays reachable)", "enum" not in step["rule_id"])
check("premises has no length constraint (V9a PREMISE_ARITY_MISMATCH stays reachable)",
      "minItems" not in step["premises"] and "maxItems" not in step["premises"])
check("scope allows a non-recognised value (A13c constructible, §5.3)",
      len(facts_schema["$defs"]["Scope"]["enum"]) > 1 and
      "FRAME_CONSTRUCTION" in facts_schema["$defs"]["Scope"]["enum"])

# ---------------------------------------------------------------- capability boundary
print("\n§9.3  capability boundary")
resolver = (E5 / "contract/fact-resolver.ts").read_text()
members = re.findall(r"^\s{2}(\w+)\s*[(<]", resolver.split("export interface FactResolver")[1], re.M)
check("K3 — FactResolver declares exactly one operation", members == ["Resolve"], str(members))
check("K3 — no iterator/length/count/keys/collection member",
      not re.search(r"\b(length|size|count|keys|entries|values|all|list|Symbol\.iterator)\b",
                    resolver.split("export interface FactResolver")[1]))
kernel_imports = set(re.findall(r'from "\./([\w-]+)"', kernel_ts))
check("K1/K2 — kernel imports only certificate and fact-resolver",
      kernel_imports == {"certificate", "fact-resolver"}, str(sorted(kernel_imports)))
check("K2 — bundle-loader is NOT in the kernel's import closure",
      "bundle-loader" not in kernel_imports)
loader = (E5 / "contract/bundle-loader.ts").read_text()
exports = re.findall(r"^export (?:declare function|interface|const|type) (\w+)", loader, re.M)
check("K5 — BundleLoader exports one function (plus its return type)",
      [e for e in exports if e == "load"] == ["load"], str(exports))

# ---------------------------------------------------------------- isolation
print("\n§6.4 / §11.2 S1  isolation from E1")
srcs = list((E5 / "contract").glob("*.ts"))
check("no E5 source imports anything under experiments/e1",
      not any(re.search(r'from ["\'].*e1[/\\]', f.read_text()) for f in srcs))
ts = json.loads(re.sub(r'"\$comment":\s*\[[^\]]*\],', "", (E5 / "tsconfig.json").read_text()))
check("tsconfig declares no path mapping", ts["compilerOptions"].get("paths") == {})
check("tsconfig rootDir confines the program to experiments/e5",
      ts["compilerOptions"].get("rootDir") == ".")

print()
print(f"{checks - len(fails)}/{checks} checks passed")
if fails:
    print("\nFAILURES:")
    for f in fails: print("  -", f)
    sys.exit(1)
print("artifacts agree with the frozen document.")
