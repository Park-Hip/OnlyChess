# Phase A1 — Content Audit

**Status:** complete. Feeds Phase B (declarative feasibility study).
**Method:** every piece of content in `src/` read and decomposed mechanically — what it selects,
what it changes, for how long, and what undoes it. Prose descriptions were ignored in favour of
what the code actually does.

**Surface audited:** 10 events, 4 abilities, 10 pieces, 6 fusion pairs.

## The headline

The content itself is **more tractable than expected** — nearly everything decomposes into
`select → pick → effect → duration`, and movement is already primitive-based. But the audit found
that the *same mechanic is enforced three different ways* depending on which mechanic it is, and
that **selectors are hand-enumerated piece-code lists**. Both are O(content × content) couplings
that a mod would silently break. They are the real findings; see [Cross-cutting findings](#cross-cutting-findings).

---

## Events (10)

**All ten share one trigger.** `EventManager` queues a single random event from the pool, warns at
`turn % EVENT_CYCLE_TURNS == EVENT_WARNING_OFFSET`, executes one turn later. No event defines its
own timing, condition, or trigger. See finding **F5** — this is load-bearing for the schema.

| Event | Selector | Pick | Effect | Duration | Shield respected? |
|---|---|---|---|---|---|
| `comeout` | all pawns, any colour | random 1 | transform → Queen | instant | **no** |
| `gia_xang_tang` | **primary component = Rook** (hand-enumerated as R, Chancellor, Warden) | all | transform → Knight | instant | **no** |
| `kho_ga_tron_ba_mia` | code in (R,N,B,A,C,W,I), per colour | random 1 per colour | apply poison | 3 turns | **no** |
| `long_toi_tan_nat…` | all queens | all | destroy | instant | **no** |
| `mat_quyen_cong_dan` | (a) black pawns (b) white pawns | random 1 each | (a) destroy (b) **change colour** → black | instant | **(a) yes (b) no** |
| `my_danh_iran` | random 2×2 zone, **chosen at warning time** | all in zone | destroy | instant | **yes** |
| `nguoi_chong_bat_luc` | all kings | all | immobilize (`is_active=False`) | 1 turn | **no** |
| `tai_xiu` | random side (coin flip), non-king | random 1 | destroy | instant | **yes** |
| `umamusume` | all non-king | all | transform → Knight | instant | **no** |
| `viec_nhe_vol_cao` | all pawns | all | stun (`is_active=False`) | 2 turns | **no** |

Every event emits a compact notation string on execution, with `"0x"` as the universal "nothing
happened" marker. Messaging is a real schema dimension, not a detail.

`nguoi_chong_bat_luc` (immobilize) and `viec_nhe_vol_cao` (stun) are **mechanically identical** —
both set `is_active = False`, store a countdown attribute, tick it down, and restore. They differ
only in name, target, and duration. Two names, one mechanic.

## Abilities (4)

Uniform shape: gated on AP, owner matched by **fusion tag** (not piece code — the one place tags
are used correctly), validate target, apply, consume turn.

| Ability | Owner tag | AP | Target rule | Effect |
|---|---|---|---|---|
| `bishop_snipe` | Bishop | 3 | enemy on unobstructed diagonal, not shielded | destroy + record capture |
| `knight_swap` | Knight | 2 | any friendly piece | swap positions |
| `pawn_sprint` | Pawn | 1 | 3 squares forward, empty, self not stunned | move; promote → Queen if last rank |
| `rook_shield` | Rook | 3 | self (`requires_target = False`) | shield self + orthogonal friendly neighbours |

`Ability.use()` in `src/abilities/base.py` owns the shared flow (check → validate → spend →
apply → `finish_ability_turn`). This is the cleanest existing seam in the codebase.

## Pieces (10)

| Piece | Movement | Material | Poison-aware? |
|---|---|---|---|
| Pawn | forward 1; forward 2 from start rank; diagonal capture; en passant | 1 | no |
| Knight | 8 leaps | 3 | **yes → cannot move at all** |
| Bishop | slide diagonal, unlimited | 3 | **yes → slide becomes 1 step** |
| Rook | slide orthogonal, unlimited | 5 | **yes → slide becomes 1 step** |
| Queen | slide 8-directional, unlimited | 9 | **no check** |
| King | step 8-directional + castling | 0 | no (uses `is_active`) |
| Archbishop | bishop full + knight full | 6 | inherited via delegation |
| Chancellor | rook full + knight full | 8 | inherited via delegation |
| Warden | rook full + **bishop limited to 3** | 7 | **yes, hand-written twice** |
| Inquisitor | bishop full + **rook limited to 3** | 7 | **yes, hand-written twice** |

**Good news for Phase B:** every piece except Pawn and King is `(direction set × limit)` composed
with `+`. Fused pieces are literally the sum of their components' move sets. `_get_sliding_moves`
and `_get_one_step_moves` already exist. Data-defined pieces are close to free.

**The exceptions are the exceptions:** Pawn (direction-dependent, first-move double, capture
differs from movement, en passant) and King (castling, which reaches into `castle_rights` and
`square_under_attack`). Any piece schema must handle these or explicitly punt them to code.

## Fusion (6 pairs)

| Capturer | Captured | Result |
|---|---|---|
| Knight | Bishop | Archbishop |
| Bishop | Knight | Archbishop |
| Rook | Knight | Chancellor |
| Knight | Rook | Chancellor |
| **Rook** | **Bishop** | **Warden** |
| **Bishop** | **Rook** | **Inquisitor** |

**The asymmetry is principled: the capturer's movement dominates.** Rook takes Bishop → Warden
(full rook + limited bishop). Bishop takes Rook → Inquisitor (full bishop + limited rook).

But the principle is **only half-applied** — knight pairs collapse to one result regardless of
direction, with both components full. Do not try to derive fusion results from a rule. Keep the
explicit 6-entry table (finding **F10**).

---

## Capability surface

The union of every verb the mod API must express.

**Selectors** — `all` · by exact piece code · by enumerated code set · by colour (fixed / random /
both) · exclude king · exclude shielded · spatial zone · adjacency (orthogonal neighbours) · line of
sight (unobstructed ray) · friendly/enemy relative to a piece

**Pick strategies** — all matching · random 1 · random 1 per colour

**Effects** — destroy · transform piece type (+ state-preservation policy) · **change owner
colour** · apply status with duration · move piece · swap two pieces · promote · record capture
(score side-effect)

**Durations** — instant · N turns with tick-down and expiry

**Statuses** — poison · stun · immobilize · shield (4 distinct, though stun ≡ immobilize)

**Messaging** — compact notation per effect; `"0x"` when nothing matched

---

## Cross-cutting findings

These are the audit's real output. Each is a coupling that would silently break under modding.

### F1 — Status enforcement happens at three different tiers *(most important)*

| Status | Enforced where | Consequence |
|---|---|---|
| stun / immobilize | **centrally** — `Piece.get_possible_moves` checks `is_active` | works for any piece automatically |
| shield | **semi** — `Piece.can_capture_target` checks `is_shielded`, but events re-check by hand via `getattr` | works for captures; every event must remember |
| poison | **not at all** — each piece class decides what poison means to it | **new pieces are silently immune** |

Poison has no central meaning. Knight interprets it as "cannot move," Bishop and Rook as "slide
becomes one step," Queen/King/Pawn ignore it entirely, Archbishop and Chancellor inherit it
accidentally through delegation, and Warden and Inquisitor hand-write it twice each.

This is safe today *only by convention*: `kho_ga_tron_ba_mia`'s eligible list happens to exclude
exactly the pieces that don't implement the check. Nothing enforces that. **A modder's new piece is
poison-immune by default and nothing warns anyone.** This is O(statuses × pieces).

### F2 — Shield respect is inconsistent and probably unintentional

Three events respect shields, seven don't, and `mat_quyen_cong_dan` respects it for its destroy
half but not its colour-change half. There is no visible principle. Some of this is surely
deliberate (a shield arguably shouldn't stop a global queen purge); some looks like drift.

A schema forces this to become an explicit per-effect field. That is a **feature of the refactor**
— it converts an invisible inconsistency into a decision someone has to make on purpose.

### F3 — Selectors hand-enumerate what are actually *principles* → O(events × pieces) drift

`gia_xang_tang` ("all rooks become knights") targets `(Rook, Chancellor, Warden)` and excludes
Inquisitor — even though Inquisitor contains a rook. **This is deliberate, not a bug.** The list is
exactly the set where `primary_component_code == ROOK`:

| Piece | Components | `primary_component_code` | Hit by `gia_xang_tang`? |
|---|---|---|---|
| Rook | — | Rook | yes |
| Chancellor | (Rook, Knight) | Rook | yes |
| Warden | (Rook, Bishop) — *Heavy Rook* | Rook | yes |
| Inquisitor | (Bishop, Rook) — *Heavy Bishop* | **Bishop** | no |
| Archbishop | (Knight, Bishop) | Knight | no |

The rule is "pieces that are **primarily** rooks," and `primary_component_code` — a field the engine
already maintains — expresses it exactly. The finding is not a missing entry. It is that **a clean
principle is encoded as a fragile hand-written list**, and the list must be re-audited every time a
piece is added. Forgetting is silent. Commit `d69b0ca` ("fix: update Warden and Inquisitor being
affected by events") is that maintenance burden already biting once.

**This reveals two distinct selector axes, both real and both needed:**

- **"contains X"** → `get_fusion_tags()` — used correctly by abilities (a Warden can use rook *and*
  bishop abilities)
- **"is primarily X"** → `primary_component_code` — needed by `gia_xang_tang`, and currently
  expressed only by hand-enumeration

A schema with just one axis cannot express the base game. `kho_ga_tron_ba_mia`'s seven-code list is
the same problem in the "contains" axis.

### F4 — Transform has two unnamed state-preservation policies

- *Copy everything except identity* (`color`, `name`, `pos`, `id`, `direction`) — `comeout`,
  `mat_quyen_cong_dan`
- *Copy `has_moved` only* — `gia_xang_tang`, `umamusume`

So a poisoned rook transformed by `gia_xang_tang` **loses its poison**, while a poisoned pawn
transformed by `comeout` **keeps it**. Neither policy is named or documented. The schema must make
this an explicit choice.

### F5 — Trigger is not a dimension of variety

All 10 events share one hardcoded trigger. This **massively simplifies a v1 schema** — there is
exactly one trigger to model, and no event needs conditions.

It is also the first thing modders will want to break. "Fire an event when a queen is captured" is
an obvious first request and is currently inexpressible. Phase B must decide whether to model
triggers now or accept that v1 events are cycle-only.

### F6 — Massive duplication that a selector primitive deletes

`_is_piece_on_board` is copy-pasted into three events (each an O(64) board scan). Nearly every
event hand-rolls its own nested `for row / for col / get_piece_at` collection loop. A single
selector primitive removes essentially all of it.

### F7 — Statuses are stored two incompatible ways

Poison, stun, and immobilize are raw attributes on the piece (`poisoned_turns`, etc.), ticked by
the *event* that applied them. Shield uses a real `ShieldTracker` object — and has **unusual expiry
semantics**: it expires after the *opponent's* turn, keyed by `shield_owner`, not by a countdown.

A unified status system must handle "expires relative to whose turn it is," not just "N turns."
Shield is the awkward case that will shape the design.

### F8 — Abilities reach into `GameState` privates

`knight_swap` calls `game_state._update_king_position_after_piece_relocation(...)`. Any effect that
relocates a piece needs this. It must become part of a public, documented contract before mods can
move pieces.

### F9 — Warning is data, not just text

`my_danh_iran` picks its 2×2 zone **in `__init__`** — at warning time — and the UI telegraphs it.
Every other event's warning is a static string. The schema needs a telegraph concept: warnings can
carry state that execution later consumes.

### F10 — Fusion asymmetry is real and half-principled

See [Fusion](#fusion-6-pairs). Model as an explicit ordered-pair table. Do not derive.

---

## Implications for Phase B

Carry into the feasibility study:

1. **Tag-based selectors are mandatory, and there are two axes** (F3): "contains X"
   (`get_fusion_tags`) and "is primarily X" (`primary_component_code`). The base game needs both.
   Test every event's selector against tags rather than code lists during the experiment.
2. **Decide where status meaning lives** (F1). Either the engine centralizes "poison limits
   movement" for all pieces, or the O(statuses × pieces) coupling ships to modders. This is a
   design decision, not a cleanup.
3. **Shield's expiry model breaks a naive countdown** (F7). Design the status system against
   shield first; poison and stun are easy afterwards.
4. **Transform needs a named state policy** (F4), and shield-respect needs an explicit per-effect
   field (F2). Both are currently invisible decisions.
5. **Trigger modelling is a scoping call** (F5). Cycle-only is honest for v1 and defensible under
   the "smallest engine" rule — but say so out loud rather than by omission.
6. **Pawn and King are the hard cases** for a piece schema. Everything else is
   `(directions × limit)` composition. Expect them in bucket 2 or 3.
7. **`mat_quyen_cong_dan` changes piece ownership** — the only event that does. Verify no engine
   assumption breaks when a piece switches colour mid-game (king tracking, castle rights, material).

## Bugs and inconsistencies found (not the audit's job to fix)

Logged so they are not lost. **Do not fix these now** — several may be deliberate, and the refactor
may erase them anyway.

- `mat_quyen_cong_dan` respects shields when destroying but not when converting (F2) — unclear
- Transform state policies disagree about whether statuses survive (F4) — unclear
- Queen ignores poison entirely; safe only because the poison event never selects her (F1)
