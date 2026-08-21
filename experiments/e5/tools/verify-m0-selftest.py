#!/usr/bin/env python3
"""
Negative controls for verify-m0.py, over a MANDATORY baseline.

The baseline comes first and is not optional. An earlier revision of this file
ran the controls without it, and reported 6/6 green while verify-m0.py was
failing 57/58 on the unmodified manifest — the controls fired on their intended
lines, but the installation was already on fire. Green controls over a red
baseline prove nothing at all, so a failing baseline aborts before a single
control runs.

Each control then corrupts one recorded audit value and asserts verify-m0.py
FAILS on the check aimed at it.

Deliberately small. These are the corruptions that matter: a substituted freeze
merge, a digit-level digest edit, a swapped document identity, a widened deny
list, a quietly dropped frozen qualifier, the design-cutoff/freeze-base
conflation §14.3 names as a defect, and one control for each side of the
revision split that this script's own history proved was needed. There is no
control for "Python still runs".

Exit 0 = the baseline passes AND every control fires on the check it was aimed at.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT   = Path(__file__).resolve().parents[3]
VERIFY = Path(__file__).resolve().parent / "verify-m0.py"
M0     = ROOT / "experiments/e5/manifest/E5-M0.json"

def run(manifest_path):
    return subprocess.run([sys.executable, str(VERIFY), str(manifest_path)],
                          capture_output=True, text=True)

# ─────────────────────────────────────────────── baseline, before anything else
print("baseline")
b = run(M0)
if b.returncode != 0:
    bad = [l.strip() for l in b.stdout.splitlines() if l.strip().startswith("FAIL")]
    print("  FAIL  unmodified E5-M0 does not pass verify-m0.py")
    for l in bad: print("          ", l)
    print("\nAborting: negative controls over a failing baseline prove nothing.")
    sys.exit(1)
print(f"  ok    unmodified E5-M0 passes  ({b.stdout.strip().splitlines()[-1]})\n")

# ─────────────────────────────────────────────────────────────────── controls
def tamper_M(m):         m["freeze_anchor"]["M"] = "0" * 40
def tamper_digest(m):
    d = m["artifacts"]["schema_certificate"]["sha256"]
    m["artifacts"]["schema_certificate"]["sha256"] = ("1" if d[0] != "1" else "2") + d[1:]
def tamper_docblob(m):   m["freeze_anchor"]["E5_DOC_BLOB_SHA"] = "f" * 40
def sixth_category(m):
    m["s2_deny_list"]["categories"].append(
        {"id": "vi", "category": "anything else we thought of later", "typescript_realization": []})
def drop_v_qualifier(m):
    v = next(c for c in m["s2_deny_list"]["categories"] if c["id"] == "v")
    v["category"] = "reflection, dynamic member access, or serialization round-trip"
def conflate_cutoff(m):
    m["design_cutoff"]["E5_DESIGN_CUTOFF_SHA"] = m["freeze_anchor"]["freeze_base_sha"]
def tamper_scan_count(m):
    m["freeze_anchor"]["M_evidence"]["f_commits_scanned"] += 1
def tamper_step2_blob(m):
    m["spec_revisions"]["spec_revision"]["blob_sha"] = "a" * 40

CONTROLS = [
    ("C1  freeze merge M substituted",
     "recorded M equals the M computed from the audit tree",              tamper_M),
    ("C2  one hex digit of a schema digest changed",
     "sha256 E5-CERT-v1.schema.json unchanged at HEAD",                   tamper_digest),
    ("C3  document blob identity swapped",
     "recorded E5_DOC_BLOB_SHA",                                          tamper_docblob),
    ("C4  a sixth S2 category added",
     "exactly five S2 categories, and no sixth",                          sixth_category),
    ("C5  the (v) 'reach past a declared interface' qualifier dropped",
     "retains the 'used to reach past a declared interface' qualifier",   drop_v_qualifier),
    ("C6  design cutoff conflated with freeze base",
     "E5_DESIGN_CUTOFF_SHA matches §1.1",                                 conflate_cutoff),
    ("C7  historical scan count altered  (section A, audit-tree relative)",
     "(f) commits scanned matches the recorded count",                    tamper_scan_count),
    ("C8  frozen Step 2 read-set blob altered  (section C, cutoff relative)",
     "spec_revision (E1 Step 2) at the design cutoff",                    tamper_step2_blob),
]

failures = []
for label, expected, mutate in CONTROLS:
    m = json.loads(M0.read_text()); mutate(m)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(m, f, indent=2); tmp = f.name
    r = run(tmp); Path(tmp).unlink()
    caught = r.returncode != 0 and any(
        expected in ln for ln in r.stdout.splitlines() if ln.strip().startswith("FAIL"))
    print(f"  {'ok  ' if caught else 'FAIL'}  {label}")
    if not caught:
        failures.append((label, expected, r.returncode,
                         [l.strip() for l in r.stdout.splitlines() if l.strip().startswith("FAIL")]))

print(f"\nbaseline PASS + {len(CONTROLS) - len(failures)}/{len(CONTROLS)} negative controls fired")
if failures:
    print("\nCONTROLS THAT DID NOT FIRE — verify-m0.py is not checking what it claims:")
    for label, exp, rc, got in failures:
        print(f"  - {label}\n      expected FAIL on: {exp}\n      exit={rc} actual={got}")
    sys.exit(1)
