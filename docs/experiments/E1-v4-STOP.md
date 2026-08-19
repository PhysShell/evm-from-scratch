# E1-v4 — STOP_UNFREEZABLE_PREREGISTRATION

**Outcome:** E1-v4 halts **before its freeze event**. The preregistration was written, reviewed
and rejected; no merge froze it, no `M0-v4` exists, and step 6a was never reached.

**Cause:** two independent defects in the preregistration itself, either of which is
disqualifying. It smuggled a **second decision-rule amendment** past a one-amendment
contract, and it was **shaped by outcomes observed before the freeze it was asking for**.

This is the first E1 stop that happens on the *near* side of a freeze. The previous three
stopped a frozen protocol that turned out to be defective; this one stops a protocol from
being frozen at all. That is a better failure and it is worth saying so plainly: the review
caught it in the one window where catching it is free.

---

## 1. The two blockers

### 1.1 §3.10 is a second amendment wearing a consequence's clothing

Frozen Step 2 §8.2.2 is a **total** procedure with exactly two outcomes:

```text
first candidate that covers the arm
    -> emit LT-BR-<unit>-<nnn>, inputs recorded verbatim

no candidate covers it within B
    -> NO_FROZEN_BRANCH_WITNESS, stop, preserve the record
```

It says nothing about host exceptions, because under the `bytes` domain none could arise.
The draft's §3.10 added a third path:

> A candidate whose evaluation raises a host-level error outside the frozen semantics […] is
> recorded as **NOT COVERING** the arm. The search proceeds to the next candidate.

**That is an amendment to the branch-search decision rule, and it is independent of A2.** The
document presented it as a consequence of introducing programs. It is not: host errors are a
property of *candidate evaluation*, not of the code domain, and the same rule would change
behaviour under any domain at all.

**It can change which witness is selected, which is the whole game.** Coverage counters
increment as the candidate executes. A candidate that covers arm `A` at instruction 40 and
then raises `RangeError` at instruction 300 has genuinely covered `A` — it *is* "the first
candidate that covers the arm" in §8.2.2's sense. §3.10 discards it and lets a later, different
candidate be emitted as `LT-BR-*` instead. The recorded fixture for that arm then depends on a
rule the frozen document does not contain.

And it silently totalises a procedure that was deliberately partial: §8.2.2's second outcome
is a *stop*, and a rule that keeps the search running past an unexpected condition converts a
halt into a shrug.

### 1.2 §3.12 observed outcomes, then wrote a decision rule from them

The draft disclosed, in §3.12, that `D_program` had been rendered **and executed** against the
inherited clean Baseline B, and recorded quantitative results: program lengths 11 641–11 707
bytes, stack depth 357 of 1024, ≤ 3 ms per member, and **10 of 35 members raising a host
error**. It called this a well-formedness check.

The label does not survive contact with what the numbers were then used for:

```text
observation                          what it went on to determine
-----------                          ---------------------------
10 members raise RangeError          §3.10's existence, and its first named class
callee can re-enter through CALL     §3.10's second named class, and §3.9's retraction
                                     of the cross-frame termination claim
address operand never meets a
World shape at index 0               prediction P3, and its opposite P3'
```

A decision rule derived from observed execution outcomes is precisely what preregistration
exists to prevent. Step 0 §0 fixes the governed documents at the first measured run of the
artefact they govern; experiments README principle 2 requires decision rules to be frozen
*before* the outcomes they will be applied to are seen. Both were violated in the same
direction, and disclosing the dry run in §3.12 does not undo it — **it is the reason the defect
was findable, not a licence for it.**

The distinction the draft leaned on — "no coverage was collected, no arm was consulted" — is
the same distinction the step-6a discovery figures were held to under v3, where the ruling went
the other way: non-adjudicating is not the same as not measured, and those figures were barred
from ever being cited as adequacy evidence. Applying the looser standard here, to the document
doing the freezing, would have been the exact inversion of that ruling.

## 2. Why this is not repairable in place

Blocker 1.1 alone would be an ordinary revision: split §3.10 out, name it `A3`, and let the
reviewer judge two amendments instead of one.

Blocker 1.2 cannot be edited away. The observations happened, and they are in the causal
history of §3.10, §3.9's retraction and P3′. Deleting §3.12 would remove the disclosure and
keep the contamination — strictly worse. Rewriting the rules "as if" the dry run had not
happened is not available to anyone who remembers it.

So the only honest options were to freeze a document known to be contaminated, or not to freeze
it. **`E1-v4` is not frozen.** PR #5 stays unmerged as a freeze event; the branch is
re-purposed to carry this record.

## 3. What is preserved, and what it may be used for

The v4 preregistration document is kept, unmerged-as-a-freeze and marked as such. It is the
record of what was attempted and why it was refused, and `A2` — the substance, `bytes ≠
executable program` — is unaffected by either blocker and carries forward.

The dry-run figures in its §3.12 are **prior calibration**. They may be disclosed as such, in
those words, and they may not be presented as measurements obtained under any later freeze. A
successor that quotes them must say where they came from.

## 4. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no
defect was injected, no calibration figure exists. This is the fourth E1 stop, and the same
sentence is owed each time: a growing pile of stop records is not a growing pile of negative
findings.

**Clean Baseline B stands, unchanged and unmeasured under v4.** 213/213 core green, both oracle
slices green, the frozen tests never edited — carrying the inherited limitation recorded in
[`records/v3-review-findings.md`](../../experiments/e1/records/v3-review-findings.md): at least
4 case IDs incompletely realise 2 frozen postconditions.

## 5. Preserved chain

```text
bd36306   freeze event (E1-v3)
   │
   ├── 39b1b4b → c054ef9   the v3 line, stopped at 6a
   ├── f76f4ec → efa283d   review findings and their accounting
   │
8aee9ff   PR #4 — v3 history closed into `main`
   │
c868281   the E1-v4 preregistration — WRITTEN, REVIEWED, NOT FROZEN
   │
   └────── this record
```

## 6. Continuation

`E1-v5` opens from a new history-closing base, by the same two-merge discipline. It carries
`A2` forward and must resolve the candidate-evaluation question **explicitly**, in one of two
ways — the choice belongs to the reviewer, not to the author:

```text
(a)  A2 alone. Any host-level failure during branch search is a protocol STOP,
     restoring §8.2.2's two-outcome shape instead of extending it.

(b)  A2 plus an explicit A3 governing candidate evaluation and host-error
     handling, preregistered and reviewed as a second amendment in its own right.
```

`B` and the index-sum record order are not touched under either. Whichever is chosen, the v5
document must be written knowing that the dry-run facts are already known — and must say so,
rather than presenting a rule shaped by them as though it had been derived from the frozen
semantics alone.
