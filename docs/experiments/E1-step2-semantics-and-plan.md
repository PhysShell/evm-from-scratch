# E1 Step 2 — normative semantics, observation projection, and local-test plan

**Status:** frozen on merge, under the rules of
[E1 Step 0](./E1-step0-preregistration.md). This document executes Step 0 §9 step 2 and
authorises the next step only if §7 records `step2_definition_gate = PASS`.

**Contains no implementation.** No interpreter, no test code, no measurement.

**On the order of authorship.** §1–§4 were written from the EVM specification, the frozen
subset and the frozen test boundary; §5 computes the projection from them; §6 reads the
catalog afterwards and reports what falls out. That order is a *provenance* record and
nothing more — its author has read Step 0 §6 and cannot unread it, so it is not blinding and
is not offered as such. What actually carries the weight is elsewhere: the projection is an
explicit algorithm (§5), the decomposition that decides the outcome is declared as a scope
condition (§1.2), and everything is frozen before any measurement. Those three do the work;
the writing order merely records how the document came to be.

---

## 1. Component decomposition — and the choice that decides the experiment

### 1.1 The units

| Unit | Responsibility |
|---|---|
| `U-ENTRY` | construction of the root frame from a fixture and its transaction context |
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

Per Step 0 §3.1.2(a). Two kinds of thing must not be confused, and an earlier draft confused
them:

- a **substituted collaborator** is a double the unit *calls*. Its behaviour and the
  internals of what is passed to it are outside the local observation set.
- **owned state** is a mutable structure the unit is *handed* and mutates in place. Its
  after-state is the unit's own observable output.

`World` is **owned state, not a collaborator.** `U-STO` and `U-GRD` receive it as an explicit
state input and their effect on it is directly observable — that is what makes their
postconditions locally decidable at all. The earlier table listed `World` as "substituted",
which contradicted §5 declaring every `SEM-STO-*` and `SEM-GRD-*` surviving. Both could not
be true; this is the resolution, and it is the model that makes the guard honestly testable.

| Unit | Inputs | Owned state | Substituted collaborator | Own observable output |
|---|---|---|---|---|
| `U-ENTRY` | fixture code, tx context | — | — | the root `Frame` it returns |
| `U-DEC` | code bytes, pc | — | — | decoded instruction, next pc |
| `U-STK` | a stack, a value | the stack | — | resulting stack, or exceptional halt |
| `U-ARI`, `U-CMP` | operand pair | — | — | result value |
| `U-JMP` | code bytes, target | — | — | validity verdict, jumpdest set |
| `U-MEM` | offset, value | memory | — | memory contents, size |
| `U-STO` | frame, slot, value | **`World`** | — | storage of `storage_owner`, after |
| `U-GRD` | frame, slot, value | **`World`** | — | whether the write landed; halt status |
| `U-HLT` | frame, offset, len | — | — | `FrameResult` |
| `U-CALL` | frame, stack operands | caller's stack, memory | **`U-RUN`** | caller's stack and memory after the call |
| `U-RET` | frame, a `FrameResult` | caller's stack, memory | — | caller's stack and memory |
| `U-RUN` | a frame | — | **`U-CALL`** | `FrameResult` |

`U-CALL`'s substitution of `U-RUN` is the mock-heavy shape Step 0 §3 requires, and it is the
*only* substitution in the seam's neighbourhood. The frame `U-CALL` builds is passed to that
double and is therefore, by §3.1.2(a), outside what a local test may assert on.

**`U-ENTRY` and `U-CALL` both build a `Frame`, and only one of them is locally assertable.**
`U-ENTRY` *returns* its frame, so every field is its own observable output; `U-CALL` *passes*
its frame to a substituted collaborator, so none of them is. The two rows are not
inconsistent — the difference is entirely positional, and it is the clearest available
illustration of §1.2: the same kind of object is observable or hidden according to where it
sits relative to the substitution, not according to what it contains.

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

TxContext {
  to      address | ABSENT
  from    address | ABSENT
}

CallOperands_CALL          { gas, address, value, argsOffset, argsSize, retOffset, retSize }
CallOperands_STATICCALL    { gas, address,        argsOffset, argsSize, retOffset, retSize }
CallOperands_DELEGATECALL  { gas, address,        argsOffset, argsSize, retOffset, retSize }
```

`REVERT` is `EXCEPTIONAL` *with* returndata; every other exceptional halt carries none.

**Field order is normative.** The order in which fields are written above is the order §8.2.1
enumerates them in. `TxContext` and the three operand tuples are declared here for exactly
that reason: §8.2.1 orders composite records "by the field order §2 declares", and an earlier
draft named records §2 did not define. The operand tuples' field order is also their pop
order (`SEM-CALL-1..3`), so the two never diverge.

---

## 3. Normative semantics

Complete for the frozen subset of Step 0 §1.1–§1.2. All arithmetic is modulo 2²⁵⁶; all
comparisons are unsigned.

### 3.0 Case sets

A postcondition's *case set* is the product of two frozen rules. A postcondition matching
neither has a single case.

```text
(i)  OPCODE ALTERNATIVES
     the postcondition explicitly names a set of opcodes or an indexed
     family  ->  one case per named member

(ii) SEMANTIC PARTITION
     the postcondition's truth is given piecewise over a finite set of
     explicitly named conditions  ->  one case per piece

     case set = (i) x (ii) when both apply
```

Rule (i) alone was not enough, and the gap it left was serious. `SEM-RET-1` — *the caller
pushes 1 for a `NORMAL` result and 0 for an `EXCEPTIONAL` one* — names no opcodes, so it had
exactly one case. A plan that discharged it with a `NORMAL` result would stay green under D4
sited on the caller side, and **the preregistered prediction "D4 fails locally" would not have
followed from the plan at all.** It now yields `SEM-RET-1/NORMAL` and
`SEM-RET-1/EXCEPTIONAL`, and D4 is forced red by construction rather than by hope.

Branch completion does not rescue this. A defect that *removes* the discriminating branch
leaves no branch for `LT-BR-*` to cover — which is exactly what absence defects do. Coverage
of the implementation's branches is not a substitute for coverage of the specification's
partition, and this rule is what keeps the second from silently depending on the first.

Both rules key on the postcondition's own text — which opcodes it names, which conditions it
distinguishes — and neither consults the defect catalog. `SEM-DEC-1` still has one case
despite ranging over every non-`PUSH` opcode: it states one uniform rule, names no opcodes,
and distinguishes no conditions.

### 3.1 Level A

| ID | Unit | Cases | Postcondition |
|---|---|---|---|
| `SEM-DEC-1` | U-DEC | 1 | a non-`PUSH` opcode at `pc` decodes with no immediate; next pc is `pc+1` |
| `SEM-DEC-2` | U-DEC | `PUSH1`…`PUSH32` | `PUSHn` takes the `n` bytes after the opcode as a big-endian immediate; next pc is `pc+1+n` |
| `SEM-DEC-3` | U-DEC | `PUSH1`…`PUSH32` | `PUSHn` with fewer than `n` bytes remaining is zero-padded on the right |
| `SEM-DEC-4` | U-DEC | 1 | `PUSH0` takes no immediate and yields the value 0 |
| `SEM-STK-1` | U-STK | 1 | push increases depth by 1; the pushed value is the new top |
| `SEM-STK-2` | U-STK | 1 | pop decreases depth by 1 and yields the previous top |
| `SEM-STK-3` | U-STK | 1 | pop on an empty stack halts exceptionally |
| `SEM-STK-4` | U-STK | `DUP1`…`DUP16` | `DUPn` copies the n-th item from the top to the top; depth increases by 1 |
| `SEM-STK-5` | U-STK | `SWAP1`…`SWAP16` | `SWAPn` exchanges the top with the (n+1)-th item; depth is unchanged |
| `SEM-STK-6` | U-STK | `DUP1`…`DUP16`, `SWAP1`…`SWAP16` | insufficient depth halts exceptionally |
| `SEM-STK-7` | U-STK | 1 | a push beyond depth 1024 halts exceptionally |
| `SEM-ARI-1` | U-ARI | `ADD` `SUB` `MUL` `DIV` `MOD` | operands are popped as `a` then `b`; the result is `a OP b` |
| `SEM-ARI-2` | U-ARI | {`ADD` `SUB` `MUL`} × {`WRAP`, `NO_WRAP`} | the result wraps modulo 2²⁵⁶ |
| `SEM-ARI-3` | U-ARI | `ZERO_DIVISOR`, `NONZERO_DIVISOR` | `DIV` with `b = 0` yields 0; otherwise floor division |
| `SEM-ARI-4` | U-ARI | `ZERO_DIVISOR`, `NONZERO_DIVISOR` | `MOD` with `b = 0` yields 0; otherwise `a mod b` |
| `SEM-CMP-1` | U-CMP | {`LT` `GT`} × {`TRUE`, `FALSE`} | compares unsigned and yields 1 or 0 |
| `SEM-CMP-2` | U-CMP | `EQUAL`, `UNEQUAL` | `EQ` yields 1 iff the operands are equal |
| `SEM-CMP-3` | U-CMP | `ZERO`, `NONZERO` | `ISZERO` yields 1 iff the operand is 0 |
| `SEM-JMP-1` | U-JMP | `AT_TOP_LEVEL`, `INSIDE_PUSH_IMMEDIATE` | the jumpdest set is every offset holding `0x5B` not inside a `PUSH` immediate |
| `SEM-JMP-2` | U-JMP | `VALID_TARGET`, `INVALID_TARGET` | `JUMP` transfers control to an offset in the jumpdest set, and halts exceptionally for one outside it |
| `SEM-JMP-3` | U-JMP | `TAKEN`, `NOT_TAKEN` | `JUMPI` transfers control iff its condition operand is non-zero |
| `SEM-RUN-1` | U-RUN | 1 | `PC` pushes the offset of the `PC` opcode itself |
| `SEM-RUN-2` | U-RUN | 1 | `STOP` halts normally with empty returndata |
| `SEM-RUN-3` | U-RUN | 1 | execution running past the end of code halts normally |
| `SEM-RUN-4` | U-RUN | 1 | `GAS` pushes MAX_UINT256 (Step 0 §1.2) |

### 3.2 Level B — memory, storage, halting

| ID | Unit | Cases | Postcondition |
|---|---|---|---|
| `SEM-MEM-1` | U-MEM | 1 | `MSTORE` writes 32 big-endian bytes at the given offset |
| `SEM-MEM-2` | U-MEM | `WRITTEN`, `UNWRITTEN` | `MLOAD` reads 32 bytes at the offset; never-written bytes read as 0 |
| `SEM-MEM-3` | U-MEM | 1 | `MSIZE` is the highest touched offset rounded up to a multiple of 32 |
| `SEM-STO-1` | U-STO | 1 | `SSTORE` writes to the storage of the frame's `storage_owner` |
| `SEM-STO-2` | U-STO | 1 | `SLOAD` reads from the storage of the frame's `storage_owner` |
| `SEM-STO-3` | U-STO | 1 | a never-written slot reads as 0 |
| `SEM-STO-4` | U-RUN | 1 | an exceptional halt does **not** undo storage writes already performed in that frame — the model has no journalling (see below) |
| `SEM-GRD-1` | U-GRD | 1 | when the frame's `static` is set, `SSTORE` performs no write and halts exceptionally |
| `SEM-GRD-2` | U-GRD | 1 | when the frame's `static` is clear, `SSTORE` proceeds |
| `SEM-HLT-1` | U-HLT | 1 | `RETURN` yields `NORMAL` with returndata `memory[offset .. offset+len)` |
| `SEM-HLT-2` | U-HLT | 1 | `REVERT` yields `EXCEPTIONAL` with returndata `memory[offset .. offset+len)` |
| `SEM-HLT-3` | U-HLT | 1 | any other exceptional halt yields empty returndata |

**Storage rollback is amputated, deliberately and explicitly.** A real EVM reverts state on
an exceptional halt; `SEM-STO-4` says this model does not. `SSTORE` and `REVERT` are both in
the frozen subset, so leaving the interaction unstated would have left two defensible
implementations and no way to call either the correct baseline.

Amputation rather than journalling, for three reasons: it matches the subset's existing
amputations (gas, value transfer, calldata); journalling would add snapshot machinery in the
seam's immediate neighbourhood, enlarging the very region whose blind spots are under study;
and it costs no oracle correctness — checked against the corpus, **no in-subset case has a
callee that both `SSTORE`s and `REVERT`s, and none has outer code that does**, so no oracle
expectation depends on rollback either way. A defect requiring rollback semantics is out of
scope for E1-v1.

### 3.3 Level B — the CALL-family operand contract

The seam lives inside `U-CALL`, so its operand contract must be specified rather than
assumed. Operand order matches the upstream fixtures (#140, #146, #147), popped top-first.

| ID | Cases | Postcondition |
|---|---|---|
| `SEM-CALL-1` | 1 | `CALL` pops seven operands, in order: `gas`, `address`, `value`, `argsOffset`, `argsSize`, `retOffset`, `retSize` |
| `SEM-CALL-2` | 1 | `STATICCALL` pops six: `gas`, `address`, `argsOffset`, `argsSize`, `retOffset`, `retSize` |
| `SEM-CALL-3` | 1 | `DELEGATECALL` pops six: `gas`, `address`, `argsOffset`, `argsSize`, `retOffset`, `retSize` |
| `SEM-CALL-4` | all three kinds | the `address` operand designates the called account |
| `SEM-CALL-5` | all three kinds | the `gas` operand is consumed and otherwise ignored — there is no gas accounting (Step 0 §1.3) |
| `SEM-CALL-6` | 1 | `CALL`'s `value` operand is consumed and no value is transferred; the model has no balances |
| `SEM-CALL-7` | all three kinds | `argsOffset`/`argsSize` are consumed and otherwise ignored — the model has no calldata, so a callee cannot observe call input |
| `SEM-CALL-8` | all three kinds | `retOffset`/`retSize` are the destination and bound of the returndata copy performed by `U-RET` |

`SEM-CALL-7` records a real amputation rather than an oversight: `CALLDATALOAD`/`SIZE`/`COPY`
are outside the frozen subset, so **the input half of the seam is not modelled at all.** Only
the context half — identity, authority, storage ownership — and the return half are. A
defect in argument passing is therefore out of scope for E1-v1, and no E1 result speaks to it.

### 3.4 Level B — the seam, producing side (inside `U-CALL`)

Every call kind × every boundary-carried identity field, so that no cell is left implicit.

| ID | Kind | Field | Value |
|---|---|---|---|
| `SEM-SEAM-P1` | `CALL` | `address` | the called address |
| `SEM-SEAM-P2` | `CALL` | `caller` | the current frame's `address` |
| `SEM-SEAM-P3` | `CALL` | `static` | the current frame's `static`, inherited |
| `SEM-SEAM-P4` | `CALL` | `storage_owner` | the called address |
| `SEM-SEAM-P5` | `STATICCALL` | `address` | the called address |
| `SEM-SEAM-P6` | `STATICCALL` | `caller` | the current frame's `address` |
| `SEM-SEAM-P7` | `STATICCALL` | `static` | **`true`**, whatever the current frame's is |
| `SEM-SEAM-P8` | `STATICCALL` | `storage_owner` | the called address |
| `SEM-SEAM-P9` | `DELEGATECALL` | `address` | the **current** frame's `address` |
| `SEM-SEAM-P10` | `DELEGATECALL` | `caller` | the **current** frame's `caller`, inherited — not the current address |
| `SEM-SEAM-P11` | `DELEGATECALL` | `static` | the current frame's `static`, inherited |
| `SEM-SEAM-P12` | `DELEGATECALL` | `storage_owner` | the **current** frame's `storage_owner` |
| `SEM-SEAM-P13` | all | `code` | the code at the called address |
| `SEM-SEAM-P14` | all | `pc` | 0 |
| `SEM-SEAM-P15` | all | `stack`, `memory`, `returndata` | all empty |

### 3.5 Level B — the seam, consuming side

| ID | Unit | Cases | Postcondition |
|---|---|---|---|
| `SEM-SEAM-C1` | U-RUN | 1 | `ADDRESS` pushes the executing frame's `address` |
| `SEM-SEAM-C2` | U-RUN | 1 | `CALLER` pushes the executing frame's `caller` |
| `SEM-RET-1` | U-RET | `NORMAL`, `EXCEPTIONAL` | the caller pushes 1 for a `NORMAL` result and 0 for an `EXCEPTIONAL` one |
| `SEM-RET-2` | U-RET | `FULL`, `TRUNCATED` | the caller copies `min(retSize, |returndata|)` bytes to memory at `retOffset` |
| `SEM-RET-3` | U-RET | 1 | `RETURNDATASIZE` is the length of the most recent result's returndata |
| `SEM-RET-4` | U-RET | 1 | `RETURNDATACOPY` copies from that returndata into memory |

### 3.6 Entry — the root frame contract

The producing semantics specifies every *inner* frame, but the first frame has to come from
somewhere, and W3/W4 depend on where. Upstream `#141` sets `tx.to = 0x…0aaa` and expects the
callee's `CALLER` to be that address; `#99` sets `tx.from` and expects `CALLER` to return it;
`#146` reads storage through a `DELEGATECALL` against the outer frame's context. Leaving the
entry frame to "whatever the harness does" would have made D2 and D3 depend on unspecified
state.

| ID | Unit | Cases | Postcondition |
|---|---|---|---|
| `SEM-ROOT-1` | U-ENTRY | 1 | `code` is the fixture's own code |
| `SEM-ROOT-2` | U-ENTRY | `PRESENT`, `ABSENT` | `address` is `tx.to`, or the zero address when `tx.to` is absent |
| `SEM-ROOT-3` | U-ENTRY | `PRESENT`, `ABSENT` | `caller` is `tx.from`, or the zero address when `tx.from` is absent |
| `SEM-ROOT-4` | U-ENTRY | 1 | `storage_owner` equals `address` |
| `SEM-ROOT-5` | U-ENTRY | 1 | `static` is false |
| `SEM-ROOT-6` | U-ENTRY | 1 | `pc` is 0 |
| `SEM-ROOT-7` | U-ENTRY | 1 | `stack`, `memory` and `returndata` are all empty |

`tx.value`, `tx.data`, `tx.origin` and `tx.gasprice` appear in the corpus but are outside the
frozen subset (Step 0 §1.3); `U-ENTRY` ignores them.

### 3.7 Level B — relational invariants across the seam

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

## 4. Completeness statement

§3 declares **79** postconditions: 25 at level A, 12 for memory/storage/halting (including the
rollback amputation), 7 for the entry frame, 8 for the CALL-family operand contract, 15
producing-side, 6 consuming-side, 6 relational. The
producing side is now a full kind × field matrix, so no call kind has an unspecified identity
field — the gap an earlier draft had, where `STATICCALL` specified only `static` and
`DELEGATECALL` omitted it.

---

## 5. The local observation projection

Step 0 §3.1.2(b), applied verbatim to every postcondition in §3:

> `P` survives iff every value needed to decide `P` is observable through the declared local
> interface of that unit, with the far side substituted.

### 5.1 Surviving — 58 postconditions

Every postcondition of §3.1, §3.2, §3.3, §3.5 and §3.6 survives. Each is decided from its unit's
own inputs, its owned state, and its own outputs, with no substituted collaborator standing
between the assertion and the value.

`SEM-STO-*` and `SEM-GRD-*` survive because `World` is owned state, not a collaborator
(§1.3). A `U-GRD` test is handed a frame with `static` set and a `World` it can inspect
afterwards, and observes that the slot is unchanged and the halt exceptional. **The static
guard is locally tested and honestly verified.**

`SEM-CALL-1..8` survive: operand arity, pop order and consumption are decidable from
`U-CALL`'s own stack before and after, with no reference to the double's behaviour.

`SEM-ROOT-1..7` survive because `U-ENTRY` *returns* the frame it builds (§1.3). This is the
positional asymmetry, not an inconsistency: the identical field `static` is assertable on
`U-ENTRY`'s output and unassertable on `U-CALL`'s collaborator argument.

### 5.2 Excluded — 21 postconditions

| IDs | Excluded by | Reason |
|---|---|---|
| `SEM-SEAM-P1` … `SEM-SEAM-P15` | clause (a) | the constructed frame's only outward manifestation is the argument `U-CALL` hands to the substituted `U-RUN`. Deciding any of these requires reading the internals of a value sent to a double. |
| `SEM-REL-1` … `SEM-REL-6` | clause (c) | each requires observations from a real producer *and* a real consumer at once. |

**All fifteen producing-side postconditions are excluded by clause (a), not by
relationality** — `SEM-SEAM-P1`…`P15` mention no consumer at all. This is the case Step 0's
earlier `iff`-relational wording got wrong, and the reason the rule is stated over the
observation set.

### 5.3 Required observation sets, for the excluded ones

| IDs | Would require observing | Denied because |
|---|---|---|
| `SEM-SEAM-P1..P15` | the field values of the frame object passed to `U-RUN` | that object is a collaborator argument; `U-CALL`'s own observable output is the caller's stack and memory after the call, which the double determines |
| `SEM-REL-1, -2, -6` | a real `U-CALL` constructing and a real `U-RUN` reading the same field | one side is always substituted in a local test |
| `SEM-REL-3` | a real `U-CALL` constructing `static` and a real `U-GRD` enforcing it | same |
| `SEM-REL-4, -5` | a real callee halting and a real caller interpreting the result | same |

### 5.4 Count

```text
postconditions in §3        79
surviving  (§5.1)           58
excluded   (§5.2)           21     15 producing-side + 6 relational
```

---

## 6. Paper check of the catalog

Only now is Step 0 §6 consulted, and nothing above is revised because of it.

| Defect | Violates | Status in §5 | Predicted local | Predicted witness |
|---|---|---|---|---|
| **D1** — `STATICCALL` never writes `static` | `SEM-SEAM-P7` | **excluded** | **passes** | W6 fails |
| **D2** — `DELEGATECALL` sets `address` to the callee | `SEM-SEAM-P9` | **excluded** | **passes** | W4 fails |
| **D3** — `CALL` sets `caller` to the callee's own address | `SEM-SEAM-P2` | **excluded** | **passes** | W3 fails |
| **D4** — callee `REVERT` flattened to a normal return | `SEM-HLT-2` or `SEM-RET-1` | **surviving** | **fails** | W2 fails |
| **C1a** — `SUB` computes `a-b-1` | `SEM-ARI-1/SUB`, `SEM-ARI-2/SUB` | surviving | **fails** | none (passes) |
| **C1b** — `LT` as `≤` | `SEM-CMP-1/LT` | surviving | **fails** | none (passes) |
| **C2** — D1 plus one local spy assertion | `SEM-SEAM-P7` | excluded, restored locally in §9 | **fails** | W6 fails |

**The controls are now forced red by construction.** Under the §3.0 case rule, `SUB` and `LT`
each own a named case ID, so C1a cannot be missed by a plan that tested only `ADD`, and C1b
cannot be missed by one that tested only `GT`. Before the case rule, a single
`LT-SEM-CMP-1` could have discharged its postcondition with `GT` alone and left C1b green —
a control that fails to control.

**D1 does not touch `SEM-GRD-1`.** The guard is implemented, correct, and locally tested; D1
removes the *propagation* that gives the guard a true `static` to act on. The surviving
postcondition is about the guard's behaviour given its input; the defect is in what that
input is set to, one unit upstream, behind a substituted collaborator.

**D4 is confirmed locally caught**, as Step 0 §6.1 predicted — and now *forced* rather than
merely expected. Both candidate sites are surviving postconditions, and under §3.0 rule (ii)
each carries the discriminating case: `LT-SEM-HLT-2` for the callee-side siting, and
`LT-SEM-RET-1/EXCEPTIONAL` for the caller-side one. Before the semantic-partition rule,
`LT-SEM-RET-1` could have been discharged with a `NORMAL` result and left D4 green, so the
prediction did not follow from the plan. It does now. The frozen subset offers no third
site, so D4 scores `INVALID(5)`.

---

## 7. Gate outcomes

```text
step2_definition_gate = PASS

    D1  violates SEM-SEAM-P7   excluded  -> survives the projection
    D2  violates SEM-SEAM-P9   excluded  -> survives the projection
    D3  violates SEM-SEAM-P2   excluded  -> survives the projection

    at least one of D1-D3 survives; in fact all three do.

class_coverage
    absence     -> D1        covered
    misbinding  -> D2, D3    covered
    no class is out of scope for E1-v1.
```

The finding is stronger than the previous draft's, because the specification it rests on is
no longer thin where it matters: the producing side is a complete kind × field matrix, the
operand contract is specified, `World` observability is resolved in favour of the guard being
locally testable, and the controls are forced red by case enumeration. The blind spot
survives after the obvious ways of manufacturing one by under-specification have been closed.

---

## 8. Calibration local-test plan

Step 0 §3.1.3 rule 1, at case granularity: **one test per (surviving postcondition × case)**.
IDs are `LT-<postcondition-id>` for a single-case postcondition and
`LT-<postcondition-id>/<CASE>` otherwise. 58 postconditions yield **213** case IDs:

```text
LT-SEM-ARI-1/ADD                    LT-SEM-ARI-1/DIV                    LT-SEM-ARI-1/MOD
LT-SEM-ARI-1/MUL                    LT-SEM-ARI-1/SUB                    LT-SEM-ARI-2/ADD_NO_WRAP
LT-SEM-ARI-2/ADD_WRAP               LT-SEM-ARI-2/MUL_NO_WRAP            LT-SEM-ARI-2/MUL_WRAP
LT-SEM-ARI-2/SUB_NO_WRAP            LT-SEM-ARI-2/SUB_WRAP               LT-SEM-ARI-3/NONZERO_DIVISOR
LT-SEM-ARI-3/ZERO_DIVISOR           LT-SEM-ARI-4/NONZERO_DIVISOR        LT-SEM-ARI-4/ZERO_DIVISOR
LT-SEM-CALL-1                       LT-SEM-CALL-2                       LT-SEM-CALL-3
LT-SEM-CALL-4/CALL                  LT-SEM-CALL-4/DELEGATECALL          LT-SEM-CALL-4/STATICCALL
LT-SEM-CALL-5/CALL                  LT-SEM-CALL-5/DELEGATECALL          LT-SEM-CALL-5/STATICCALL
LT-SEM-CALL-6                       LT-SEM-CALL-7/CALL                  LT-SEM-CALL-7/DELEGATECALL
LT-SEM-CALL-7/STATICCALL            LT-SEM-CALL-8/CALL                  LT-SEM-CALL-8/DELEGATECALL
LT-SEM-CALL-8/STATICCALL            LT-SEM-CMP-1/GT_FALSE               LT-SEM-CMP-1/GT_TRUE
LT-SEM-CMP-1/LT_FALSE               LT-SEM-CMP-1/LT_TRUE                LT-SEM-CMP-2/EQUAL
LT-SEM-CMP-2/UNEQUAL                LT-SEM-CMP-3/NONZERO                LT-SEM-CMP-3/ZERO
LT-SEM-DEC-1                        LT-SEM-DEC-2/PUSH1                  LT-SEM-DEC-2/PUSH10
LT-SEM-DEC-2/PUSH11                 LT-SEM-DEC-2/PUSH12                 LT-SEM-DEC-2/PUSH13
LT-SEM-DEC-2/PUSH14                 LT-SEM-DEC-2/PUSH15                 LT-SEM-DEC-2/PUSH16
LT-SEM-DEC-2/PUSH17                 LT-SEM-DEC-2/PUSH18                 LT-SEM-DEC-2/PUSH19
LT-SEM-DEC-2/PUSH2                  LT-SEM-DEC-2/PUSH20                 LT-SEM-DEC-2/PUSH21
LT-SEM-DEC-2/PUSH22                 LT-SEM-DEC-2/PUSH23                 LT-SEM-DEC-2/PUSH24
LT-SEM-DEC-2/PUSH25                 LT-SEM-DEC-2/PUSH26                 LT-SEM-DEC-2/PUSH27
LT-SEM-DEC-2/PUSH28                 LT-SEM-DEC-2/PUSH29                 LT-SEM-DEC-2/PUSH3
LT-SEM-DEC-2/PUSH30                 LT-SEM-DEC-2/PUSH31                 LT-SEM-DEC-2/PUSH32
LT-SEM-DEC-2/PUSH4                  LT-SEM-DEC-2/PUSH5                  LT-SEM-DEC-2/PUSH6
LT-SEM-DEC-2/PUSH7                  LT-SEM-DEC-2/PUSH8                  LT-SEM-DEC-2/PUSH9
LT-SEM-DEC-3/PUSH1                  LT-SEM-DEC-3/PUSH10                 LT-SEM-DEC-3/PUSH11
LT-SEM-DEC-3/PUSH12                 LT-SEM-DEC-3/PUSH13                 LT-SEM-DEC-3/PUSH14
LT-SEM-DEC-3/PUSH15                 LT-SEM-DEC-3/PUSH16                 LT-SEM-DEC-3/PUSH17
LT-SEM-DEC-3/PUSH18                 LT-SEM-DEC-3/PUSH19                 LT-SEM-DEC-3/PUSH2
LT-SEM-DEC-3/PUSH20                 LT-SEM-DEC-3/PUSH21                 LT-SEM-DEC-3/PUSH22
LT-SEM-DEC-3/PUSH23                 LT-SEM-DEC-3/PUSH24                 LT-SEM-DEC-3/PUSH25
LT-SEM-DEC-3/PUSH26                 LT-SEM-DEC-3/PUSH27                 LT-SEM-DEC-3/PUSH28
LT-SEM-DEC-3/PUSH29                 LT-SEM-DEC-3/PUSH3                  LT-SEM-DEC-3/PUSH30
LT-SEM-DEC-3/PUSH31                 LT-SEM-DEC-3/PUSH32                 LT-SEM-DEC-3/PUSH4
LT-SEM-DEC-3/PUSH5                  LT-SEM-DEC-3/PUSH6                  LT-SEM-DEC-3/PUSH7
LT-SEM-DEC-3/PUSH8                  LT-SEM-DEC-3/PUSH9                  LT-SEM-DEC-4
LT-SEM-GRD-1                        LT-SEM-GRD-2                        LT-SEM-HLT-1
LT-SEM-HLT-2                        LT-SEM-HLT-3                        LT-SEM-JMP-1/AT_TOP_LEVEL
LT-SEM-JMP-1/INSIDE_PUSH_IMMEDIATE  LT-SEM-JMP-2/INVALID_TARGET         LT-SEM-JMP-2/VALID_TARGET
LT-SEM-JMP-3/NOT_TAKEN              LT-SEM-JMP-3/TAKEN                  LT-SEM-MEM-1
LT-SEM-MEM-2/UNWRITTEN              LT-SEM-MEM-2/WRITTEN                LT-SEM-MEM-3
LT-SEM-RET-1/EXCEPTIONAL            LT-SEM-RET-1/NORMAL                 LT-SEM-RET-2/FULL
LT-SEM-RET-2/TRUNCATED              LT-SEM-RET-3                        LT-SEM-RET-4
LT-SEM-ROOT-1                       LT-SEM-ROOT-2/ABSENT                LT-SEM-ROOT-2/PRESENT
LT-SEM-ROOT-3/ABSENT                LT-SEM-ROOT-3/PRESENT               LT-SEM-ROOT-4
LT-SEM-ROOT-5                       LT-SEM-ROOT-6                       LT-SEM-ROOT-7
LT-SEM-RUN-1                        LT-SEM-RUN-2                        LT-SEM-RUN-3
LT-SEM-RUN-4                        LT-SEM-SEAM-C1                      LT-SEM-SEAM-C2
LT-SEM-STK-1                        LT-SEM-STK-2                        LT-SEM-STK-3
LT-SEM-STK-4/DUP1                   LT-SEM-STK-4/DUP10                  LT-SEM-STK-4/DUP11
LT-SEM-STK-4/DUP12                  LT-SEM-STK-4/DUP13                  LT-SEM-STK-4/DUP14
LT-SEM-STK-4/DUP15                  LT-SEM-STK-4/DUP16                  LT-SEM-STK-4/DUP2
LT-SEM-STK-4/DUP3                   LT-SEM-STK-4/DUP4                   LT-SEM-STK-4/DUP5
LT-SEM-STK-4/DUP6                   LT-SEM-STK-4/DUP7                   LT-SEM-STK-4/DUP8
LT-SEM-STK-4/DUP9                   LT-SEM-STK-5/SWAP1                  LT-SEM-STK-5/SWAP10
LT-SEM-STK-5/SWAP11                 LT-SEM-STK-5/SWAP12                 LT-SEM-STK-5/SWAP13
LT-SEM-STK-5/SWAP14                 LT-SEM-STK-5/SWAP15                 LT-SEM-STK-5/SWAP16
LT-SEM-STK-5/SWAP2                  LT-SEM-STK-5/SWAP3                  LT-SEM-STK-5/SWAP4
LT-SEM-STK-5/SWAP5                  LT-SEM-STK-5/SWAP6                  LT-SEM-STK-5/SWAP7
LT-SEM-STK-5/SWAP8                  LT-SEM-STK-5/SWAP9                  LT-SEM-STK-6/DUP1
LT-SEM-STK-6/DUP10                  LT-SEM-STK-6/DUP11                  LT-SEM-STK-6/DUP12
LT-SEM-STK-6/DUP13                  LT-SEM-STK-6/DUP14                  LT-SEM-STK-6/DUP15
LT-SEM-STK-6/DUP16                  LT-SEM-STK-6/DUP2                   LT-SEM-STK-6/DUP3
LT-SEM-STK-6/DUP4                   LT-SEM-STK-6/DUP5                   LT-SEM-STK-6/DUP6
LT-SEM-STK-6/DUP7                   LT-SEM-STK-6/DUP8                   LT-SEM-STK-6/DUP9
LT-SEM-STK-6/SWAP1                  LT-SEM-STK-6/SWAP10                 LT-SEM-STK-6/SWAP11
LT-SEM-STK-6/SWAP12                 LT-SEM-STK-6/SWAP13                 LT-SEM-STK-6/SWAP14
LT-SEM-STK-6/SWAP15                 LT-SEM-STK-6/SWAP16                 LT-SEM-STK-6/SWAP2
LT-SEM-STK-6/SWAP3                  LT-SEM-STK-6/SWAP4                  LT-SEM-STK-6/SWAP5
LT-SEM-STK-6/SWAP6                  LT-SEM-STK-6/SWAP7                  LT-SEM-STK-6/SWAP8
LT-SEM-STK-6/SWAP9                  LT-SEM-STK-7                        LT-SEM-STO-1
LT-SEM-STO-2                        LT-SEM-STO-3                        LT-SEM-STO-4
```

### 8.1 Deterministic input selection

Frozen, so that no test's inputs are an author's choice:

1. **Boundary-first.** For a postcondition over a numeric domain, inputs are drawn in this
   fixed order until its stated condition is met: `0`, `1`, `2`, `2²⁵⁶ − 1`, `2²⁵⁵`, then
   ascending integers from `3`.
2. **Pairs** are drawn in lexicographic order over that same sequence.
3. **Addresses** are `0x…0aaa` for a caller, `0x…0c42` for a callee, `0x…0dad` for a third
   party — matching the upstream fixtures.
4. **Byte strings** are the shortest satisfying the condition, then `0x42` repeated.
5. **Stack depth** fixtures use the smallest depth that exercises the stated rule.

### 8.2 Branch completion

Step 0 §3.1.3 rule 2 adds one test per branch left uncovered by rule 1. Branches do not exist
until the clean implementation does, so their IDs cannot be enumerated here. Frozen instead:

- ID form `LT-BR-<unit>-<nnn>`, allocated in ascending order of source position;
- the input for each is found by the terminating search procedure of §8.2.2 over the total
  order of §8.2.1;
- they may assert **only** postconditions surviving §5.1, never one the projection excluded.

#### 8.2.1 Total input enumeration

§8.1 orders numbers, pairs, addresses, byte strings and stack depths — but a clean
implementation will branch on `frame.static`, on `FrameResult.halt`, on the call kind, on
whether an account exists, and on combinations of those. For such predicates "the first value
in §8.1 order" names nothing, and author choice would walk straight back in at step 6 of §10,
which is precisely what `LT-BR-*` exists to prevent. The order is therefore total over every
domain the frozen model contains:

```text
bool                    false, true
FrameResult.halt        NORMAL, EXCEPTIONAL
call kind               CALL, STATICCALL, DELEGATECALL
address                 0x…0aaa, 0x…0c42, 0x…0dad, zero address   (§8.1 rule 3, then zero)
account presence        absent, present-with-empty-code, present-with-non-empty-code
storage slot            account absent; account present & slot never written;
                        account present & slot written zero;
                        account present & slot written non-zero
tx.to                   absent, present
tx.from                 absent, present
uint256                 §8.1 rule 1
byte string             §8.1 rule 4
stack depth             §8.1 rule 5

records (Frame, FrameResult, TxContext, World, operand tuples)
                        the Cartesian product of their field domains,
                        enumerated lexicographically by the field order in
                        which §2 declares them
```

`TxContext` and `World` are in that list deliberately. `U-ENTRY` branches on whether `tx.to`
and `tx.from` are present (`SEM-ROOT-2/3`), and a first implementation writing
`account?.storage.get(slot) ?? 0n` branches on the storage-slot states above — so an
enumeration that stopped at "account presence" would have left "the first frozen input"
undefined for exactly those branches, and the word *total* would have been doing more work
than the table under it.

#### 8.2.2 The branch-search procedure

The enumeration above orders the domains; it does not by itself say how a witness is found,
and the earlier stop rule made that gap worse by keying on whether a branch was *reachable*.
Deciding reachability of an arbitrary program branch is not a task to hand an experimenter
mid-qualification — it is the halting problem wearing a lab coat. The procedure below never
asks the question:

```text
for each uncovered branch arm, in frozen source order:

    enumerate candidates from the §8.2.1 stream for that unit's
    input record, in the frozen product order, up to budget B

    first candidate that covers the arm
        -> emit LT-BR-<unit>-<nnn>, inputs recorded verbatim

    no candidate covers it within B
        -> NO_FROZEN_BRANCH_WITNESS, naming the arm and B
        -> stop E1-v1, preserve the record
        -> continue only as a new E1-v2 preregistration

B = 4096 candidates per arm, frozen here.
```

This terminates unconditionally: every arm either gets a witness from a frozen, ordered,
finite prefix, or produces a named stop. Whether the arm was *truly* unreachable or merely
unreached within `B` is not decided, and does not need to be — either way E1-v1 halts and the
result is preserved. `NO_FROZEN_BRANCH_WITNESS` supersedes the earlier
`UNREACHABLE_UNDER_FROZEN_DOMAIN`, which claimed a reachability verdict the procedure could
not deliver.

**Why the stop is a stop, and not an amendment.** This condition can only surface at step 6 of
§10, and step 3 has already demonstrated coverage and mutation on Baseline A — so a measured
run has happened and Step 0's freeze has bitten. The strict reading is also the honest one:
**the Baseline A measurement is the moment the freeze becomes final**, exactly as Step 0 §0
promises, and a witness gap found afterwards is a v1 result to preserve, not a document to
edit. Redefining "measured run" as the first injected-specimen measurement would weaken
Step 0's freeze contract retroactively for no gain, and is rejected.

A hand-written fixture invented at the keyboard to close such a gap is prohibited outright.
Without this procedure the enumeration is deterministic only until the first
`if (frame.static)`, and a single improvised fixture would silently convert the frozen plan
back into an authored one.

Two digests, therefore:

```text
plan_core_digest      over the 213 case IDs above, frozen NOW (§8.3)

test_domain_digest    over the realised list, recorded at step 6 of §10 —
                      after the clean Baseline B exists and before any
                      defect is injected. Must be a superset of the 213,
                      differing only by LT-BR-* entries generated by the
                      frozen procedure.
```

A realised domain that drops a core ID, or adds a non-`LT-BR-*` entry, violates this plan and
invalidates the run.

### 8.3 `plan_core_digest`

SHA-256 over the 213 IDs, sorted ascending as ASCII, joined by `\n`, with a trailing newline.
The listing in §8 is the canonical input.

```text
plan_core_digest = 63b4d9f9e1b40a08d2bd3f862ce072fb036bc6401f4360823cc5bfc8d79aae02
```

---

## 9. `c2_control_suite`

Per Step 0 §3.2.2, a separate domain with its own digest, used by C2 and nothing else.

C2 is the **positive control with a local oracle**: the same defect as D1, but with the local
suite permitted one assertion the projection withholds. It must therefore remain a *local*
test that breaks the discipline in exactly one place — not a composition test.

```text
c2_control_core  = the 213 core IDs of §8
                 + exactly one preregistered assertion:

    LT-C2-SEM-SEAM-P7
        U-CALL exercised in isolation, with U-RUN substituted by a SPY.
        Perform STATICCALL. Inspect the frame argument the spy captured.
        Assert capturedFrame.static === true.
```

### 9.1 The frozen relation, not two frozen lists

Freezing the two *core* lists is not enough. At step 6 of §10 the calibration domain grows by
the realised `LT-BR-*` set, and if C2's domain were left at "213 core + one assertion" the
two would diverge into:

```text
D1   213 core + LT-BR-*
C2   213 core + spy assertion
```

— which is no longer *the same evidence plus one local oracle*, and the contrast C2 exists to
draw would be gone. What is frozen is therefore the **relation**:

```text
final_calibration_domain = 213 core + realised LT-BR-*
final_c2_domain          = final_calibration_domain + LT-C2-SEM-SEAM-P7
```

checked mechanically at step 6, before any defect exists:

```text
final_c2_domain  -  final_calibration_domain  ==  { LT-C2-SEM-SEAM-P7 }
final_calibration_domain  -  final_c2_domain  ==  { }
```

Either check failing invalidates the run. `c2_control_core_digest` below remains as the
pre-implementation commitment to the core plus the one assertion; the final domains carry
`test_domain_digest` and `c2_control_test_set_digest`, both recorded at step 6.

Two points this pins down:

**It restores `SEM-SEAM-P7`, not `SEM-REL-3`.** `SEM-SEAM-P7` is the producing-side
postcondition D1 actually violates. `SEM-REL-3` requires a real producer *and* a real
consumer, so restoring it would have made C2 a composition test — a small W6 — and C2 would
no longer demonstrate what it exists to demonstrate. An earlier draft made exactly that
mistake.

**It breaks the discipline in one named way: it inspects a collaborator argument.** That is
precisely the clause of §3.1.2(a) whose absence hides D1. So the three-way contrast is exact:

```text
D1   calibration suite forbids collaborator-argument assertions   -> green
C2   one preregistered spy assertion on that same argument        -> red
W6   both sides real, no doubles at all                           -> red
```

`c2_control_suite` is never handed to the mutation engine or coverage instrumentation for any
D-specimen, and contributes to no §5.1 result.

```text
c2_control_core_digest = c4273493fd9c001687c9b745df3e1f900a64a3fe746c8d91142298dd3587a051
```

---

## 10. Revised implementation sequence

The sequence in Step 0 §9 was not executable as written: it placed the local-suite
qualification before Baseline B, while the frozen plan contains level-B postconditions
(`SEM-MEM-*`, `SEM-STO-*`, `SEM-GRD-*`, `SEM-HLT-*`, `SEM-CALL-*`, `SEM-SEAM-C*`,
`SEM-RET-*`). That asked for coverage and mutation thresholds over production code that did
not yet exist. Branch completion has the same problem one step further on.

Superseding §9 steps 3–7 (Step 0 §9 steps 1–2 stand):

```text
3.  Baseline A          write the M0 protocol manifest FIRST (Step 0 §8), then
                        level-A units; green on the 49-case level-A oracle slice;
                        harness, coverage, mutation and manifest replay
                        demonstrated. This measurement makes the freeze final.

4.  core local tests    all 213 case IDs written from §8. Level-B ones fail at this
                        point, which is expected and recorded — the units do not exist.

5.  Baseline B, clean   implement the complete surviving level-B semantics of §3 —
                        memory, storage, the guard, halting, the entry frame, the
                        CALL-family operand contract, frame construction, and the
                        consuming side. The relational invariants of §3.7 are
                        composition-only and are NOT implemented as a separate
                        mechanism; they hold, or fail, as a consequence of the rest.
                        NO defects.

                        Green on the 65 level-B oracle cases (Step 0 §1.4 — the 71
                        in-subset cases less the 6 witnesses); all 213 core tests
                        green.

6.  qualification       enumerate LT-BR-* from the clean source by §8.2.2; freeze
                        both final domains and run the §9.1 set-difference check;
                        record test_domain_digest and c2_control_test_set_digest;
                        run the clean coverage and mutation qualification to the
                        Step 0 §3.3 thresholds with NoCoverage == 0; confirm W1-W6
                        all green (§4.1 arm 1). Append the M1 clean-baseline
                        record (Step 0 §8). A NO_FROZEN_BRANCH_WITNESS finding
                        here stops E1-v1 (§8.2.2).

7.  proxy               gated on the Step 0 §5.1.1 circularity check, then
                        e1-static-test-proxy/v0.

8.  injections          catalog Step 0 §6, both revisions measured. Append an M2
                        specimen record (Step 0 §8) BEFORE each injected
                        measurement.
```

The final domain digest is fixed at step 6 — after the clean Baseline B and **before any
defect exists**. That ordering cannot tune anything to an outcome, because the
branch-completion algorithm was frozen in §8.2 and no injected specimen exists yet to tune
towards.
