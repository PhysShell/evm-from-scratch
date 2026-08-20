#!/usr/bin/env python3
"""
E5-M0 audit-value verifier.

§14.2 records M and E5_DOC_BLOB_SHA "as audit values that must equal the computed
ones, never as the thing that selects it", and a recorded value disagreeing with
the computation is INVALID_EXPERIMENT — §12.2 G0, the first gate. This script
mechanises that comparison for every value E5-M0 records.

THREE REVISIONS, THREE DIFFERENT QUESTIONS. An earlier revision of this script
resolved everything against HEAD, which was wrong twice over:

  - it re-scanned HEAD and compared the count to f_commits_scanned, so the act of
    committing E5-M0 made the manifest's own historical evidence "wrong". It
    failed 57/58 on the very commit that introduced it. Reachability counts are
    evidence ABOUT the tree the manifest was computed from; they cannot be
    invariants of a future HEAD.
  - it resolved the E1 Step 0 and Step 2 blobs at HEAD, so a future E1-v6 legally
    editing either document would retroactively invalidate an old M0 — when those
    values exist precisely to witness what was READ at the design cutoff.

So each value is checked against the revision that gives it meaning:

  A  historical M0 evidence      -> M0.computed_from.tree
  B  current protocol integrity  -> HEAD
  C  frozen read-set             -> M0.design_cutoff.E5_DESIGN_CUTOFF_SHA
  D  M0-pinned mutable surfaces  -> HEAD
  E  manifest vs frozen document -> the document at M

D is deliberately HEAD-relative while C is deliberately cutoff-relative: the
ruleset and schemas are surfaces M0 PINS, so silent drift in them must be caught,
whereas the Step 0/Step 2 blobs are a record of a past reading and must not move
when E1 moves on.

IN SCOPE: exactly the obligations §14.3 enumerates.
OUT OF SCOPE, deliberately: judging the preregistration; adding obligations;
E5-M1; extractor/producer/verifier implementations; promoting the informational
spec-facts hash into a gate.

Usage: verify-m0.py [path-to-manifest]
The optional argument points at a manifest copy while the git queries still
target the real repository; it parameterizes the INPUT only, and changes no check.

Exit 0 = every recorded audit value equals the computed one.
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT     = Path(__file__).resolve().parents[3]
DOC_PATH = "docs/experiments/E5-finding-certificates-preregistration.md"
M0_PATH  = "experiments/e5/manifest/E5-M0.json"

def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()

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

def scan_for_M(tip, base):
    """Full §14.2 (a)-(f) scan over everything reachable from `tip`."""
    found, scanned = [], 0
    for c in git("rev-list", tip).split():
        scanned += 1
        parents = git("log", "-1", "--format=%P", c).split()
        if len(parents) != 2:                                   continue   # (a)
        p1, p2 = parents
        if p1 != base:                                          continue   # (b)
        if path_exists(p1, DOC_PATH):                           continue   # (c)
        if not path_exists(p2, DOC_PATH):                       continue   # (d)
        if git("rev-parse", f"{c}:{DOC_PATH}") != git("rev-parse", f"{p2}:{DOC_PATH}"):
            continue                                                       # (e)
        found.append(c)
    return found, scanned

m0_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / M0_PATH
m0      = json.loads(m0_file.read_text())

HEAD       = git("rev-parse", "HEAD")
AUDIT_TREE = m0["computed_from"]["tree"]
CUTOFF     = m0["design_cutoff"]["E5_DESIGN_CUTOFF_SHA"]
fa         = m0["freeze_anchor"]
base       = fa["freeze_base_sha"]
ev         = fa["M_evidence"]

print(f"E5-M0 audit verification")
print(f"  HEAD        {HEAD}")
print(f"  audit tree  {AUDIT_TREE}   (M0.computed_from.tree)")
print(f"  cutoff      {CUTOFF}   (M0.design_cutoff)\n")

# ══════════════════════════════════════════ A ═══ historical evidence @ audit_tree
print("A  historical M0 evidence, reproduced from the audit tree")
cand_a, scanned_a = scan_for_M(AUDIT_TREE, base)
check("(f) exactly one commit satisfies (a)-(e) in the audit tree", 1, len(cand_a))
if len(cand_a) != 1:
    print(f"\n  candidates = {cand_a}\n  cannot proceed: M is not uniquely determined")
    sys.exit(1)
M = cand_a[0]
check("recorded M equals the M computed from the audit tree", fa["M"], M)
check("(f) commits scanned matches the recorded count", ev["f_commits_scanned"], scanned_a)
check("(a) parent count", ev["a_parent_count"], len(git("log", "-1", "--format=%P", M).split()))
check("(b) first parent", ev["b_first_parent"], git("rev-parse", f"{M}^1"))
check("(b) first parent equals freeze_base_sha", True, git("rev-parse", f"{M}^1") == base)
check("(c) doc absent at first parent", True, not path_exists(f"{M}^1", DOC_PATH))
check("(d) second parent", ev["d_second_parent"], git("rev-parse", f"{M}^2"))
check("(d) doc present at second parent", True, path_exists(f"{M}^2", DOC_PATH))
check("(e) blob at M", ev["e_blob_at_M"], git("rev-parse", f"{M}:{DOC_PATH}"))
check("(e) blob at second parent", ev["e_blob_at_second_parent"], git("rev-parse", f"{M}^2:{DOC_PATH}"))
check("(e) the two blobs are equal", True, ev["e_blob_at_M"] == ev["e_blob_at_second_parent"])
check("recorded E5_DOC_BLOB_SHA", fa["E5_DOC_BLOB_SHA"], git("rev-parse", f"{M}:{DOC_PATH}"))

# ══════════════════════════════════════════ B ═══ current integrity @ HEAD
print("\nB  current protocol integrity, at HEAD")
cand_b, scanned_b = scan_for_M(HEAD, base)
check("M is still unique under (a)-(e) at HEAD", 1, len(cand_b))
check("the M computed at HEAD is still the recorded M", fa["M"], cand_b[0] if cand_b else None)
check("E5_FROZEN clause 2 — HEAD descends from M", True,
      subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", M, HEAD]).returncode == 0)
touched = [x for x in git("rev-list", f"{M}..{HEAD}", "--", DOC_PATH).split() if x]
check("E5_FROZEN clause 3 — no commit in M..HEAD modifies the preregistration", 0, len(touched))
check("recorded E5_FROZEN clause-3 count is about the audit tree, and holds there",
      fa["E5_FROZEN_clause_3"]["commits_modifying_doc_between_M_and_computed_tree"],
      len([x for x in git("rev-list", f"{M}..{AUDIT_TREE}", "--", DOC_PATH).split() if x]))
print(f"  ..    commits reachable: audit tree {scanned_a}, HEAD {scanned_b}"
      f"{' (HEAD has advanced since M0 was prepared — expected)' if scanned_b > scanned_a else ''}")

# ══════════════════════════════════════════ C ═══ frozen read-set @ design cutoff
print("\nC  frozen read-set, reproduced at the design cutoff")
sr = m0["spec_revisions"]
for label, entry in (("spec_revision (E1 Step 2)", sr["spec_revision"]),
                     ("E1 Step 0 blob",            sr["e1_step0_blob_sha"])):
    p = entry["path"]
    check(f"{label} at the design cutoff", entry["blob_sha"], git("rev-parse", f"{CUTOFF}:{p}"))
    at_head = git("rev-parse", f"{HEAD}:{p}")
    if at_head == entry["blob_sha"]:
        print(f"  ..    {p.split('/')[-1]} is unchanged at HEAD — this check is not"
              f" currently discriminating, but it is what keeps a future E1 edit"
              f" from retroactively invalidating this manifest")
    else:
        print(f"  ..    {p.split('/')[-1]} HAS since changed at HEAD ({at_head}) — correctly"
              f" ignored: M0 witnesses what was read at the cutoff")

# ══════════════════════════════════════════ D ═══ pinned surfaces @ HEAD
print("\nD  M0-pinned surfaces, checked at HEAD for silent drift")
check("artifact digest method is recorded", "SHA-256 over exact file bytes",
      m0["artifact_digest_method"]["method"])

PINNED = [("artifacts", "ruleset",            "ruleset_id", "E5-RULES/v1"),
          ("artifacts", "schema_facts",       "schema_id",  "E5-FACTS/v1"),
          ("artifacts", "schema_certificate", "schema_id",  "E5-CERT/v1"),
          ("capability_boundary", "fact_resolver_declaration",       None, None),
          ("capability_boundary", "bundle_loader_exported_signature", None, None)]
for group, key, idfield, idvalue in PINNED:
    a     = m0[group][key]
    label = a["path"].split("/")[-1]
    check(f"sha256 {label} unchanged at HEAD", a["sha256"],
          hashlib.sha256(blob_bytes(HEAD, a["path"])).hexdigest())
    check(f"git blob {label} unchanged at HEAD", a["git_blob_sha"], git("rev-parse", f"{HEAD}:{a['path']}"))
    if idfield:
        check(f"{idfield} of {label}", a[idfield], idvalue)

check("ruleset_id equals the id inside the ruleset artifact",
      m0["artifacts"]["ruleset"]["ruleset_id"],
      json.loads(blob_bytes(HEAD, m0["artifacts"]["ruleset"]["path"]))["ruleset_id"])
for key, sid in (("schema_facts", "E5-FACTS/v1"), ("schema_certificate", "E5-CERT/v1")):
    a = m0["artifacts"][key]
    check(f"$id inside {a['path'].split('/')[-1]}", sid, json.loads(blob_bytes(HEAD, a["path"]))["$id"])

fr = m0["capability_boundary"]["fact_resolver_declaration"]
check("FactResolver Resolve signature appears in the declaration", True,
      "Resolve(id: FactId): Fact | NotFound" in blob_bytes(HEAD, fr["path"]).decode())
bl = m0["capability_boundary"]["bundle_loader_exported_signature"]
check("BundleLoader exported signature appears verbatim in the declaration", True,
      bl["signature"] in blob_bytes(HEAD, bl["path"]).decode())

# ══════════════════════════════════════════ E ═══ manifest vs the frozen document
print("\nE  manifest content, re-extracted from the frozen document at M")
doc = blob_bytes(M, DOC_PATH).decode("utf-8")
cutoff_doc = re.search(r"E5_DESIGN_CUTOFF_SHA = ([0-9a-f]{40})", doc).group(1)
check("E5_DESIGN_CUTOFF_SHA matches §1.1", CUTOFF, cutoff_doc)
base_doc = re.search(r"freeze_base_sha := ([0-9a-f]{40})", doc).group(1)
check("freeze_base_sha matches §14.2", base, base_doc)
check("design cutoff and freeze base are DISTINCT values (§14.3)", True, cutoff_doc != base_doc)

log_rows = re.findall(r"^\| (\d+) \| `([0-9a-f]+)…` \|", doc, re.M)
check("topology amendment log entry count matches §14.2",
      len(fa["topology_amendment_log"]), len(log_rows))
for rec, (num, prefix) in zip(fa["topology_amendment_log"], log_rows):
    check(f"topology log entry {num} prefix matches the document",
          rec["freeze_base_sha"][:len(prefix)], prefix)
check("the current topology log entry is the recorded freeze_base_sha", base,
      fa["topology_amendment_log"][-1]["freeze_base_sha"])

doc_cats = re.findall(r"^\s+\((i|ii|iii|iv|v)\)\s+(.+?)$",
                      doc.split("S2   that closure references nothing")[1].split("E5-M0 records")[0], re.M)
cats = m0["s2_deny_list"]["categories"]
check("exactly five S2 categories, and no sixth", 5, len(cats))
check("S2 category ids", ["i", "ii", "iii", "iv", "v"], [c["id"] for c in cats])
for c, (did, dtext) in zip(cats, doc_cats):
    check(f"S2 category ({did}) text begins as the document states",
          True, c["category"].startswith(dtext.strip().rstrip(",")[:30]))
v = next(c for c in cats if c["id"] == "v")
check("S2 (v) retains the 'used to reach past a declared interface' qualifier",
      True, "used to reach past a declared interface" in v["category"])
check("S2 (v) introduces no static-type narrowing",
      True, any("NO narrowing by the expression's current static type" in a
                for a in v.get("applicability", [])))

fs = m0["frozen_surfaces_by_reference"]
check("by-reference block names the frozen document blob", fs["blob_sha"], fa["E5_DOC_BLOB_SHA"])
unresolved = [s for refs in fs["surfaces"].values()
              for s in re.findall(r"§(\d+(?:\.\d+)?)", refs)
              if not re.search(rf"^#{{2,3}} {re.escape(s)}[ .]", doc, re.M)]
check("every referenced section resolves to a heading in the document", [], unresolved)

cd = m0["canonicalization_and_digest"]
check("canonicalization", "RFC 8785 JSON Canonicalization Scheme (JCS)", cd["canonicalization"])
check("digest", "SHA-256, lowercase hex", cd["digest"])

# ────────────────────────────────────────── informational, gates nothing
print("\ninformational — NOT an M0 obligation and NOT a gate")
sf_path = m0["spec_facts_identity"]["transcription_artifact"]["path"]
sf_name = sf_path.split("/")[-1]
print(f"  ..    {sf_name}  sha256 = {hashlib.sha256(blob_bytes(HEAD, sf_path)).hexdigest()}")
print(f"  ..    {sf_name}  blob   = {git('rev-parse', f'{HEAD}:{sf_path}')}")
print(f"  ..    normative identity is §5.4 of the document at {fa['E5_DOC_BLOB_SHA']}")
print(f"  ..    neither value gates anything (§14.3 does not enumerate this artifact)")

print(f"\n{n - len(fails)}/{n} recorded audit values equal the computed ones")
if fails:
    print("\nMISMATCHES — INVALID_EXPERIMENT under §12.2 G0:")
    for f in fails: print("  -", f)
    sys.exit(1)
