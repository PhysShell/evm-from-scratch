# E1-v2 — preregistration

**Status:** a **new** preregistration, opened because
[E1-v1 stopped](./E1-v1-STOP.md) with `STOP_SPECIFICATION_CONFLICT`. It is not an edit of
the v1 documents, which remain frozen and unmodified.

**Frozen on merge**, under the same rule the v1 documents carried: nothing here may be
revised after the first measured run of the artefact it governs; a revision after that point
produces `E1-v3`.

---

## 1. Inheritance

E1-v2 adopts, unchanged and by reference, the v1 documents at the exact blobs measured under
v1:

```text
c294d724ce50952db4642f9ef757a3f7a6bf33b6   E1-step0-preregistration.md
586bb92f66d9c6c889a9c2266832264d526a87b4   E1-step2-semantics-and-plan.md
```

Everything in them applies to v2 **except** the single amendment in §2. Inheriting by blob
sha rather than by copying is deliberate: duplicating roughly two thousand lines of frozen
specification to relocate one row would create two texts to keep in step, and drift between
them would be a worse defect than the one being repaired.

## 2. The amendment — one row, and the counts that follow from it

### 2.1 `SEM-RUN-4` is a level-B postcondition

Step 2 §3.1's table is headed *Level A* and contains:

```text
| SEM-RUN-4 | U-RUN | 1 | GAS pushes MAX_UINT256 (Step 0 §1.2) |
```

`GAS` is a level-**B** opcode (Step 0 §1.2), which the row's own citation says. Under v2,
`SEM-RUN-4` **belongs to level B**, filed with the level-B memory/storage/halting group.

Everything else about it is unchanged: the same unit (`U-RUN`), the same single case, the
same value (`MAX_UINT256`, pinned by upstream #84), the same test ID `LT-SEM-RUN-4`, and it
still survives the observation projection.

### 2.2 Consequences, computed rather than asserted

**Postcondition counts** — Step 2 §4's categorical breakdown becomes:

```text
79 postconditions                       (unchanged)
    24  level A                         (was 25)
    13  level-B memory/storage/halting/GAS   (was 12)
     7  entry frame
     8  CALL-family operand contract
    15  producing-side seam
     6  consuming-side
     6  relational
                                        24+13+7+8+15+6+6 = 79
```

**Surviving and excluded are unchanged**: 58 and 21. `SEM-RUN-4` survives the projection
under either filing — it is decided from `U-RUN`'s own stack output.

**The test plan is unchanged, and this is verified rather than hoped.** The 213 core case
IDs are a flat sorted list; which table a postcondition's row sits in does not appear in it.
Recomputed:

```text
plan_core_digest       = 63b4d9f9e1b40a08d2bd3f862ce072fb036bc6401f4360823cc5bfc8d79aae02
c2_control_core_digest = c4273493fd9c001687c9b745df3e1f900a64a3fe746c8d91142298dd3587a051
```

Both identical to v1 and to M0. What *does* move is the level split within those 213:

```text
level A   167 -> 166      LT-SEM-RUN-4 moves out
level B    46 ->  47
total     213 -> 213
```

**Oracle sets are unchanged**: 49 level A, 71 level B in-subset, 6 witnesses, 65 level-B
oracle. Case #84 `GAS` is absent from the level-A set and present in the level-B set — which
is now what both documents say, and was already what the corpus said.

### 2.3 Nothing else changes

No semantics, no projection rule, no case rule, no candidate generator, no branch-search
procedure, no decision rule, no defect or control catalog, no thresholds, no witnesses, no
proxy definition. The amendment is confined to which level one postcondition is filed under
and the two counts that follow.

## 3. Why the amendment is outcome-independent

Stated plainly, because a preregistration amended after a measurement invites exactly this
question.

The v1 measurement produced one adjudicating fact: the level-A implementation passes 49/49
against Step 0's reading. The amendment adopts **that same reading** — the one the
implementation and M0 had already taken, and the one Step 0 stated first and unambiguously.
It does not select between a "convenient" and an "inconvenient" outcome, because both
readings were equally silent about D1–D4: no specimen, no seam, and no calibration figure
existed under v1, and none is affected by which table `SEM-RUN-4` sits in.

The alternative repair — moving `GAS` into level A — was available and is rejected on
grounds recorded before this measurement: Step 0 §1.2 justifies `GAS`'s presence entirely by
the level-B `DELEGATECALL` fixture, so a level-A `GAS` would have no reason to exist in the
frozen subset at all.

## 4. What v2 inherits from v1's measurement, and what it must redo

**Inherited as fact about the toolchain, not as evidence about the specimen:**

- StrykerJS 10.0.0 performs genuine per-test analysis (11.64 tests per mutant against a
  50-test suite), discharging the P-038 §3.3 warning Step 2 §2 had only inherited;
- harness, coverage, mutation and manifest replay all function.

**Redone under v2:**

- the Baseline A **measurement** is re-run against `M0-v2`, on the recorded target revision.
  The v1 figures were taken under a manifest that recorded a contradictory specification, so
  they are preserved as v1's record and not carried across as v2's.

**Not redone:**

- the Baseline A **implementation**. It implements Step 0's reading, which is the reading v2
  adopts, so it is correct as written and is not touched. Rewriting working code to produce a
  fresh commit would add nothing but a new sha to audit.

## 5. Sequence

Step 2 §10 continues to govern, with its steps 1–2 already discharged by the inherited
documents:

```text
3.  M0-v2, then re-run Baseline A on the recorded target revision.
    THIS measurement makes the E1-v2 freeze final.
4.  core local tests — all 213 case IDs
5.  Baseline B, clean
6a. domain realisation, M1
6b. qualification
7.  proxy
8.  injections
```

## 6. Reason for v2, for the record

```text
E1-v1
  documents frozen             0346964508260965a5229b929d9b4d06a8914bf1
       ↓
  M0, no measurement           b694824611a2a3eba3e806de3f847406acf5a6f9
       ↓
  first measured run           affde50ea049681395002861672adab8a8ed74b2
       ↓
  discovered:
      Step 0 §1.1   GAS ∈ level B
      Step 2 §3.1   SEM-RUN-4 (GAS) filed under level A
      — irreconcilable: 49-case slice vs 50-case slice
       ↓
  STOP_SPECIFICATION_CONFLICT  (docs/experiments/E1-v1-STOP.md)
       ↓
E1-v2  this document
```

A null or stopped result is preserved, never deleted — Step 0 §9 and the experiments README
principle 4 both require it. v1's stop is a result about the specification, and explicitly
not a result about boundary blindness.
