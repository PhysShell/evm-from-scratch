#!/usr/bin/env python3
"""
E5-M0 audit-value verifier.

§14.2 records M and E5_DOC_BLOB_SHA "as audit values that must equal the computed
ones, never as the thing that selects it", and a recorded value disagreeing with
the computation is INVALID_EXPERIMENT — §12.2 G0, the first gate. This script
mechanises exactly that comparison for every value E5-M0 records.

IN SCOPE
  - find M independently by a full (a)-(f) scan of the reachable history
  - evaluate E5_FROZEN at HEAD
  - compare the recorded M and E5_DOC_BLOB_SHA against the computed ones
  - re-extract the design cutoff, freeze base and topology log FROM THE FROZEN
    DOCUMENT and compare
  - check the E1 Step 0 and Step 2 blob shas
  - recompute SHA-256 over exact file bytes for ONLY the artifacts §14.3
    requires digesting
  - check ruleset_id, the schema ids, and the two capability signatures
  - check that all five S2 categories are present and that there is no sixth
  - check the by-reference block names the frozen blob and resolvable sections
  - check the canonicalization and digest function

OUT OF SCOPE, deliberately
  - judging whether the preregistration is any good
  - adding M0 obligations beyond §14.3
  - E5-M1, which does not exist
  - extractor / producer / verifier implementations
  - turning the informational spec-facts hash into a gate

Exit 0 = every recorded audit value equals the computed one.
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = "docs/experiments/E5-finding-certificates-preregistration.md"
M0_PATH  = "experiments/e5/manifest/E5-M0.json"

# Optional argv[1] overrides the manifest path so the self-test can point this
# script at a mutated copy while the git queries still target the real
# repository. It parameterizes the INPUT only; no check changes.

def git(*a):
    r = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)
    return r.stdout.strip()

def blob_bytes(rev, path):
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", f"{rev}:{path}"],
                          capture_output=True).stdout

def path_exists(rev, path):
    return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{rev}:{path}"],
                          capture_output=True).returncode == 0

fails, n = [], 0
def check(name, recorded, computed):
    global n; n += 1
    ok = recorded == computed
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
    if not ok:
        fails.append(f"{name}\n        recorded = {recorded!r}\n        computed = {computed!r}")
    return ok

HEAD = git("rev-parse", "HEAD")
m0_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / M0_PATH
m0 = json.loads(m0_file.read_text())
print(f"E5-M0 audit verification   HEAD = {HEAD}\n")

# ---------------------------------------------------------------- freeze anchor
print("§14.2  freeze anchor, recomputed from history")
fa   = m0["freeze_anchor"]
base = fa["freeze_base_sha"]

candidates, scanned = [], 0
for c in git("rev-list", HEAD).split():
    scanned += 1
    parents = git("log", "-1", "--format=%P", c).split()
    if len(parents) != 2:                       continue      # (a)
    p1, p2 = parents
    if p1 != base:                              continue      # (b)
    if path_exists(p1, DOC_PATH):               continue      # (c)
    if not path_exists(p2, DOC_PATH):           continue      # (d)
    if git("rev-parse", f"{c}:{DOC_PATH}") != git("rev-parse", f"{p2}:{DOC_PATH}"):
        continue                                              # (e)
    candidates.append(c)

check("(f) exactly one commit satisfies (a)-(e)", 1, len(candidates))
if len(candidates) != 1:
    print(f"\n  candidates = {candidates}\n  cannot proceed: M is not uniquely determined")
    sys.exit(1)
M = candidates[0]
ev = fa["M_evidence"]
check("recorded M equals the computed M", fa["M"], M)
check("(a) parent count", ev["a_parent_count"], len(git("log", "-1", "--format=%P", M).split()))
check("(b) first parent", ev["b_first_parent"], git("rev-parse", f"{M}^1"))
check("(b) first parent equals freeze_base_sha", True, git("rev-parse", f"{M}^1") == base)
check("(c) doc absent at first parent", True, not path_exists(f"{M}^1", DOC_PATH))
check("(d) second parent", ev["d_second_parent"], git("rev-parse", f"{M}^2"))
check("(d) doc present at second parent", True, path_exists(f"{M}^2", DOC_PATH))
check("(e) blob at M", ev["e_blob_at_M"], git("rev-parse", f"{M}:{DOC_PATH}"))
check("(e) blob at second parent", ev["e_blob_at_second_parent"], git("rev-parse", f"{M}^2:{DOC_PATH}"))
check("(e) the two blobs are equal", True, ev["e_blob_at_M"] == ev["e_blob_at_second_parent"])
check("(f) commits scanned", ev["f_commits_scanned"], scanned)

print("\nE5_FROZEN at HEAD")
check("clause 1 — M exists and is unique", True, True)
check("clause 2 — HEAD descends from M", True,
      subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", M, HEAD]).returncode == 0)
touched = [x for x in git("rev-list", f"{M}..{HEAD}", "--", DOC_PATH).split() if x]
check("clause 3 — no commit in M..HEAD modifies the preregistration", 0, len(touched))
check("recorded E5_DOC_BLOB_SHA", fa["E5_DOC_BLOB_SHA"], git("rev-parse", f"{M}:{DOC_PATH}"))
check("recorded E5_FROZEN clause-3 count",
      fa["E5_FROZEN_clause_3"]["commits_modifying_doc_between_M_and_computed_tree"], len(touched))

# ------------------------------------------- values re-extracted from the document
print("\n§1.1 / §14.2  values re-extracted from the frozen document")
doc = blob_bytes(M, DOC_PATH).decode("utf-8")
cutoff_doc = re.search(r"E5_DESIGN_CUTOFF_SHA = ([0-9a-f]{40})", doc).group(1)
check("E5_DESIGN_CUTOFF_SHA matches §1.1", m0["design_cutoff"]["E5_DESIGN_CUTOFF_SHA"], cutoff_doc)
base_doc = re.search(r"freeze_base_sha := ([0-9a-f]{40})", doc).group(1)
check("freeze_base_sha matches §14.2", base, base_doc)
check("design cutoff and freeze base are DISTINCT values (§14.3)", True, cutoff_doc != base_doc)

log_rows = re.findall(r"^\| (\d+) \| `([0-9a-f]+)…` \|", doc, re.M)
check("topology amendment log entry count matches §14.2",
      len(m0["freeze_anchor"]["topology_amendment_log"]), len(log_rows))
for rec, (num, prefix) in zip(m0["freeze_anchor"]["topology_amendment_log"], log_rows):
    check(f"topology log entry {num} prefix matches the document",
          rec["freeze_base_sha"][:len(prefix)], prefix)
check("the current topology log entry is the recorded freeze_base_sha", base,
      m0["freeze_anchor"]["topology_amendment_log"][-1]["freeze_base_sha"])

print("\n§5.1 / §1.2  spec revisions")
sr = m0["spec_revisions"]
check("spec_revision blob (E1 Step 2)", sr["spec_revision"]["blob_sha"],
      git("rev-parse", f"{HEAD}:{sr['spec_revision']['path']}"))
check("E1 Step 0 blob", sr["e1_step0_blob_sha"]["blob_sha"],
      git("rev-parse", f"{HEAD}:{sr['e1_step0_blob_sha']['path']}"))

# ------------------------------------------------------- byte-pinned artifacts
print("\n§14.3  byte-pinned artifacts — SHA-256 over exact file bytes")
check("artifact digest method is recorded", "SHA-256 over exact file bytes",
      m0["artifact_digest_method"]["method"])

REQUIRED = {  # exactly what §14.3 requires digesting, and nothing else
    "artifacts.ruleset":            ("ruleset_id",  "E5-RULES/v1"),
    "artifacts.schema_facts":       ("schema_id",   "E5-FACTS/v1"),
    "artifacts.schema_certificate": ("schema_id",   "E5-CERT/v1"),
    "capability_boundary.fact_resolver_declaration":      (None, None),
    "capability_boundary.bundle_loader_exported_signature": (None, None),
}
def dig(d, dotted):
    for k in dotted.split("."): d = d[k]
    return d

for key, (idfield, idvalue) in REQUIRED.items():
    a = dig(m0, key)
    label = a["path"].split("/")[-1]
    check(f"sha256 {label}", a["sha256"], hashlib.sha256(blob_bytes(HEAD, a["path"])).hexdigest())
    check(f"git blob {label}", a["git_blob_sha"], git("rev-parse", f"{HEAD}:{a['path']}"))
    if idfield:
        check(f"{idfield} of {label}", a[idfield], idvalue)

check("ruleset_id equals the id inside the ruleset artifact",
      m0["artifacts"]["ruleset"]["ruleset_id"],
      json.loads(blob_bytes(HEAD, m0["artifacts"]["ruleset"]["path"]))["ruleset_id"])
for key, sid in (("schema_facts", "E5-FACTS/v1"), ("schema_certificate", "E5-CERT/v1")):
    a = m0["artifacts"][key]
    check(f"$id inside {a['path'].split('/')[-1]}", sid,
          json.loads(blob_bytes(HEAD, a["path"]))["$id"])

print("\n§9.3  capability signatures present in the declarations")
fr = m0["capability_boundary"]["fact_resolver_declaration"]
check("FactResolver Resolve signature appears in the declaration", True,
      "Resolve(id: FactId): Fact | NotFound" in blob_bytes(HEAD, fr["path"]).decode())
bl = m0["capability_boundary"]["bundle_loader_exported_signature"]
check("BundleLoader exported signature appears verbatim in the declaration", True,
      bl["signature"] in blob_bytes(HEAD, bl["path"]).decode())

# --------------------------------------------------------------- S2 deny-list
print("\n§11.2 S2  deny-list")
doc_cats = re.findall(r"^\s+\((i|ii|iii|iv|v)\)\s+(.+?)$",
                      doc.split("S2   that closure references nothing")[1].split("E5-M0 records")[0], re.M)
cats = m0["s2_deny_list"]["categories"]
check("exactly five categories, and no sixth", 5, len(cats))
check("category ids", ["i", "ii", "iii", "iv", "v"], [c["id"] for c in cats])
for c, (did, dtext) in zip(cats, doc_cats):
    check(f"category ({did}) text begins as the document states",
          True, c["category"].startswith(dtext.strip().rstrip(",")[:30]))
v = next(c for c in cats if c["id"] == "v")
check("category (v) retains the 'used to reach past a declared interface' qualifier",
      True, "used to reach past a declared interface" in v["category"])
check("category (v) introduces no static-type narrowing",
      True, any("NO narrowing by the expression's current static type" in a
                for a in v.get("applicability", [])))

# ------------------------------------------------------------- by-reference block
print("\n§14.3  frozen surfaces, by reference")
fs = m0["frozen_surfaces_by_reference"]
check("by-reference block names the frozen document blob", fs["blob_sha"], fa["E5_DOC_BLOB_SHA"])
unresolved = [s for refs in fs["surfaces"].values()
              for s in re.findall(r"§(\d+(?:\.\d+)?)", refs)
              if not re.search(rf"^#{{2,3}} {re.escape(s)}[ .]", doc, re.M)]
check("every referenced section resolves to a heading in the document", [], unresolved)

print("\n§5.5  canonicalization and digest")
cd = m0["canonicalization_and_digest"]
check("canonicalization", "RFC 8785 JSON Canonicalization Scheme (JCS)", cd["canonicalization"])
check("digest", "SHA-256, lowercase hex", cd["digest"])

# ------------------------------------------------------------------ informational
print("\ninformational — NOT an M0 obligation and NOT a gate")
sf_path = m0["spec_facts_identity"]["transcription_artifact"]["path"]
sf_name = sf_path.split("/")[-1]
sf_sha  = hashlib.sha256(blob_bytes(HEAD, sf_path)).hexdigest()
sf_blob = git("rev-parse", f"{HEAD}:{sf_path}")
print(f"  ..    {sf_name}  sha256 = {sf_sha}")
print(f"  ..    {sf_name}  blob   = {sf_blob}")
print(f"  ..    normative identity is §5.4 of the document at {fa['E5_DOC_BLOB_SHA']}")
print("  ..    neither value gates anything (§14.3 does not enumerate this artifact)")

print(f"\n{n - len(fails)}/{n} recorded audit values equal the computed ones")
if fails:
    print("\nMISMATCHES — INVALID_EXPERIMENT under §12.2 G0:")
    for f in fails: print("  -", f)
    sys.exit(1)
