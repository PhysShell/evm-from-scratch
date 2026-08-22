# E1-v5 — STOP_PROTOCOL_POSTFREEZE_CHAIN_NONCONFORMANT

**Outcome:** E1-v5 halts. `M1` was not written and no adjudicating figure was produced.

**What the outcome means.** The v5 preregistration and its freeze event are valid and stand on
their own. **Everything the protocol built after the freeze is nonconformant** — not only the
step 6a search, but the artefact it consumed (`D_program`) and the replay that was supposed to
bind the manifest to the protocol version. No figure, index, ID or digest produced downstream
of the freeze may be promoted to frozen-procedure evidence.

An earlier version of this record named `STOP_PROTOCOL_STEP6A_NONCONFORMANT` as the whole
disposition. That was still too narrow, and in a way that mattered: it implied one could keep a
sound `M0` and a sound `D_program` and merely replace the branch search. That is no longer
available. The defect is at the level of the post-freeze chain, so the outcome names that level;
the earlier codes are preserved below as subordinate findings rather than erased.

## 1. The chain, and where it breaks

```text
v5 preregistration + freeze event
        │
        │  VALID independently — §2
        ▼
f670258 freeze
        │
        ├── M0 / replay binding          NONCONFORMANT   §3
        │     ├── version selector is self-supplied
        │     ├── a mandatory rule-5 block is optional/skippable
        │     ├── D_program conformance never established
        │     └── the structural check is weaker than the invariant it claims
        │
        ├── D_program implementation     NONCONFORMANT   §4
        │     └── CALL-family operand typing violates §3.4
        │
        └── Step 6a                      NONCONFORMANT   §5
              ├── Frame.pc omitted
              ├── U-HLT dimension invented
              ├── mutable D_BYTES
              ├── instrumentation provenance unbound
              ├── tooling-gap false-verdict path
              └── inter-file arm order underspecified
```

Two subordinate codes are preserved:

- **`STOP_PROTOCOL_STEP6A_NONCONFORMANT`** — §5, the executed search did not implement the
  parts of the generator that were defined.
- **`STOP_PROTOCOL_ARM_ORDER_UNDERSPECIFIED`** — §5.6, an independent *specification* defect:
  the frozen procedure does not determine its own result. It is not a consequence of any
  implementation error and would survive a perfect implementation.

## 2. What still stands, and why

**The freeze event `f670258` is standing evidence** — but *not* because the generic manifest
replay reported PASS. It stands because its topology and the §4.1 literal predicate can be
established independently of any manifest: two parents, `^1 == 8f5aaed…`, the path absent at
`^1`, present at `^2`, and the merged blob equal to the landed blob. Those are facts about the
commit graph, checkable without trusting `M0`. §3 explains why the replay's own PASS is not what
carries this.

**The v5 preregistration is frozen and unrevised**, and step 6a finalised that freeze.

**Clean Baseline B** is inherited unchanged and unmeasured. Every defect below is in the
post-freeze tooling; none is in `src/`.

## 3. Reason one — the M0/replay binding is nonconformant

### 3.1 The version selector is supplied by the artefact being checked

`manifest-replay.ts` holds the freeze literals as a table and then selects the row with

```ts
const literals = FREEZE_LITERALS[m0.experiment_version ?? ''];
```

Three things must be kept apart here. The **manifest supplies the declaration fields**
`freeze_base_sha` and `freeze_path`. The **verifier's `FREEZE_LITERALS` table supplies the
expected literal values** those fields are checked against — correctly held outside the
manifest. But the **manifest also supplies `experiment_version`, the selector that chooses
which table row applies** — and therefore which expected literals its own declarations are
measured against. That last one is the defect. The file's own comment argues it is safe
because "a manifest that named the wrong version would be judged against that
version's base and path, and its own freeze merge introduces neither". That holds only for an
*incoherent* mis-declaration. A coherent one — version, base, path and freeze SHA all moved
together to a genuine older freeze — passes.

Demonstrated, with a manifest carrying the v5 `program_domain` block and E1-v3 freeze fields:

```text
freeze event bd363066c900 — E1-v3 §3.1
ok    manifest freeze_base_sha matches the frozen literal
ok    manifest freeze_path matches the frozen literal
ok    freeze (a)…(e)                      all PASS
ok    freeze ordering: HEAD is a descendant of the freeze

program domain — E1-v5 §3.7, binding rule 5
ok    |Σ| … |D_program| … d_program_digest … §3.9 all 37 members

manifest replay: M0 agrees with every primary source
```

Fully green while certifying the **v3** freeze under a v5 program-domain heading. Nothing binds
the declared version to the file it came from, to the governing documents, or to anything outside
the manifest. (The demonstration file was deleted and never committed.)

This does not unsettle `f670258` — §2 establishes that independently. What it unsettles is the
claim that the generic replay reliably binds an arbitrary `M0` to the protocol version that `M0`
declares.

### 3.2 Binding rule 5 was not discharged

Frozen §4.2 rule 5 requires:

> `M0-v5` MUST additionally recompute `D_program` **from §3.2-§3.7** and record its member count
> and digest…

The replay recomputes the digest by calling the same `buildDomain()` that produced the recorded
one. Since that implementation violates §3.4 (§4 below), the check establishes

> *`M0` and this implementation of `buildDomain()` agree with each other*

and **not**

> *this implementation conforms to frozen §3.2–§3.7*

Rule 5 promised the second. The replay's `|Σ|`, plain-block count, terminal-variant count,
`|D_program|` and digest results remain true **as properties of the artefact that was actually
built** — an artefact that does not implement §3.4. They are not standing evidence that the
`D_program` implementation is conformant, and this record no longer claims they are.

**The sole-trailing-`JUMPDEST` result is removed from that list**, because it is not merely
recorded under a loose label — the predicate does not enforce the invariant it names.
`soleTrailingJumpdest()` returns `true` for any member with *no* jumpdests at all, so the two
intentionally anchorless members pass through the same branch that an **accidentally** anchorless
generated program would:

```text
member     len  jumpdests  lastByte  predicate
ε            0          0    (none)  true
p_trunc      1          0      0x7f  true

members WITH a trailing jumpdest anchor : 35 of 37
members the check calls compliant       : 37
```

What is true of the artefact actually built is the **role-specific** statement: all **35
generated `p(j,t)` members** carry exactly one `JUMPDEST` and it is the final byte, while `ε` and
`p_trunc` are anchorless by construction. The replay's boolean does not establish that
distinction and must not be presented as doing so.

### 3.3 A mandatory obligation is skippable

The whole of the rule-5 section is guarded:

```ts
if (m0.program_domain) { … }
```

Frozen §4.2 rule 5 says `M0-v5` **MUST** recompute `D_program`. Treating the block's presence as
an optional feature means a v5 manifest that simply omits it loses the member count, the digest
and the structural assertion — silently. Replayed with the block deleted:

```text
freeze event f670258f1e7e — E1-v5 §4.1
ok    (a)…(e) and the ancestry check          all PASS
      measured target (HEAD) add0a0975eb4

manifest replay: M0 agrees with every primary source
exit=0
```

No program-domain section, no warning, exit 0. (Demonstration file deleted, never committed.)

Preserved as **historical verifier evidence**, not repaired. Taken with §3.1 this is the same
defect twice: the artefact under test controls not only *which criteria* apply to it, but
*whether a mandatory obligation exists at all*.

## 4. Reason two — `D_program` does not implement frozen §3.4

§3.4 assigns the `address` operand of `CALL` / `STATICCALL` / `DELEGATECALL` to the §8.2.1
**address** domain, every other operand to the uint256 domain.

`render()` pushes operands `k = 0 … need-1`, so `k = need-1` ends on top of the stack, and
`popOperands` consumes top-first in the §2 order `gas, address, value, …`. The address therefore
belongs at `k = need-2`:

```text
CALL          need=7    gas k=6    address k=5
STATICCALL    need=6    gas k=5    address k=4
DELEGATECALL  need=6    gas k=5    address k=4
```

The generator fixes `addressOperand = 1` for all three. Decoded from a real member at `j = 1`,
where the two domains differ:

```text
member p(1, STOP)                       j=1 -> address 0x…0aaa, uint256 1

pushes before CALL (bottom -> top)      k=0  0x1
                                        k=1  0x1000000000000000000000000000000000000aaa
                                        k=2..6  0x1

popOperands binds                       gas         0x1
                                        address     0x1
                                        value       0x1
                                        argsOffset  0x1
                                        argsSize    0x1
                                        retOffset   0x1000…0aaa   <-- the address value
                                        retSize     0x1
```

The address-domain value lands in `retOffset`; the `address` operand receives a plain uint256.
`k = 1` maps to `retOffset` in both the 7- and 6-operand layouts, so all three kinds are affected.

**This is wrong at the level of the program bytes**, not merely in how a later search consumed
them — so it precedes step 6a in the chain and cannot be cured by replacing the search.

**Not repaired here.** Correcting `addressOperand` changes the rendered bytes, hence
`d_program_digest`, hence `M0-v5`. `M0-v5` is not edited and the digest is not recomputed.

## 5. Reason three — the step 6a execution is nonconformant

Preserved from the previous disposition as a subordinate finding,
`STOP_PROTOCOL_STEP6A_NONCONFORMANT`.

**5.1 `Frame.pc` omitted.** §8.2.1 states "`Frame.pc` from `uint256`" and "`Frame` has nine
fields"; `src/domain.ts` carries `Declaration order is the §8.2.1 enumeration order` with `pc`
second of nine. `FRAME_FIELDS` has eight entries and `frameFrom` hard-codes `pc: 0`, so `U-RUN`,
`U-CALL`, `U-STO`, `U-GRD`, `U-HLT` and `U-RET` all enumerated a non-frozen stream. Replaying
both streams for the recorded U-CALL fixture: index **796** as executed, **886** under the
reconstructed frozen stream.

**5.2 `U-HLT` invents an input dimension.** Frozen §1.3 declares its inputs as
`frame, offset, len`. The tool adds a `halt` field, and `exercise` passes `RETURN`/`REVERT` while
`describe` reports `NORMAL`/`EXCEPTIONAL`. Relabelling would only make the report honest about a
stream that is still wrong. (`U-RET`'s `halt` is legitimate — §1.3 gives it `frame, a
FrameResult`.)

**5.3 The byte domain became runtime state.** `ensure()` returns early when the buffer already
covers the write and `mstore` then writes into it; `D_BYTES[2]` is exactly one word, and the
`U-MEM` record hands the domain member in directly:

```text
bytes[2] before   66,66,66,66,66,66,66,66 …
bytes[2] after    0,0,0,0,0,0,0,0 …
same object       true
```

One candidate destroys a frozen domain member for every later candidate and arm; enumeration
became history-dependent.

**5.4 Instrumentation provenance unbound.** `istanbul-lib-instrument` (6.0.3) and `source-map`
(0.7.6) fix arm enumeration order and arm positions, and therefore every ordinal — yet both are
transitive, absent from `package.json` and absent from `M0-v5`'s `toolchain` set, which is the
only thing replay checks.

**5.5 A tooling gap can print as a verdict.** A missing `UnitRecord` or instrumentation entry
falls through toward `unwitnessed`, which prints under the `NO_FROZEN_BRANCH_WITNESS — Step 2
§8.2.2` heading. Both branches are unreachable in this run. Recorded, not repaired; `E1-v6` must
fail closed.

**5.6 The inter-file arm order is underspecified.** `STOP_PROTOCOL_ARM_ORDER_UNDERSPECIFIED`,
independent of every implementation defect above. §8.2.2 iterates "in frozen source order" and
§8.2 allocates `LT-BR-*` "in ascending order of source position", but no frozen text defines a
total order between files. Three concrete admissible orders give three distinct results:

```text
executed alphabetical   two witnesses, then jmp.ts exhausts B
§1.3 unit order         U-DEC and U-JMP precede U-CALL — LT-BR-U-CALL-001 never emitted
mem.ts before jmp.ts    U-MEM's domain holds 2²⁵⁶−1 — the §3.10 evaluation stop, candidate 11
```

Not repairable in v5: adding a file-order rule after measurement would choose which of three
already-known outcomes becomes the record.

## 6. The raw run — preserved, non-admissible

```text
LT-BR-U-CALL-001  src/call.ts:44:42  candidate 796
LT-BR-U-DEC-001   src/dec.ts:22:25   candidate 1
NO_FROZEN_BRANCH_WITNESS   src/jmp.ts:17:27
arm identity      103 by source position, 20 by matched sibling, 0 disagree
§3.10 reachable   candidate 11, U-MEM RangeError
```

> **NON-ADMISSIBLE PROTOCOL EVIDENCE.** A historical observation of one tool in one environment.
> No `LT-BR-*` ID is allocated, no candidate index is a frozen index, no stop is the frozen
> procedure's stop.

**No ID is selectively salvaged.** The reconstructed frozen stream happening to reach the same
U-CALL fixture inside budget is not a reason to keep `LT-BR-U-CALL-001`.

Two source-level observations survive because they need no run: the `jmp.ts` `code[pc] ?? 0` arm
cannot execute under `while (pc < code.length)`, while the identical idiom at `src/dec.ts:22` is
reachable via `SEM-DEC-3` — dead in one unit, live in the other, indistinguishable in a coverage
report. §8.2.2 decides no reachability question and neither does this record.

## 7. Scope

**Nothing is established or refuted about boundary blindness.** No specimen was built, no defect
was injected, no calibration figure exists. `M1` does not exist, and **E1-v5 §7** — the
preregistration's sequence, not §7 of this record — makes it a precondition for any adjudicating
figure.

**Predictions P1–P4 are unadjudicated.**

**Amendment `A2` is neither validated nor falsified.** It remains frozen and untouched, and no
defect above is about it. Its support cannot be drawn from this run: the two witnesses are
non-admissible, and, with §3.2 and §4, **even its post-freeze implementation binding did not
happen** — the artefact that was supposed to realise the amendment's program domain does not
implement §3.4, and the replay that was supposed to establish conformance established only
self-agreement.

**Clean Baseline B stands**, inherited unchanged, carrying its recorded limitation that at least
4 case IDs incompletely realise 2 frozen postconditions.

## 8. Preserved chain

```text
8f5aaed   PR #5 — the stopped, never-frozen v4 closed into `main`
   │
2b640e7   the E1-v5 preregistration, reviewed
   │
f670258   FREEZE EVENT (E1-v5) — valid, established independently of the replay
   │
baf6eb3   M0-v5 and the D_program generator — no measurement, and §3–§4 nonconformant
   │
   └────── step 6a: executed, finalising the freeze, and not admissible
```

PR #8 merges as **history closure**, by ordinary merge preserving the audit chain — not as a
successful measured step 6a.

## 9. Continuation — what `E1-v6` must freeze before executing anything

```text
(a) a TOTAL ARM ORDER determined by the specification alone, frozen without reference to which
    arms are currently red, since all three outcomes in §5.6 are already known.

(b) the exact PER-UNIT INPUT-RECORD CONSTRUCTION from §1.3 + §2, including `Frame.pc` and with
    no invented dimensions.

(c) FRESH OR IMMUTABLE candidate values, so enumeration is history-independent.

(d) EVERY RESULT-BEARING INSTRUMENTATION DEPENDENCY in the bound toolchain and checked by
    replay — transitive presence is not binding.

(e) FAIL-CLOSED treatment of missing records, missing arm mappings and tooling gaps.

(f) OPERAND-ROLE BINDING derived from ONE frozen operand schema that fixes pop-order and type
    together, rather than a hand-maintained `addressOperand` index — plus an independent
    structural check of a generated CALL block, so the generator cannot confirm itself.

    That structural verifier must be ROLE-SPECIFIC, not one disjunctive boolean:

        member 0, ε        MUST be empty and have no jumpdest
        each p(j,t), 35    MUST have exactly one jumpdest, and it MUST be the final byte
        p_trunc            MUST be exactly the truncated PUSH32 member, and have no jumpdest

    A single predicate covering all three roles is what lets an accidentally anchorless
    generated member pass through the branch meant for the two intentionally anchorless ones.

(g) THE VERIFIER'S VERSION SPECIFIED OUTSIDE THE MANIFEST IT CHECKS, **and every
    version-mandatory manifest block REQUIRED FAIL-CLOSED** — never guarded by artefact-supplied
    presence. The blunt option is the good one: a separate `verify-m0-v6.ts` holding a literal
    `EXPECTED_VERSION = 'E1-v6'`. A generic `--expect` is acceptable only if the invocation
    carrying `--expect E1-v6` is itself part of the frozen protocol.
```

Prefer **one canonical record-schema source** from which the generator is constructed, rather
than another handwritten table plus a checker for that table. §4 and §5.1–§5.2 are all what a
second handwritten copy produces.

The oldest open question stands, now last in line: **what the branch-completion rule does with an
arm that cannot execute.** Step 0 §3.1.3 rule 2 asks for one test per uncovered branch; §8.2.2
turns an unwitnessable arm into a stop; neither anticipated arms that exist only to make an
expression total.

## 10. What the external round actually showed

Codex did not find two more scattered bugs. It found **two forms of one disease**, and it is the
disease this experiment exists to hunt:

```text
the implementation supplied its own interpretation of the spec     §4, §5.1, §5.2
the verifier took its criterion selector from the artefact         §3.1
```

Both are ordinary ways for a careful human process to reach a green PASS. Neither survives being
asked to prove itself mechanically — which is the entire point of the exercise, and the reason
this stop is a result rather than a setback.
