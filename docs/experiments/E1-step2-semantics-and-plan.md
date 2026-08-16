# E1 Step 2 — normative semantics, observation projection, and local-test plan

**Status:** frozen on merge, under the rules of
[E1 Step 0](./E1-step0-preregistration.md). This document executes Step 0 §9 step 2 and
authorises step 3 only if §7 below records `step2_definition_gate = PASS`.

**Contains no implementation.** No interpreter, no test code, no measurement.

**Order of authorship, which is itself part of the method:** §1–§4 are written from the
frozen semantics and the frozen boundary alone. §5 (the projection) is computed from them
mechanically. §6 (the paper check) is the *consequence*, read off §5. The catalog of Step 0
§6 is not consulted until §6 of this document, and nothing in §1–§5 may be revised in
response to what §6 reports. If §6 reports an unwelcome result, that result stands and is
recorded in §7.

---

## 1. Component decomposition — and the choice that decides the experiment

### 1.1 The units

| Unit | Responsibility |
|---|---|
| `U-DEC` | instruction decode: opcode and immediate at a program counter |
| `U-STK` | stack: push, pop, dup, swap, depth rules |
| `U-ARI` | `ADD` `SUB` `MUL` `DIV` `MOD` over `uint256` |
| `U-CMP` | `LT` `GT` `EQ` `ISZERO` |
| `U-JMP` | `JUMPDEST` analysis and jump validity |
| `U-MEM` | byte-addressed memory: store, load, size |
| `U-STO` | storage accessor, addressed by a frame's `storage_owner` |
| `U-GRD` | the static write guard |
| `U-HLT` | `STOP` / `RETURN` / `REVERT` → a `FrameResult` |
| `U-CALL` | the `CALL` / `STATICCALL` / `DELEGATECALL` opcode handler |
| `U-RET` | application of a returned `FrameResult` to the calling frame |
| `U-RUN` | the interpreter loop over a frame |

### 1.2 The load-bearing decision: where frame construction lives

The seam is the caller frame → callee frame transition. **Frame construction is internal to
`U-CALL`.** It is not a separately exported unit, and the constructed frame reaches the
outside world only as the argument `U-CALL` hands to `U-RUN`.

This single decision determines whether D1–D3 are blind spots, so it must be justified on
grounds that have nothing to do with them, and its alternative must be stated.

**Why internal.** The frozen semantics (§3) is written before any implementation and
describes *operations*, following the EVM specification's own shape: `CALL`, `STATICCALL` and
`DELEGATECALL` are defined there as single operations with a described effect. There is no
`buildCalleeFrame` in the EVM specification — it is an implementation artifact. A
decomposition derived from the semantics therefore has the opcode handler as the unit and
frame construction as a step inside it.

**The alternative, stated plainly.** Had frame construction been a separately exported
`buildCalleeFrame`, the constructed frame would be *that unit's own return value*, squarely
inside the declared local interface of Step 0 §3.1.2(a). Its postconditions would survive the
projection, acquire local tests, and D1–D3 would be caught locally. **The opposite
decomposition inverts the result.**

**Therefore this is a second scope condition,** and it joins the one in Step 0 §3.1.4. Every
§5.1 result carries both clauses, or it overclaims:

> under a local-testing discipline that asserts through a unit's own interface rather than on
> collaborator arguments, **and** a decomposition in which cross-boundary context construction
> is internal to the calling operation rather than a separately unit-tested factory.

That second clause is not a hedge invented for convenience. It is a real and testable claim
about which codebases have this blind spot: those that build the context object inline, and
not those that build it in a factory with its own tests. That is a finding, and it belongs in
the write-up rather than in a footnote.

### 1.3 The declared local test boundary, per unit

Per Step 0 §3.1.2(a). "Substituted" means a double; "observable" means what the unit itself
returns or the state it owns.

| Unit | Inputs | Substituted | Own observable output |
|---|---|---|---|
| `U-DEC` | code bytes, pc | — | decoded instruction, next pc |
| `U-STK` | a stack value | — | resulting stack, or exceptional halt |
| `U-ARI`, `U-CMP` | operand pair | — | result value |
| `U-JMP` | code bytes, target | — | validity verdict, jumpdest set |
| `U-MEM` | offset, value | — | memory contents, size |
| `U-STO` | a frame, slot, value | world state | storage of `storage_owner` |
| `U-GRD` | a frame | world state | write performed or exceptional halt |
| `U-HLT` | a frame, offset, len | — | `FrameResult` |
| `U-CALL` | a frame, stack args | **`U-RUN`** | caller's stack and memory after the call |
| `U-RET` | a frame, a `FrameResult` | — | caller's stack and memory |
| `U-RUN` | a frame | `U-CALL` | `FrameResult` |

`U-CALL`'s substitution of `U-RUN` is the mock-heavy shape Step 0 §3 requires. The frame it
builds is passed *to* that double and is therefore, by §3.1.2(a), outside what a local test
may assert on.

---

## 2. State model

```text
Frame {
  code            bytes
  pc              uint
  stack           uint256[]        (max depth 1024)
  memory          bytes            (zero-extended on read)
  address         address          the callee executes AS this
  caller          address          what CALLER observes
  static          bool             writes prohibited when true
  storage_owner   address          which account's storage SLOAD/SSTORE reach
  returndata      bytes            from the most recent inner call
}

FrameResult { halt: NORMAL | EXCEPTIONAL, returndata: bytes }

World: address -> { code: bytes, storage: uint256 -> uint256 }
```

`REVERT` is `EXCEPTIONAL` *with* returndata; every other exceptional halt carries none.

---

## 3. Normative semantics

Complete for the frozen subset of Step 0 §1.1–§1.2. Every postcondition carries an ID. All
arithmetic is modulo 2²⁵⁶; all comparisons are unsigned.

### 3.1 Level A

| ID | Unit | Postcondition |
|---|---|---|
| `SEM-DEC-1` | U-DEC | a non-`PUSH` opcode at `pc` decodes with no immediate; next pc is `pc+1` |
| `SEM-DEC-2` | U-DEC | `PUSHn` (n≥1) takes the `n` bytes after the opcode as a big-endian immediate; next pc is `pc+1+n` |
| `SEM-DEC-3` | U-DEC | `PUSHn` with fewer than `n` bytes remaining is zero-padded on the right |
| `SEM-DEC-4` | U-DEC | `PUSH0` takes no immediate and yields the value 0 |
| `SEM-STK-1` | U-STK | push increases depth by 1; the pushed value is the new top |
| `SEM-STK-2` | U-STK | pop decreases depth by 1 and yields the previous top |
| `SEM-STK-3` | U-STK | pop on an empty stack halts exceptionally |
| `SEM-STK-4` | U-STK | `DUPn` copies the n-th item from the top to the top; depth increases by 1 |
| `SEM-STK-5` | U-STK | `SWAPn` exchanges the top with the (n+1)-th item; depth is unchanged |
| `SEM-STK-6` | U-STK | `DUPn`/`SWAPn` with insufficient depth halts exceptionally |
| `SEM-STK-7` | U-STK | a push beyond depth 1024 halts exceptionally |
| `SEM-ARI-1` | U-ARI | operands are popped as `a` then `b`; the result is `a OP b` |
| `SEM-ARI-2` | U-ARI | `ADD`, `SUB`, `MUL` wrap modulo 2²⁵⁶ |
| `SEM-ARI-3` | U-ARI | `DIV` with `b = 0` yields 0; otherwise floor division |
| `SEM-ARI-4` | U-ARI | `MOD` with `b = 0` yields 0; otherwise `a mod b` |
| `SEM-CMP-1` | U-CMP | `LT`/`GT` compare unsigned and yield 1 or 0 |
| `SEM-CMP-2` | U-CMP | `EQ` yields 1 iff the operands are equal |
| `SEM-CMP-3` | U-CMP | `ISZERO` yields 1 iff the operand is 0 |
| `SEM-JMP-1` | U-JMP | the jumpdest set is every offset holding `0x5B` that is not inside a `PUSH` immediate |
| `SEM-JMP-2` | U-JMP | `JUMP` to an offset outside the jumpdest set halts exceptionally |
| `SEM-JMP-3` | U-JMP | `JUMPI` transfers control iff its condition operand is non-zero |
| `SEM-RUN-1` | U-RUN | `PC` pushes the offset of the `PC` opcode itself |
| `SEM-RUN-2` | U-RUN | `STOP` halts normally with empty returndata |
| `SEM-RUN-3` | U-RUN | execution running past the end of code halts normally |
| `SEM-RUN-4` | U-RUN | `GAS` pushes MAX_UINT256 (Step 0 §1.2) |

### 3.2 Level B — memory, storage, halting

| ID | Unit | Postcondition |
|---|---|---|
| `SEM-MEM-1` | U-MEM | `MSTORE` writes 32 big-endian bytes at the given offset |
| `SEM-MEM-2` | U-MEM | `MLOAD` reads 32 bytes at the offset; never-written bytes read as 0 |
| `SEM-MEM-3` | U-MEM | `MSIZE` is the highest touched offset rounded up to a multiple of 32 |
| `SEM-STO-1` | U-STO | `SSTORE` writes to the storage of the frame's `storage_owner` |
| `SEM-STO-2` | U-STO | `SLOAD` reads from the storage of the frame's `storage_owner` |
| `SEM-STO-3` | U-STO | a never-written slot reads as 0 |
| `SEM-GRD-1` | U-GRD | when the frame's `static` is set, `SSTORE` performs no write and halts exceptionally |
| `SEM-GRD-2` | U-GRD | when the frame's `static` is clear, `SSTORE` proceeds |
| `SEM-HLT-1` | U-HLT | `RETURN` yields `NORMAL` with returndata `memory[offset .. offset+len)` |
| `SEM-HLT-2` | U-HLT | `REVERT` yields `EXCEPTIONAL` with returndata `memory[offset .. offset+len)` |
| `SEM-HLT-3` | U-HLT | any other exceptional halt yields empty returndata |

### 3.3 Level B — the seam, producing side (inside `U-CALL`)

| ID | Postcondition |
|---|---|
| `SEM-SEAM-P1` | `CALL` constructs a callee frame whose `address` is the called address |
| `SEM-SEAM-P2` | `CALL` constructs a callee frame whose `caller` is the *current* frame's `address` |
| `SEM-SEAM-P3` | `CALL` constructs a callee frame whose `storage_owner` is the called address |
| `SEM-SEAM-P4` | `CALL` constructs a callee frame whose `static` equals the current frame's `static` |
| `SEM-SEAM-P5` | `STATICCALL` constructs a callee frame whose `static` is **true**, whatever the current frame's is |
| `SEM-SEAM-P6` | `DELEGATECALL` constructs a callee frame whose `address` is the *current* frame's `address` |
| `SEM-SEAM-P7` | `DELEGATECALL` constructs a callee frame whose `caller` is the *current* frame's `caller` — inherited, not the current address |
| `SEM-SEAM-P8` | `DELEGATECALL` constructs a callee frame whose `storage_owner` is the current frame's `storage_owner` |
| `SEM-SEAM-P9` | every call kind constructs a callee frame whose `code` is the code at the called address |
| `SEM-SEAM-P10` | every call kind constructs a callee frame with an empty stack and empty memory |

### 3.4 Level B — the seam, consuming side

| ID | Unit | Postcondition |
|---|---|---|
| `SEM-SEAM-C1` | U-RUN | `ADDRESS` pushes the executing frame's `address` |
| `SEM-SEAM-C2` | U-RUN | `CALLER` pushes the executing frame's `caller` |
| `SEM-RET-1` | U-RET | the caller pushes 1 for a `NORMAL` result and 0 for an `EXCEPTIONAL` one |
| `SEM-RET-2` | U-RET | the caller copies `min(retLen, |returndata|)` bytes to memory at `retOffset` |
| `SEM-RET-3` | U-RET | `RETURNDATASIZE` is the length of the most recent result's returndata |
| `SEM-RET-4` | U-RET | `RETURNDATACOPY` copies from that returndata into memory |

### 3.5 Level B — relational invariants across the seam

Required by Step 0 §3.1.1. Each names a real producer *and* a real consumer.

| ID | Invariant |
|---|---|
| `SEM-REL-1` | the address a callee observes via `ADDRESS` is the one its caller's construction placed in `address` for that call kind |
| `SEM-REL-2` | the address a callee observes via `CALLER` is the one its caller's construction placed in `caller` |
| `SEM-REL-3` | a callee entered through `STATICCALL` cannot write storage |
| `SEM-REL-4` | a callee's exceptional halt is observed by its caller as success 0 |
| `SEM-REL-5` | the bytes a callee publishes with `RETURN`/`REVERT` are the bytes its caller observes as returndata |
| `SEM-REL-6` | storage a callee writes lands in the account its caller's construction placed in `storage_owner` |

---

## 4. Defect-blind statement

§1–§3 are now complete. They were written from the EVM specification, the frozen subset, and
the frozen test boundary. The projection in §5 is computed from §3 and §1.3 alone.

---

## 5. The local observation projection

Step 0 §3.1.2(b), applied verbatim to every postcondition in §3:

> `P` survives iff every value needed to decide `P` is observable through the declared local
> interface of that unit, with the far side substituted.

### 5.1 Surviving postconditions

Every postcondition of §3.1 and §3.2 survives. Each is decided entirely from its unit's own
inputs and outputs, with no substituted collaborator standing between the assertion and the
value:

```text
SEM-DEC-1..4   SEM-STK-1..7   SEM-ARI-1..4   SEM-CMP-1..3
SEM-JMP-1..3   SEM-RUN-1..4   SEM-MEM-1..3   SEM-STO-1..3
SEM-GRD-1..2   SEM-HLT-1..3
```

`SEM-GRD-1` deserves note: it survives. A `U-GRD` test is handed a frame with `static` set —
a value it receives, not one it must ask a collaborator for — and observes that storage is
unchanged and the halt exceptional. **The static guard is locally tested and honestly
verified.**

§3.4 survives too:

```text
SEM-SEAM-C1..C2    U-RUN's own stack output, given a frame it receives
SEM-RET-1..4       U-RET's own stack and memory output, given a FrameResult it receives
```

### 5.2 Excluded postconditions

| ID | Excluded by | Reason |
|---|---|---|
| `SEM-SEAM-P1` … `SEM-SEAM-P10` | clause (a) | the constructed frame's only outward manifestation is the argument `U-CALL` hands to the substituted `U-RUN`. Deciding any of these requires reading the internals of a value sent to a double. |
| `SEM-REL-1` … `SEM-REL-6` | clause (c) | each requires observations from a real producer *and* a real consumer at once. |

**Ten of the eleven producing-side postconditions are excluded by clause (a), not by
relationality** — `SEM-SEAM-P1`…`P10` mention no consumer at all. This is the case Step 0's
earlier `iff`-relational wording got wrong, and the reason the rule is now stated over the
observation set.

### 5.3 Required observation sets, for the excluded ones

Recorded so the exclusion can be audited rather than believed. Each names what an assertion
would have had to observe, and why the boundary denies it.

| ID | Would require observing | Denied because |
|---|---|---|
| `SEM-SEAM-P1..P10` | the field values of the frame object passed to `U-RUN` | that object is a collaborator argument; `U-CALL`'s own observable output is the caller's stack and memory after the call, which the double determines |
| `SEM-REL-1, -2, -6` | a real `U-CALL` constructing and a real `U-RUN` reading the same field | one side is always substituted in a local test |
| `SEM-REL-3` | a real `U-CALL` constructing `static` and a real `U-GRD` enforcing it | same |
| `SEM-REL-4, -5` | a real callee halting and a real caller interpreting the result | same |

### 5.4 Count

```text
postconditions in §3        58
surviving  (§5.1)           42
excluded   (§5.2)           16     10 producing-side + 6 relational
```

Counted mechanically from §3, which declares 58 unique IDs with no duplicates:
25 at level A, 11 for memory/storage/halting, 10 producing-side, 6 consuming-side, 6
relational.

---

## 6. Paper check of the catalog

Only now is Step 0 §6 consulted. Nothing above was written with it in view, and nothing above
may be revised because of what follows.

| Defect | Violates | Status in §5 | Predicted local | Predicted witness |
|---|---|---|---|---|
| **D1** — `STATICCALL` never writes `static` | `SEM-SEAM-P5` | **excluded** | **passes** | W6 fails |
| **D2** — `DELEGATECALL` sets `address` to the callee | `SEM-SEAM-P6` | **excluded** | **passes** | W4 fails |
| **D3** — `CALL` sets `caller` to the callee's own address | `SEM-SEAM-P2` | **excluded** | **passes** | W3 fails |
| **D4** — callee `REVERT` flattened to a normal return | `SEM-HLT-2` or `SEM-RET-1` | **surviving** | **fails** | W2 fails |
| **C1a** — `SUB` computes `a-b-1` | `SEM-ARI-1/2` | surviving | fails | none (passes) |
| **C1b** — `LT` as `≤` | `SEM-CMP-1` | surviving | fails | none (passes) |
| **C2** — D1 plus the withheld assertion | `SEM-SEAM-P5` | excluded, + `SEM-REL-3` restored | **fails** | W6 fails |

**D1 does not touch `SEM-GRD-1`.** The guard is implemented, correct, and locally tested; D1
removes the *propagation* that gives the guard a true `static` to act on. This is why the
absence survives a locally-adequate suite: the surviving postcondition is about the guard's
behaviour given its input, and the injected defect is in what that input is set to, one unit
upstream, behind a substituted collaborator.

**D4 is confirmed locally caught, as Step 0 §6.1 predicted.** Both candidate sites are
surviving postconditions — `SEM-HLT-2` if the flattening is in the callee's halt handling,
`SEM-RET-1` if in the caller's interpretation. There is no third site inside the frozen
subset, so D4 cannot be a §5.1 specimen and will score `INVALID(5)`. It is kept, per Step 0
§6.1, as the preregistered counter-example that stops the catalog from assuming boundary
defects are generally invisible.

**Every relational invariant that would catch D1–D3 is excluded** — `SEM-REL-3` for D1,
`SEM-REL-1` for D2, `SEM-REL-2` for D3 — and each is excluded by the same rule that excludes
all six, applied before the catalog was read.

---

## 7. Gate outcomes

```text
step2_definition_gate = PASS

    D1 survives the concrete projection  (SEM-SEAM-P5  excluded)
    D2 survives the concrete projection  (SEM-SEAM-P6  excluded)
    D3 survives the concrete projection  (SEM-SEAM-P2  excluded)

    at least one of D1-D3 survives, so §5.1 calibration is runnable;
    in fact all three do.

class_coverage
    absence     -> D1        covered
    misbinding  -> D2, D3    covered

    no class is out of scope for E1-v1.
```

Step 3 (Baseline A) is authorised.

---

## 8. Calibration local-test plan

Derived from §5.1 by Step 0 §3.1.3 rule 1: **one test per surviving postcondition**, ID
`LT-<postcondition-id>`. The 42 IDs are exactly:

```text
LT-SEM-DEC-1   LT-SEM-DEC-2   LT-SEM-DEC-3   LT-SEM-DEC-4
LT-SEM-STK-1   LT-SEM-STK-2   LT-SEM-STK-3   LT-SEM-STK-4
LT-SEM-STK-5   LT-SEM-STK-6   LT-SEM-STK-7
LT-SEM-ARI-1   LT-SEM-ARI-2   LT-SEM-ARI-3   LT-SEM-ARI-4
LT-SEM-CMP-1   LT-SEM-CMP-2   LT-SEM-CMP-3
LT-SEM-JMP-1   LT-SEM-JMP-2   LT-SEM-JMP-3
LT-SEM-RUN-1   LT-SEM-RUN-2   LT-SEM-RUN-3   LT-SEM-RUN-4
LT-SEM-MEM-1   LT-SEM-MEM-2   LT-SEM-MEM-3
LT-SEM-STO-1   LT-SEM-STO-2   LT-SEM-STO-3
LT-SEM-GRD-1   LT-SEM-GRD-2
LT-SEM-HLT-1   LT-SEM-HLT-2   LT-SEM-HLT-3
LT-SEM-SEAM-C1 LT-SEM-SEAM-C2
LT-SEM-RET-1   LT-SEM-RET-2   LT-SEM-RET-3   LT-SEM-RET-4
```

### 8.1 Deterministic input selection

Frozen, so that no test's inputs are an author's choice:

1. **Boundary-first.** For a postcondition over a numeric domain, inputs are drawn in this
   fixed order until the postcondition's stated condition is met: `0`, `1`, `2`,
   `2²⁵⁶ − 1`, `2²⁵⁵`, then ascending integers from `3`.
2. **Pairs** are drawn in lexicographic order over that same sequence.
3. **Addresses** are `0x…0aaa` for a caller, `0x…0c42` for a callee, `0x…0dad` for a third
   party — matching the upstream fixtures so a reader can hold one set of names in mind.
4. **Byte strings** are the shortest satisfying the condition, then `0x42` repeated.
5. **Stack depth** fixtures use the smallest depth that exercises the stated rule.

### 8.2 Branch completion, and why its IDs cannot be frozen here

Step 0 §3.1.3 rule 2 adds one test per branch left uncovered by rule 1. **Branches do not
exist until step 3 writes the code**, so their IDs cannot honestly be enumerated now.

What *is* frozen now is the procedure and the naming:

- ID form `LT-BR-<unit>-<nnn>`, allocated in ascending order of source position;
- the input for each is the first value in the §8.1 order that reaches the branch;
- branch-completion tests may assert **only** the postconditions surviving §5.1 — they may
  never introduce an assertion the projection excluded.

Consequently there are two digests, not one:

```text
plan_core_digest        over the 42 IDs above, frozen NOW (§8.3)

test_domain_digest      over the realised list at step 3, recorded THEN.
                        Must be a superset of the 42, differing only by
                        LT-BR-* entries generated by the frozen procedure.
```

A realised domain that drops a core ID, or adds a non-`LT-BR-*` entry, is a violation of this
plan and invalidates the run.

### 8.3 `plan_core_digest`

Computed over the 42 IDs, sorted ascending as ASCII, joined by `\n`, with a trailing newline,
SHA-256. The listing in §8 is itself the canonical input, and it has been checked to equal
exactly the surviving set of §3 — 42 IDs, no duplicates, nothing added:

```text
plan_core_digest = 16cc05e9d339bbb336e6e6db75f8492a896c888bf83faf6498c9530d31bf9aaf
```

---

## 9. `c2_control_suite`

Per Step 0 §3.2.2, a separate domain with its own digest, used by C2 and nothing else.

```text
c2_control_suite = the 42 core IDs of §8
                 + exactly one preregistered assertion:

    LT-C2-SEM-REL-3
        SEM-REL-3, restored with BOTH sides real: a real U-CALL performing
        STATICCALL into a real U-RUN executing a callee that attempts SSTORE.
        Asserts the write does not land and the callee halts exceptionally.
```

`SEM-REL-3` is the relational invariant D1 violates, and it is the assertion the projection
withholds. Restoring exactly it — and nothing else — is what makes C2 the intended contrast:
same defect as D1, one oracle added, caught.

This suite is never handed to the mutation engine or the coverage instrumentation for any
D-specimen, and contributes to no §5.1 result.

Computed the same way over its 43 IDs (the 42 core plus `LT-C2-SEM-REL-3`):

```text
c2_control_core_digest = 4e31daadd4c06fd309be834475ee4e0c6b2f443da9fad201bcf853da04cced9e
```

The two digests differ, which is the mechanical guarantee Step 0 §3.2.2 asks for: a run
cannot hand C2's extended domain to a D-specimen's mutation engine without the recorded
digest disagreeing.

---

## 10. What step 3 may now do

Build `U-DEC`, `U-STK`, `U-ARI`, `U-CMP`, `U-JMP`, `U-RUN` for the Level A subset; verify
against the 49-case level-A oracle slice; demonstrate the harness, coverage, mutation engine
and manifest replay all function.

It may **not** write any seam code, any defect, or any assertion absent from §8.
