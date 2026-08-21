# ai-final-review — shadow-mode pilot

Status: **shadow pilot, non-enforcing.** Nothing in this work blocks a merge,
no required check was added, no ruleset was touched.

Goal of the eventual production rule:

> FINAL ACCEPT is admissible only after a fresh, clean CodeRabbit **full
> review** + Codex review round on the **current** PR HEAD.

Goal of this pilot: not to guess the two providers' behaviour from their
Markdown, but to establish their real, machine-checkable GitHub contract by
experiment, encode it in a fail-closed reducer, and decide honestly whether
the contract is strong enough to enforce.

Everything labelled **OBSERVED** below is backed by a captured artifact from
the controlled pilot on PhysShell/evm-from-scratch PR #11 (2026-08-21), a
sanitized copy of which lives in `governor/pilot/observations/` and — where
it is parser-relevant — in `governor/tests/fixtures/` with a replay test in
`governor/tests/test_live_fixtures.py`. Everything labelled **UNVERIFIED**
is implemented defensively but has never been observed here and must not be
trusted for enforcement.

---

## 1. Architecture

```
GitHub event (webhook)                    reconciliation poll (REST)
        |                                          |
        v                                          v
  webhook.py: verify X-Hub-Signature-256  ->  engine.py ingest_* entrypoints
              dedupe X-GitHub-Delivery             |
        |                                          |
        v                                          v
  route: labeled / synchronize / comment / review / review_comment / reaction
        |
        v
  adapters/ (codex.py, coderabbit.py): admission + normalization
        |                 admission = numeric actor ID + strictly-after
        |                 request server time + generation binding
        v
  store.py (SQLite): review_epochs / provider_runs / webhook_deliveries /
        |            shadow_verdicts — deterministic transitions, no clock
        v
  adapters/common.py: per-provider state resolution (findings-sticky,
        |             latest-terminal-wins, eyes-veto, same-second conflict)
        v
  reducer.py: shadow verdict (fail-closed)
        |
        v
  check.py: ai/final-review-shadow check-run payload (App-only to publish)
```

The engine owns no network. Live transports (or a human running the pilot)
call `ingest_*` with raw GitHub objects; everything downstream is pure and
offline-testable (`python3 governor/run_tests.py`, 90+ tests, no network).

Events are observation triggers, never evidence: nothing changes provider
state until an adapter has admitted a concrete provider-authored artifact.

## 2. State machine

### Review epoch

```
ReviewEpoch { repository_id, pr_number, head_sha, base_sha,
              generation, state, requested_at }
```

One epoch = one review round scope = one exact head. Generations are
monotonic per PR.

```
            label round requested          push (synchronize)
   (none) ----------------------> ACTIVE -------------------> STALE
                                    |                            
                                    | label re-added, same head  
                                    v                            
                                SUPERSEDED                       
```

* `ACTIVE` — the epoch whose verdict is current.
* `STALE` — a newer head exists. Every provider reply bound to this epoch is
  audit evidence only. **Invariant: provider evidence for SHA A must never
  make SHA B clean.**
* `SUPERSEDED` — a newer generation exists for the same head (re-trigger).
  The old generation's request comments no longer accept new bindings.

A push creates the successor epoch immediately (so the current epoch always
describes the current head) but does **not** start a round: a round costs
provider quota and is only started by the explicit trigger label
(`ai-final-review`).

### Provider run

```
REQUEST_PENDING -> REQUEST_BOUND                    (201 with comment id)
               -> REQUEST_OUTCOME_UNKNOWN           (response lost)
               -> REQUEST_FAILED                    (definite error, or
                                                     complete listing +
                                                     window elapsed)
result: PENDING | CLEAN | FINDINGS | RATE_LIMITED | UNAVAILABLE |
        MALFORMED_EVIDENCE | INCONCLUSIVE | STALE
```

### Verdict reducer (pure, no I/O, no clock)

```
1. epoch not ACTIVE, or epoch.head != current head   -> STALE
2. any provider FINDINGS on the current head         -> BLOCKED
3. any provider's evidence only stale-bound          -> STALE
4. codex == CLEAN and coderabbit == CLEAN            -> CLEAN
5. everything else                                   -> INCONCLUSIVE
```

Fail-closed is proven by an exhaustive matrix test: for all 8×8 provider
state combinations, only CLEAN+CLEAN yields CLEAN
(`test_reducer.test_exhaustive_fail_closed_matrix`). Absence of comments,
timeout, skip, rate limit, malformed evidence — none of them is CLEAN.

Per-provider resolution adds:

* **findings-sticky**: once a finding artifact is admitted in a generation,
  no later artifact of the same generation undoes it — a re-review is
  always a new generation;
* latest-terminal-wins otherwise; two conflicting terminals in the same
  server second → INCONCLUSIVE;
* a reaction-basis CLEAN is vetoed by a provider "eyes" at-or-after it
  (prior-art invariant; the reaction path itself is UNVERIFIED here, §4).

## 3. Experimentally established provider contracts

Controlled pilot: PR #11, three heads, `ai-final-review` label applied,
trigger comments posted by the pilot operator. Heads:

```
A = 1bc8038d0339bef67ad145bff85fb04b24e1e24b   (bait file with 2 planted defects)
B = d979642546f29c2a3c032b4146687d40cceaf320   (bait removed)
C = ff74f6f34d10527ff357ebf75b43914722ad1588   (pushed 11s after round-2 triggers)
```

### 3.1 Codex — OBSERVED

Actor: `chatgpt-codex-connector[bot]`, **id 199175422** (matches the
expected ID; first direct observation in this repository).

* **Findings case (round 1, head A):** a `pull_request_review` with
  `state=COMMENTED`, **`commit_id` = head A exactly**, submitted 98s after
  the trigger, plus one inline review comment per finding carrying P1/P2
  severity badges. The review body carries a provider-authored attestation
  `**Reviewed commit:** \`1bc8038d03\`` (10-char short SHA) consistent
  with `commit_id`. Both planted defects were found.
* **Clean case (round 2):** a **new issue comment**:
  `"Codex Review: Didn't find any major issues. Delightful!"` +
  `**Reviewed commit:** \`ff74f6f34d\``. No review object was created for
  the clean case; **no 👍 reaction was observed at any poll**, despite the
  provider's own blurb ("otherwise it will react with 👍").
* **Head binding under mid-flight push:** round 2 was requested while head
  was B; head C was pushed 11s later; Codex attested **C** — it binds its
  run to the head current at run time and says so explicitly. Codex clean
  lineage is therefore *available*, contradicting the prior-art assumption
  (`provider_input_lineage = unavailable` in the codex-review-gate v2
  contract) — the carrier has since gained an explicit attestation.
* **Liveness:** an `eyes` reaction appears on the trigger comment within
  seconds and is **removed after completion** (observed present at 03:16,
  gone at 03:22 for round 1). Reactions are mutable, deletable state.
* Trigger latency observed: 98–117s from trigger comment to terminal
  artifact.

### 3.2 CodeRabbit — OBSERVED

Actor: `coderabbitai[bot]`, **id 136622811**. Plan here: Pro Plus,
auto-review disabled ("fewer than 10 stars"), manual trigger required.

* **Findings case (round 1, head A):** a `pull_request_review` with
  `state=COMMENTED`, **`commit_id` = head A**, body starting
  `**Actionable comments posted: 2**`, containing a Run ID and a
  full-SHA range attestation: *"Reviewing files that changed from the base
  of the PR and between `047ff1a6…` and `1bc8038d…`"*. Inline comments
  carry severity/category markers and committable suggestions; the
  ruff-sourced one is tagged `Source: Linters/SAST tools`. End-to-end
  latency 131s.
* **Ack lifecycle is comment-edit-driven:** the ack comment is created as
  *"Action performed / Full review triggered."* and later **edited in
  place** to *"✅ Action performed / Full review finished."*. "Full review
  finished" is command completion, **not** zero findings — it appeared in
  the same round that posted 2 actionable comments. The reducer never
  treats it as CLEAN.
* **Hard rate limit (round 2):** delivered **only as edits**: the ack
  comment was edited to *"⚠️ Action not completed / Review rate limited."*
  and the sticky comment gained a *"Review limit reached"* warning naming
  the wait (*"Next review available in: 55 minutes"*), a Run ID, and the
  base..head-B range the run would have covered. A `created`-only listener
  never sees the refusal.
* **Soft fair-usage warning ≠ refusal:** the round-2 ack as created said
  *"Action performed / Full review triggered"* **plus** *"included review
  limit is currently reached … may still proceed through usage-based
  billing"*. 17 seconds later the edit turned it into the hard refusal. The
  soft shape classifies as acknowledgement (PENDING), and only the hard
  markers (`Review rate limited`, `Action not completed`,
  `Review limit reached`, `reached your PR review limit`) classify as
  RATE_LIMITED.
* **Real budget:** despite documented plan numbers (Pro+ "10 reviews/hour"),
  the observed allowance was **"up to 1 included review per hour; 0
  remain"**, and CodeRabbit's own docs note the hourly allowance is
  adaptive over a 7-day window. Enforcement design must assume a budget of
  ~1 full review/hour/developer, not 10.
* **The sticky comment is not an evidence carrier:** one comment id
  (5364754026) was observed as placeholder → walkthrough → placeholder+
  walkthrough interleaved (new Run ID) → +rate-limit warning block, via
  in-place edits, with a scope marker (`up to \`1bc80\``) still naming head
  A while the true head was C. Comment surfaces mutate and lag; only
  review objects carry `commit_id`.
* **Clean case (round 3): [PENDING — to be captured when the included
  review budget recovers at ~04:15Z]**

### 3.3 Trigger semantics — OBSERVED

* Commands: `@coderabbitai full review` (full re-review from scratch, per
  docs and the provider's own placeholder text in this repo) and
  `@codex review`.
* Both providers accepted the trigger although the pilot transport appended
  an attribution footer to the comment body — command recognition is
  first-line / substring based, not exact-body based.
* The pilot's trigger actor was the **human owner account via OAuth**
  (PhysShell, id 45852143, `author_association: OWNER`). Both providers
  honored it. **App-authored triggers remain UNVERIFIED** (§4).

## 4. What remains UNKNOWN / UNVERIFIED

1. **App-authored trigger acceptance.** The pilot could only post as the
   owner's OAuth user. Whether either provider honors a mention authored by
   a GitHub App bot account is unmeasured. Probe design: install the
   governor App on a sandbox repo, post the same two commands from the App
   installation token, observe ack/eyes within a fixed window. If ignored,
   the minimal fallback authority is a user-authorized OAuth app acting as
   a dedicated machine user; a PAT is the last resort, not the default.
2. **Codex 👍-reaction clean.** Documented by the provider's own blurb and
   prior art, not observed here (the observed clean carrier was a comment).
   The reaction path stays implemented (with the eyes-veto and
   strictly-after rules) but must not be the load-bearing clean contract:
   reactions are webhookless (GitHub emits **no reaction events**), mutable,
   deletable, and — through this session's tooling — only countable, not
   actor-attributable. If future clean cases arrive reaction-only, a
   production governor needs the REST/GraphQL reactions listing (actor +
   created_at) on a poll loop.
3. **Codex no-start bodies.** The two exact "To use Codex here…" bodies come
   from prior art; Codex was installed here, so no-start was never
   reproduced.
4. **CodeRabbit clean review shape.** `Actionable comments posted: 0` with
   `commit_id` = head is the expected carrier; **round 3 pending**. Until
   observed, CodeRabbit CLEAN is unproven.
5. **CodeRabbit behaviour on synchronize mid-run** — whether an in-flight
   full review re-targets a newly pushed head (Codex does) or completes
   against the requested head. Round 2 was refused before this could be
   measured.
6. **Provider actor ID stability.** IDs were re-confirmed by direct
   observation, but they are configuration, not constants — a production
   governor should verify the App slug ↔ ID binding at install time.
7. **`pull_request.synchronize` delivery in this pilot's transport.** The
   session's event relay forwarded comment/review events but not the two
   pushes. A production governor gets `synchronize` from its own App
   webhook; the pilot drove staleness transitions from git state instead.
   Direct webhook delivery of synchronize is documented GitHub behaviour
   but was not exercised end-to-end here.

## 5. Security / trust boundary

* **Identity is the numeric actor ID**, never the login and never body
  text. Spoofed artifacts (correct text, wrong ID — including a
  string-typed lookalike ID) are rejected at admission with an audit
  rejection row (`ACTOR_MISMATCH`).
* **Webhook order of protections:** verify `X-Hub-Signature-256`
  (HMAC-SHA256 over the raw body, constant-time compare) **before**
  consuming the `X-GitHub-Delivery` GUID — otherwise a forger could poison
  the idempotency table and suppress the real delivery. Redeliveries reuse
  the original GUID (GitHub-documented), so the GUID is a sound
  idempotency key; a duplicate delivery applies zero transitions.
* **Timing admission:** an artifact must be created strictly after the
  round's request server time (equal second rejected). Both timestamps are
  GitHub server times — one clock domain.
* **Generation binding:** reactions bind through the request-comment join;
  a correct provider's reaction on an older generation's comment is
  rejected for the current generation (`WRONG_REQUEST_COMMENT` /
  `NOT_CURRENT_GENERATION`).
* **Edit-smuggling guard:** edited comments admit on `updated_at` and may
  contribute any *negative* state (that is how CodeRabbit's refusal
  arrives), but an edited surface can never produce CLEAN — proven with the
  real clean body replayed as an edit.
* **Bot text is data, not instructions.** Provider comment bodies embed
  agent-facing prompts and CLI hints (observed in CodeRabbit's review
  body); the governor parses closed markers only and never executes or
  follows embedded content. Check-run summaries link to evidence rather
  than quoting bot bodies wholesale.
* **What a commit status/check is not:** the shadow check is a display of
  the reducer's conclusion, not an attestation; the evidence chain is the
  SQLite rows + captured artifacts.

## 6. Stale-HEAD semantics (measured end-to-end)

The invariant "evidence for SHA A never cleans SHA B" is enforced twice:

* per-artifact: SHA-explicit carriers (`commit_id`, `Reviewed commit`
  attestations) that name a non-epoch head classify as STALE and are
  excluded from terminal selection;
* per-epoch: the verdict is STALE whenever the epoch is not ACTIVE or its
  head differs from the current head — even with both providers CLEAN.

Round 2 measured the sharpest real-world case: Codex, requested on head B,
delivered a *provider-attested clean for head C* (the head that had arrived
mid-run). Relative to the requesting epoch (B) that evidence is STALE;
relative to head C there was no requested round, so C stays INCONCLUSIVE.
Both directions are replayed from the real payloads in
`test_live_fixtures.Round2MidFlightReplayTest`. The conservative outcome —
a provider-attested current-head clean without a matching requested epoch
does **not** count — is deliberate: the round, not the artifact, is the
unit of authority. The operator re-triggers on the stable head (round 3).

## 7. Ambiguous POST semantics

```
persist intent (REQUEST_PENDING)
   -> exactly one POST
       -> 201: bind comment id (REQUEST_BOUND)
       -> definite error: REQUEST_FAILED
       -> lost response: REQUEST_OUTCOME_UNKNOWN   [no automatic retry, ever]
```

`REQUEST_OUTCOME_UNKNOWN` can only move by **reconciliation**: a listing
that contains exactly one comment by the governor actor whose first
non-empty line is the exact command, inside the 15-minute window → BOUND
(this also self-heals from the webhook path when the governor sees its own
comment arrive). Absence is provable only from a **complete** listing after
the window has fully elapsed → FAILED. Multiple indistinguishable matches
stay UNKNOWN for a human. A POST is never proof the provider started;
start evidence only ever comes from provider-authored artifacts.

## 8. Exact evidence accepted for CLEAN / FINDINGS

### CLEAN (all conditions, per provider)

Codex (OBSERVED carrier):

```
issue_comment, created (not edited), actor id == 199175422
AND created_at strictly after this generation's request comment time
AND body matches "Codex Review: Didn't find any (major )issues"
AND body attests **Reviewed commit:** `<short-sha>`
AND epoch.head_sha starts with <short-sha>
AND epoch is ACTIVE and epoch.head_sha == current PR head
```

Codex (UNVERIFIED carriers, implemented defensively): a `+1` reaction on
this generation's request comment, strictly after request time, not vetoed
by an eyes at-or-after it; an APPROVED/clean-bodied review with
`commit_id == head` and zero inline comments.

CodeRabbit (expected, **round-3 pending**):

```
pull_request_review, actor id == 136622811
AND submitted_at strictly after this generation's request comment time
AND review.commit_id == epoch.head_sha
AND body matches "Actionable comments posted: 0"
AND epoch is ACTIVE and epoch.head_sha == current PR head
```

A comment-carried "Actionable comments posted: 0" (no `commit_id`) is
INCONCLUSIVE, never CLEAN. "Full review finished" is never CLEAN.

The shadow gate then requires `codex == CLEAN AND coderabbit == CLEAN AND
epoch.head == current head` — with CLEAN unreachable for a provider by any
path other than the above.

### FINDINGS (any of, per provider — deliberately weaker preconditions)

* CodeRabbit review with `Actionable comments posted: N>0` (OBSERVED), or
  `CHANGES_REQUESTED`, or inline comments on an unparseable review;
* Codex review with inline comments (OBSERVED) or `CHANGES_REQUESTED`;
  each Codex inline comment is independently FINDINGS (Codex posts only
  P0/P1);
* SHA-mismatched variants of the above are STALE, not FINDINGS, for this
  epoch.

Negative evidence may bind with weaker lineage than positive evidence —
blocking on a possibly-stale finding is safe; cleaning on one is not.

## 9. Deliberate non-goals of this pilot

No merge queue; no distributed consensus; no git-backed transactional
ledger (SQLite is the runtime state; git holds code and sanitized
captures); no generic bot framework; no production retry scheduler; no
automatic merging; no required check or ruleset change; no provider
finding ontology (findings count, they are not modeled); no CI workflow
changes; no changes to E1/E5 scientific state. The probe PR (#11) used its
own disposable files and is closed unmerged.

## 10. Prerequisites for production activation

1. **A governor GitHub App.** Non-negotiable: only GitHub Apps can create
   check runs (`ai/final-review`), and the governor needs its own webhook
   (with secret) for `pull_request`, `issue_comment` (created **and**
   edited), `pull_request_review`, `pull_request_review_comment`. The
   pilot's OAuth-user identity can post triggers but cannot publish checks.
2. **Measured answer to the App-authored-trigger question** (§4.1) — or a
   designated trigger authority that providers demonstrably honor.
3. **CodeRabbit CLEAN observed** (round 3) and re-observed after any
   provider-side format change; the fixtures in `tests/fixtures/` are the
   regression bar.
4. **Budget-aware rounds:** with ~1 included CodeRabbit review/hour, a
   final-review label applied more than once an hour rate-limits; the
   governor must surface RATE_LIMITED verdicts and the provider's own
   recovery time rather than retrying.
5. **Reaction observability** if the Codex 👍 path is ever load-bearing:
   an authenticated reactions listing (actor + created_at) on a poll loop,
   since no webhook exists.
6. **A reconciliation loop** (poll comments/reviews on a schedule) to close
   REQUEST_OUTCOME_UNKNOWN states and catch missed deliveries; webhooks are
   at-least-once but not guaranteed.
7. Only after all of the above, and a canary period where the shadow check
   agrees with human judgment on real PRs: add `ai/final-review` to the
   ruleset.

## 11. Pilot round log

| round | head | trigger time | CodeRabbit outcome | Codex outcome |
|---|---|---|---|---|
| 1 | A `1bc8038d` | 03:15:11/15Z | FINDINGS: review 4989406397, "Actionable comments posted: 2", commit_id=A | FINDINGS: review 4989404627, commit_id=A, 2 inline P1/P2 |
| 2 | B `d9796425` (C pushed +11s) | 03:19:31/34Z | RATE_LIMITED: ack 5364784582 edited to "Action not completed / Review rate limited" | CLEAN **for C**: comment 5364792938, "Reviewed commit: ff74f6f34d" — STALE for the B-epoch |
| 3 | C `ff74f6f3` | *pending ~04:16Z* | *pending: expected "Actionable comments posted: 0" + commit_id=C* | *pending* |

Shadow verdicts replayed from real payloads: round 1 → BLOCKED; round 2 →
STALE (gen 2) / INCONCLUSIVE (head C, no requested round); round 3 →
*pending*.

## 12. Production recommendation

**[PENDING — finalized after round 3.]**

The recommendation will be NOT_READY_FOR_ENFORCEMENT unless every clause of
§8's CLEAN contracts has at least one captured observation, and will remain
NOT_READY in any case until the §10 prerequisites (governor App identity,
trigger authority, reconciliation loop) exist — the shadow pilot itself has
no identity that could publish the required check today.
