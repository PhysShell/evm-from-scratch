# E1-v3 — preregistration

**Status:** a **new** preregistration, opened because
[E1-v2 stopped](./E1-v2-STOP.md) with `STOP_PROTOCOL_FREEZE_ORDER`. It is not an edit of any
earlier document; v1 and v2 remain frozen, stopped and unmodified.

**Freeze event:** the merge commit that brings *this document* into `main`. Not this
document's own commit, and not any statement inside it. §3 defines the event precisely and
makes it mechanically checkable, because v2 stopped exactly on the difference between
declaring a freeze and having one.

---

## 1. Why v3 exists

v2 said of itself *"Frozen on merge"*, and inherited Step 0 §9 step 1 says *"freeze — this
document reviewed and merged"*. At the moment of the v2 Baseline A measurement, `main` stood
at the roadmap commit `2ea7057` and carried none of the E1 preregistrations. The documents
were committed before measurement — real provenance, preserved — but committed is not
merged.

Merging afterwards could not repair it: the measurement had already happened, and no ordering
of commits places a later merge before an earlier measurement. So v2 stopped, and its history
was merged into `main` at `fbef84cd4a925345d3aa65c2e02d9d7502bea787` for one purpose only —
so that v3 could be opened from a `main` that actually carries the record, and so that v3's
own freeze event can be a real merge commit preceding every v3 measurement.

**v3 introduces no semantic change of any kind.** Its entire content is inheritance plus a
freeze-event definition that can be checked rather than asserted.

## 2. Inheritance

E1-v3 adopts, unchanged and by reference, these documents at the blobs merged into `main`:

```text
c294d724ce50952db4642f9ef757a3f7a6bf33b6   E1-step0-preregistration.md
586bb92f66d9c6c889a9c2266832264d526a87b4   E1-step2-semantics-and-plan.md
a42fa76f702cfa45664198eea809464d87a7b35f   E1-v2-preregistration.md
```

- Step 0 and Step 2 supply the whole specification: the semantic subset, the observation
  projection, the case rule, the candidate generator, the branch-search procedure, the
  thresholds, the decision rule, the staged manifest, the catalog, and the sequence.
- The v2 preregistration supplies **amendment `E1-v2/A1`** — `SEM-RUN-4` is a level-B
  postcondition — which v3 carries forward verbatim, together with every consequence it
  computed:

```text
postconditions      79      24 + 13 + 7 + 8 + 15 + 6 + 6
surviving           58
excluded            21
core case IDs      213      level split 166 A / 47 B
plan_core_digest         63b4d9f9e1b40a08d2bd3f862ce072fb036bc6401f4360823cc5bfc8d79aae02
c2_control_core_digest   c4273493fd9c001687c9b745df3e1f900a64a3fe746c8d91142298dd3587a051
oracle sets              49 level A / 71 level B in-subset / 6 witnesses / 65 level-B oracle
```

Inheriting by blob sha rather than by copying is deliberate and unchanged from v2's
reasoning: duplicating the specification would create two texts to hold in step, and drift
between them would be worse than the defect being repaired.

## 3. The freeze event — defined so it can be checked

This is the only thing v3 adds.

### 3.1 Definition

```text
freeze_merge_sha := the merge commit that brings this document into `main`
```

It is an object in the repository with a timestamp and two parents, not a sentence. Nothing
about the run may be settled by a document asserting its own status.

### 3.2 Binding rules

```text
1.  M0-v3 may exist only on a commit that is a DESCENDANT of freeze_merge_sha.
2.  M0-v3 MUST record freeze_merge_sha in a `freeze_merge_sha` field.
3.  Every measured run MUST be taken on a descendant of freeze_merge_sha, and
    MUST record its own target_revision_sha per Step 0 §8.
4.  Manifest replay MUST verify rules 1-3 mechanically:
        git merge-base --is-ancestor <freeze_merge_sha> <target_revision_sha>
    A replay that cannot establish this fails, and the run is not admissible.
```

Rule 4 is what distinguishes v3 from v2. v2's freeze condition was true or false about the
world and nothing checked it; v3's is checked by the same tool that already recomputes the
digests and the oracle sets, so a violation surfaces the way every other violation in this
experiment surfaces — as a failing replay, not as a reviewer's good eyesight.

### 3.3 What the freeze fixes, and when

Unchanged from Step 0 §0: nothing in the frozen documents may be revised after the **first
measured run** of the artefact they govern. The freeze *event* (§3.1) establishes which
documents are in force; the first measurement makes that set final. Both must happen, in that
order, and under v1 and v2 respectively one of them did not.

A revision required after the first v3 measurement produces `E1-v4`, by the same rule that
produced v2 and v3.

## 4. What carries over from earlier measurements

**Carried as fact about the toolchain, not as evidence about the specimen:**

- StrykerJS 10.0.0 performs genuine per-test analysis — 11.64 tests per mutant against a
  50-test suite — discharging the P-038 §3.3 warning that Step 2 §2 had only inherited;
- harness, coverage, mutation and manifest replay all function.

**Redone under v3:** the Baseline A measurement, on a descendant of `freeze_merge_sha`
against `M0-v3`. Earlier figures were taken before a valid freeze existed and stay attached
to their own stopped versions.

**Not redone:** the Baseline A implementation. It is correct under the inherited
specification and is not touched. It has now been measured identically twice, and a third
identical result will say nothing new about the code — only about the protocol under which it
was taken, which is the whole point of v3.

## 5. Sequence

Step 2 §10 governs. Steps 1–2 are discharged by the inherited documents.

```text
0.  freeze          this document reviewed and merged into `main`.
                    That merge commit is freeze_merge_sha.
3.  M0-v3, then re-run the unchanged Baseline A on a descendant of it.
                    THIS measurement makes the E1-v3 freeze final.
4.  core local tests — all 213 case IDs; 166 level-A green, 47 level-B red
5.  Baseline B, clean
6a. domain realisation, M1
6b. qualification
7.  proxy
8.  injections
```

## 6. Version chain, for the record

```text
E1-v1   STOP_SPECIFICATION_CONFLICT     Step 0 §1.1 vs Step 2 §3.1 over GAS
                                        docs/experiments/E1-v1-STOP.md
E1-v2   STOP_PROTOCOL_FREEZE_ORDER      declared freeze event never occurred
                                        docs/experiments/E1-v2-STOP.md
E1-v3   this document
```

Both stops are preserved, never deleted — Step 0 §9 and experiments README principle 4. And
both are statements about the specification and its protocol. **Neither is a result about
boundary blindness**, and neither may be cited as one: no specimen has been built, no seam
exists, no defect has been injected, and no calibration figure has been produced. The
distinction is the one P-038 §5.1 and Step 0 §6.1 both insist on, and it is worth repeating
once per version precisely because a growing pile of stop records starts to look like a
growing pile of negative findings, and is not.
