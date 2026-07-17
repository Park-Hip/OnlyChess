# E2 — Migration plan and target architecture

**Status:** plan-only (roadmap E2). No implementation code. Written after
[E1](engine-gap-analysis.md).
**Decides:** rebuild-vs-migrate, the target architecture, the wave order, the walking skeleton.
**Priority, stated once and applied throughout:** *extensibility is the goal; the game is the test of
it.* Where the two conflict below, extensibility wins and the cost is written down.

> **All three blocking decisions are settled** (§6, 2026-07-17): folder-per-piece assets, a
> `game_mode` content type, and the castling bug fixed. **Wave 0 is unblocked** — the only work left
> before code is the `.lc` spike.

---

## 0. The strategic question — migrate or rebuild?

The roadmap assumes a migration: *"sequence the refactor so the game stays runnable and the tests stay
green throughout."* That instinct is right about **risk** and wrong about **code**. Both halves matter,
and separating them is what makes this decision tractable.

### Count what actually survives

`src/` is 4,430 lines, of which ~2,000 is UI and ~2,400 is engine. Against the finished spec:

| Today | Fate | Lines |
|---|---|---|
| `pieces/standard.py`, `pieces/fused.py`, `pieces/registry.py` | **Become `mods/base-*/pieces/*.yaml`** | 383 |
| `events/*.py` (10 event files) | **Become `mods/base-events/events/*.yaml`** | ~600 |
| `abilities/{bishop_snipe,knight_swap,pawn_sprint,rook_shield}.py` | **Become `mods/base-chess/abilities/*.yaml`** | ~140 |
| `fusion/rules.py` | **Becomes `mods/base-fusion/fusion/rules.yaml`** | 26 |
| `game/mode_config.py` | **Becomes `mods/base-events/pool/main.yaml`** | 12 |
| `game/castling.py` | **Becomes `base:chess`'s `code/`** | 83 |
| `game/shield_tracker.py`, `game/action_points.py` | Deleted; replaced by generic systems | 62 |
| `pieces/base.py`, `game/move.py`, `game/board.py` | **Rewritten** — E1 §2.1, §2.2, §2.8 | 586 |
| `constants.py` | Mostly deleted | 69 |
| `ui/` | **Survives**, ~4 touch points | ~2,000 |

**About 1,300 lines become data. About 700 more get rewritten.** What is left of the engine after
removing everything that is content or that E1 says is broken is not a codebase you migrate — it is
a `Board` grid, a UI, and a test suite.

**So it is a rebuild.** Pretending otherwise produces a migration that touches every file anyway,
without the licence to get the shape right.

### But rebuilds die

The graveyard argument is real and it is not a cliché: a rewrite with no running artifact loses the
only feedback that matters, and this project has a working game with 182 passing tests. Throwing that
away to chase an architecture is how preparation phases like this one end up as the whole project.

### The resolution: rebuild the core, keep the old engine alive as an oracle

**Build the new engine alongside the old, behind the loader. `main.py` keeps running the old one until
the new one can play a full game. Then cut over and delete.**

Two things make the strangler unusually cheap here, and they are worth stating because they do not
generalise:

1. **There is no ongoing feature work.** The old engine is frozen by the roadmap itself — Gate 4
   forbade code for months. The usual killer of parallel-engine work (every new feature costs double)
   **is zero here**.
2. **The old engine is a differential oracle, and that is worth more than the test suite.** 182 tests
   is a rounding error next to *"generate 10,000 random positions and assert both engines produce the
   same move list."* That test only exists while both engines do.

The oracle is the argument. Everything else about the strangler is ordinary.

> ### What the oracle can and cannot do — be honest about this up front
>
> **It works for move generation**, which is the part with the most surface, the most silent failure
> modes, and the three transcription hazards D1 flagged (`limit` off-by-one, the pawn double-step,
> fusion's matching axes).
>
> **It does not work for events.** They are random, and the new selector engine will enumerate the
> board in a different order than a hand-written scan, so a shared RNG seed still yields different
> choices. Events need structural tests (*"exactly one R/N/B per side is poisoned"*), not equality.
>
> **It is not an equality test — it is an equality-modulo-a-list test.** The spec has *deliberate*
> divergences: the pawn's `has_moved` double-step (C3 finding 3), status stacking taking `max`
> (status-model), and the castling fix below. **That is a feature.** Every difference the oracle
> reports must be either a bug or on a written list, and the list is short enough to review. It
> converts "we think we preserved behaviour" into "here are the four places we didn't, on purpose."

---

## 1. The finding that shapes the architecture

E1 found `Move` is content-aware and the two pipelines have drifted. Planning surfaced something
sharper, and it is the best available argument that the spec's shape is right.

### `capture:`, `castle`'s hack, and a live chess bug are one missing concept

**Verified.** `square_under_attack` asks *"does any enemy **move** end on this square?"* The correct
question is *"does any enemy piece **threaten** this square?"* For pawns these differ **in both
directions**:

- A pawn's **forward push is a move but not a threat** → false positive.
- A pawn's **diagonal onto an empty square is a threat but not a move** → false negative (the engine
  only generates the diagonal when a victim is already standing there).

The false negative is a real, reachable, mods-free rules bug:

```
Black pawn on e2 attacks d1 and f1. f1 is a castling pass-through square.
  square_under_attack(f1) = False  <- should be True
  in_check (king on e1)   = False  <- correctly False; pawns do not attack forward
  legal castle moves offered: ['e1g1']
```

**White castles through a square a pawn attacks.** Illegal in chess.

Now notice what else is the same concept:

| Symptom | Today |
|---|---|
| Pawn push counts as an attack | Attack gen ignores `capture: false` — it does not exist in code |
| Pawn diagonal on an empty square is not an attack | Move gen conflates "can move here" with "threatens here" |
| `castle` must be excluded from attack gen | `include_castle=False`, a bool threaded through 3 functions, dispatched on `KING_CODE` (E1 §2.4) |

**One concept, three hacks, and the schema already has the field.** `capture: allowed / false / only`
is in `content-schemas.md` because the pawn earned it. The engine never reads it, because the engine
has no notion of a threat distinct from a move.

**So the target engine generates two things from one move part**: the **moves** it offers and the
**threats** it projects. `capture: false` → moves, no threats. `capture: only` → threats, and moves
only onto occupied squares. `castle` → moves, no threats. `include_castle` evaporates, the pawn bug
evaporates, and `base:chess` registers `castle` with `threatens=False` through the ordinary verb path
with no engine special case.

**This is the single best evidence so far that the spec's vocabulary was derived correctly.** The
field that fixes a bug nobody knew about was already there, earned by content, for an unrelated
reason. It is also a warning: **the schema is ahead of the engine in more places than this one**, and
the rebuild should look for them rather than port hacks forward.

> **Decision needed (§6):** fixing this changes standard chess behaviour. It is a *bug fix*, but it
> is also a divergence the oracle will report. It goes on the list either way — the question is
> whether it goes on the list as "fixed" or "preserved".

---

## 2. Target architecture

```
mods/
  base-chess/  base-fusion/  base-events/  <third-party>/

src/
  modding/                THE LOADER — the 9 stages
    parse.py              ruamel chokepoint; rejects stock PyYAML; retains .lc
    resolve.py            graph, cycles, originator rule
    validate.py           schema × frozen vocabulary; the error contract
    patch.py              replaces → set/add/remove → re-validate
    register.py           normalize (every `limit` in the vocabulary), populate
    link.py               resolve every cross-reference; did-you-mean
    api.py                ★ THE PUBLIC VERB PATH — the only way verbs exist
    registries.py         content registries + verb registries
    errors.py             mod id · file · line:col · field · problem · expected
  engine/
    board.py              geometry + sides, from a board layout
    piece.py              ONE Piece class: PieceDef (shared) + instance state
    movegen.py            walks move parts → dispatches to move-type verbs
    actions.py            Relocate / Remove / Replace — the relocation contract
    pipeline.py           simulate | apply; the hookable stages
    turn.py               the turn lifecycle E1 says does not exist
    status.py             central; ticks; resolves `modifies` at move-gen time
    bus.py                triggers + the capture bus
    selector.py           scope / filter / pick
    condition.py          pure predicates
    effect.py             the six effect verbs
    resource.py           per-side quantities of registered resources
    events.py             pool schedule + two-phase runner + bindings
  ui/                     ~unchanged; 4 touch points (§5)
```

### 2.1 ★ The verb path is an **injected API object**, not an import

The most important structural decision in this document, because the dogfooding claim rests entirely
on it.

```python
# mods/base-chess/code/__init__.py
def register(api):
    api.move_type("castle", castle_fn, threatens=False)
    api.move_type("enpassant", enpassant_fn)
```

The loader calls `register(api)` at stage 4. Mods **do not import from `src`**.

Why this and not imports:

- **It solves a real open question.** `loader-lifecycle` asks whether `code/__init__.py` is importable
  or exec'd, because mods live outside `sys.path`. Injection makes the question disappear.
- **It makes privilege impossible to hide.** `CLAUDE.md` says the base mod gets no private API. With
  imports, "no privilege" is a *convention* — nothing stops core reaching into a registry directly.
  With injection, the API object **is** the surface, and if `base:chess` needed something extra it
  would have to be a different object, visibly.
- **It makes the claim testable.** Pass a recording fake `api` to `base:chess`'s `register` and assert
  exactly what it registers. **That is the dogfooding claim as an executable test**, and it does not
  exist in any other design.
- **It gives the loader control.** The api object can refuse registration after stage 4 (the
  vocabulary freeze) by simply going dead. No global state to police.

**Consequence for the freeze:** the vocabulary freezes when stage 4 ends, i.e. when the last
`register(api)` returns. Enforced by the object, not by discipline.

### 2.2 One `Piece` class; identity is data

```python
class PieceDef:        # shared, from YAML, immutable
    id, name, sprite, material, components, moves, on, properties

class Piece:           # per instance
    defn, side, pos, has_moved, statuses: dict[id, StatusInstance], properties
```

Flyweight. **`standard.py` and `fused.py` cease to exist** — 340 lines of classes become 10 YAML
files. `create_piece(id, side, pos)` looks up a `PieceDef`, and `_PIECE_REGISTRY`'s dict literal
becomes registry output.

`components` defaults to `[<own id>]`, so `tag_any`/`primary` work uniformly and F3's two axes are one
field. E1 §2.9's dead `fusion_components` attribute goes with it.

### 2.3 ★ A `Move` is a list of **actions**

Today `Move` carries `is_castle_move`, `is_enpassant_move`, `is_pawn_promotion` — three content-shaped
booleans — plus ten rollback snapshot fields, and `GameState` has six hand-written inverse methods.

```python
class Move:
    piece, start, end
    actions: [Relocate(piece, to), Remove(piece), ...]
    threatens: bool
```

- **Castle** is a move with two `Relocate`s. **En passant** is a `Relocate` plus a `Remove` at a
  square that isn't the destination. **No flags.**
- **Rollback is reversing the actions.** Six inverse methods and ten snapshot fields collapse into
  one `undo(action)` per action type. This is what makes `get_valid_moves`'s simulate-everything loop
  safe rather than a minefield.
- **The relocation contract (F8) is `Relocate`.** King tracking and castle rights update *there*, once.
  `knight_swap` reaching into `GameState._update_king_position_after_piece_relocation` (E1 §2.7)
  stops being possible, because there is nothing else to reach for.
- **`is_pawn_promotion` does not exist.** Promotion is `on: trigger: moved` + `when:
  { at_promotion_rank: true }`, which is where the spec already put it. E1 §2.1 dissolves.

**A code mod's move type returns actions.** That is what makes "add a `drop` move type" real rather
than aspirational: shogi drops are `[Relocate(piece_from_hand, square)]` and need no engine change.

### 2.4 `simulate` ≠ `apply`

```python
pipeline.simulate(move)   # actions only, then undo. For king-safety tests.
pipeline.apply(move)      # actions → triggers → capture bus → turn end
```

Today `make_move` runs promotion during *simulation* — constructing and discarding a piece for every
candidate promotion — which is why `promotion_choice='Q'` is a parameter on `make_move`, a UI concept
leaking into the legality checker.

**Promotion is provably irrelevant to own-king safety**: the promoted piece stands on the same square
as the pawn would, so occupancy and therefore blocking are identical, and it is your own piece so it
cannot check you. Skipping triggers during simulation is both correct and faster.

### 2.5 One capture bus — this is how the two pipelines unify

E1 §2.2: `finish_ability_turn` duplicates three post-move systems and omits two, which is why
`bishop_snipe` hand-calls `record_capture`, and why snipe does not fuse.

```python
bus.emit(Capture(capturer=…, captured=…, displaced=bool))
```

- A capturing **move** emits it with `displaced=True`.
- `bishop_snipe`'s **`credit: self`** emits it with `displaced=False`.
- **Capture tracking** listens. **`base:fusion`** listens and applies `fuses_on`.

One bus, one emission point per capture, and `fuses_on: displacing_captures` becomes a real filter on
a real field instead of a rationale for an accident. **A mod's `mymod:assassinate` gets scoring and
fusion for free**, which is the entire point and is impossible today.

### 2.6 The turn lifecycle must be **built**, not preserved

E1 §2.3 verified there is no rule: `ability_used_this_turn` is vestigial and `can_use` never checks
whose turn it is. The UI is the only thing stopping white from acting twice.

```python
class TurnManager:
    current_side
    def can_act(side) -> bool
    def end_turn(side)      # THE one path — moves and abilities both use it
```

Once abilities are data, core is the only caller and the UI's accidental enforcement is gone. **Every
data-defined ability inherits an unlimited-actions exploit unless this exists first**, which is why it
is Wave 3 and not Wave 5.

> **Extensibility call.** "Using an ability ends your turn" is base-game *policy*, and a mod may well
> want free actions. But no content earns a verb for it, and `CLAUDE.md` is explicit that vocabulary
> is earned. **Resolution: the policy lives in core, but it fires through the bus**, so a future code
> mod can intercept `turn_ending` without a refactor. Shape accommodates; vocabulary stays small.
> That is `CLAUDE.md`'s rule applied exactly as written — *get the shape right, keep the vocabulary
> small* — and it is the pattern for every similar call below.

### 2.7 Statuses resolve at move-generation time

```python
def effective_move_parts(piece):
    parts = piece.defn.moves
    for status in piece.statuses:          # most-restrictive wins
        parts = apply_modifiers(status.defn.modifies, parts)
    return parts
```

One central rule; **every piece — including a modder's — is poison-aware for free**, where today a new
piece is silently immune. Deletes five `getattr(self, "poisoned_turns", 0)` checks, `ShieldTracker`,
`ChessEvent.tick`/`cleanup`, and three copies of `_is_piece_on_board`.

It also **fixes E1 §5.1 by construction**: statuses live on pieces and tick centrally, so no event
holds a stale list and no transformed piece can be stranded frozen.

**Gap:** status-model leaves stacking across *different* statuses unspecified. The loop above needs an
answer. **Proposal: most-restrictive wins (`min` of limits, `disable` dominates).** It is the only
composition that is order-independent, and order-independence is the property that matters — two mods'
statuses must not depend on which loaded first.

---

## 3. The waves

Each wave ends with the game running and the oracle green. Sizes are relative, not estimates.

### Wave 0 — De-risk (no product code)

| # | Work | Why first |
|---|---|---|
| ~~**S1**~~ | ~~The `.lc` spike~~ | ✅ **Done, 2026-07-17. Passed.** `ruamel.yaml>=0.18` declared; all 6 checks green, incl. the unknown-key case and a path through a seq index. **Three findings** → [roadmap](roadmap.md#s1-is-done--the-lc-spike-passed-and-narrowed-adr-003): pydantic is disqualified on positions, jsonschema paths the unknown-key case worst, and **patch provenance is an unmodelled hole in the error contract**. |
| **S2** | **The differential harness**, old-vs-old. A position description → both engines; compare move sets. | The safety net for every wave after. Build it while it is trivially green. |
| ~~**S3**~~ | ~~Asset ID scheme~~ | ✅ **Decided** (§6.1): folder per piece, file per side. The ~20 file renames are Wave 2 work. |
| **S4** | **Standing gates G1–G3** (§7), written as the seam lands in Wave 1. | ~20 lines total, and they are the only checks that see the invariants. Cheap now; retrofitted checks find violations after they are load-bearing. |

### Wave 1 — The seam

`api.py`, the registries, and enough loader to read one file: parse (with the PyYAML rejection),
register, activate. The error contract from the first error it can produce — **not retrofitted**,
because `file:line:col` is architecture and E1 §3.1 is a standing lesson about deferred verification.

Nine stages are the target, not a big bang. They arrive as the content types that need them do.

### Wave 2 — Walking skeleton

`mods/skeleton/` — one manifest, one board layout, one piece. The game loads it and draws the piece.
Old engine still runs the real game. **This is the first moment anything is proven end to end.**

### Wave 3 — Engine core

`Piece` + `PieceDef`; `movegen` with `slide` and `leap`; `Move` as actions; `simulate`/`apply`;
`TurnManager` (§2.6); the bus; `status`.

**Oracle gate:** new vs old move generation for the six standard pieces, no castle/enpassant.
Every difference is a bug or on the divergence list.

### Wave 4 — `base:chess`

`castle` + `enpassant` registered through `api` (**the dogfooding test — assert it with a recording
fake**). Threat generation replacing `include_castle` (§1). `base:shield`. Resources. Abilities.
Promotion, including the player-choice contract and the UI's option list.

**Oracle gate:** full standard chess. This is where the divergence list earns its keep.
**Gate G1 goes live here** (§7) — the first moment `castle` exists is the first moment "core didn't
register it" is checkable.

### Wave 5 — `base:fusion` and `base:events`

Selector, condition and effect engines. The fusion table + capture bus + `fuses_on`. The pool, the
two-phase runner, bindings. Ten events.

**Not oracle-tested** — structural tests instead (§0).
**Gate G4 goes live here** (§7): the probe fixtures. By Wave 5 the `api` is complete enough that "a
code mod adds HP as a verb, a data mod uses it" either works or names the missing capability.

### Wave 6 — Cutover and delete

`main.py` → the new engine. Delete the old core. Then the deletion list from E1 §4.

**On the 182 tests: they are restructured, not ported.** Most of them test that a rook slides in
straight lines — which is now `mods/base-chess/pieces/rook.yaml`, and the test splits into "the
`slide` verb works" plus "the loader loads that file". Tests of deleted code are retired with it.
**Do not preserve them as a compatibility shim** — that would keep `piece_code` alive to satisfy
tests, which is the thing this whole project exists to remove.

---

## 4. What could go wrong

| Risk | Reality | Mitigation |
|---|---|---|
| **The parallel engine never converges** and the project stalls with two half-engines | The classic strangler failure | Every wave ends green and the oracle is objective. If Wave 3 doesn't converge, the design is wrong and that is worth knowing at Wave 3. |
| **The loader is a big up-front build** before anything runs | Real | Wave 2 forces end-to-end before the loader is complete. Stages arrive with the content types that need them. |
| **Performance.** Interpreted move-gen inside `get_valid_moves`'s simulate-everything loop | ~900 move-gens/turn today; a data-driven layer adds a constant factor | Irrelevant at human speed and 60fps. **Do not optimise.** It would matter for an AI, which is out of scope. |
| **The oracle's divergence list grows** until it explains everything | The failure mode that makes it worthless | Cap it. Four entries are known. **A fifth needs a written argument**, not a shrug. |
| **`.lc` doesn't work** as specified | Genuinely unknown | S1, first, before anything depends on it. |
| **Scope creep into UI** | 2,000 lines, tempting, unrelated | Four touch points (§5). Nothing else. |

---

## 5. The UI's four touch points

The spec says almost nothing about rendering, so this is E2's to name:

1. **`render_board.py:122`** — `getattr(piece, "is_shielded", False)` → a generic status read, or a
   modder's `mymod:ward` is invisible. (This is what status-model's UI warning *should* have said —
   E1 §3.1.)
2. **`promotion_menu.py:56`** — hardcodes Q/R/B/N. Must take the option list from the pawn's
   `into:` + `choose: mover`. **This is C3 finding 2's move-pipeline contract, and it is smaller than
   feared**: the UI pre-flights *"what will this move offer?"*, shows it, then applies. No coroutine,
   no suspending pipeline. ⚠️ **The limit is honest and must be stated: `choose:` works only where the
   choice is knowable before the move.** An event effect with `choose:` mid-execution would need a
   real suspend. v1 earns only promotion, so v1 does not build one — but validation must reject
   `choose:` outside a piece trigger, or a modder writes something that cannot run.
3. **`assets.py`** — `STANDARD_SPRITE_KEYS` is 20 hardcoded `f"{color}{code}"` strings and
   `build_image_path` is `images/{key}.png`. Needs S3.
4. **`assets.py`'s Queen fallback** — a missing sprite prints a warning and **silently renders a
   queen**. That is exactly `CLAUDE.md`'s *never silently skip malformed content*, in the one place a
   modder's typo lands. **It must become a load error** at the asset stage.

---

## 6. Decisions — all three settled 2026-07-17

The three blockers are closed. Recorded with their reasoning so a later session does not reopen them.

### 6.1 ✅ Asset ID scheme — **folder per piece, file per side**

`sprite: base:sprites/warden` resolves to **`<mod>/assets/sprites/warden/<side_id>.png`**.

Chosen over a flat `warden_white.png` because it **extends to a board with any number of `sides`
without string-mangling** — a three-sided total conversion adds a third file and no new concept. And
over declaring sprites per side inside the piece file, because that mapping is entirely mechanical
and would cost two lines in every piece for nothing.

Replaces `assets.py`'s 20 hardcoded `f"{color}{code}"` keys. Costs ~20 file renames, once.
Closed [mod-package](spec/mod-package.md)'s asset open question.

⚠️ **`load_images`' Queen fallback dies with it** (§5.4). A missing sprite currently prints a warning
and silently renders a queen — `CLAUDE.md`'s *never silently skip malformed content*, in the one place
a modder's typo lands. It becomes a load error.

### 6.2 ✅ Board and pool selection — **a `game_mode` content type**

Specified in [content-schemas](spec/content-schemas.md) → Game mode. A mode names a `board:` and its
`pools:`; the engine requires ≥1 registered; **the player picks one in the existing menu.**

The reasoning worth keeping: **any engine rule for picking a board needs a rule for picking that
rule.** The recursion has to terminate, and the only terminator that does not make core name a mod is
a *player choice* — which already exists in `menu_screen.py`. `mode_config.py` is the type's ancestor,
which is what earns it: an existing hardcoded mechanic becoming data, not a new one.

**It pays for itself immediately: UC11 stops being a disable chain and becomes data.**
`base:vanilla` (`pools: []`, in `base:chess`) is standard chess **as a menu entry** — where before,
"disabling `base:events` yields playable chess" needed a mod manager to reach. The requirement is now
met twice, one of which a player can actually use. `base:advanced` (`pools: [base:main_pool]`) has to
live in `base:events`, because that is where the ID it names is visible — **the dependency rules place
each mode without anyone choosing.**

**Stage 9's activation requirement changes** from "≥1 board layout" to "≥1 `game_mode`". Strictly
stronger (a mode requires a board), still names no mod. Closed
[loader-lifecycle](spec/loader-lifecycle.md)'s oldest open question.

### 6.3 ✅ The castling bug — **fixed, and on the divergence list**

§1. The engine offers `e1g1` while a black pawn on e2 attacks f1.

**Fixed.** The new architecture fixes it *by not reproducing the hack*: once a move part generates
moves and threats separately, the conflation that causes it has nowhere to live. Preserving it would
mean writing code to deliberately reintroduce a bug.

**The counter-argument, recorded because it was real:** the spec has a precedent of *not* fixing live
behaviour — F2 (seven events ignore shields) and F4 (stun does not stop abilities) were both surfaced
rather than corrected. The distinction that decided it: **those are game-design inconsistencies
somebody could have meant; this is a rules bug nobody designed.** And the precedent's actual rule was
"make it visible, then a human decides on purpose" — which is what happened here.

**Divergence list: 4 → 5.** The oracle will report `e1g1` missing from the new engine's move list in
positions like the one above, and that is the expected result, not a regression.

### 6.4 The two live bugs — fix now or let the rebuild dissolve them?

**Recommendation: dissolve.** E1 §5.1 (the frozen piece) and §5.2 (no turn rule) are both fixed by
construction in Waves 3 and 4. A point fix is throwaway work on code scheduled for deletion. The
counter-argument is real if the rebuild slips: §5.1 is currently unreachable at stock tuning, but the
moment `every:` becomes tunable data it is not — **so it must not ship as data before Wave 3 lands.**

### 6.5 `material` in `properties`? — cheap, defer

C3 flagged it: `scoring.py` reads `material`, which is core knowing a chess concept, and under UC12 it
is meaningless. Still a one-line change later. Defer.

---

## 7. Standing gates — how this stays on track

The phase gates (1–4) were scaffolding for a phase with **no executable feedback**, where reading was
the only check available. Waves 0–6 have a machine. So the question *"do we need a reviewer?"* has a
different answer here than it did in Phase C, and the project's own record answers it.

### What review does and does not catch — measured, not assumed

**Gate 3 was a review pass. It found nine defects and none of the three that mattered.**

| Defect | Kind | Caught by |
|---|---|---|
| Nine Gate 3 findings | **Consistency** — spec vs spec | ✅ review |
| `random_zone` couldn't express its only consumer | **Correspondence** — spec vs source | ❌ review (it passed Gate 3) → D1, by transcribing |
| The message model fitted no event | **Correspondence** | ❌ review → D1, by transcribing |
| `render_panels` "displays active events" | **Correspondence** | ❌ review → E1, by reading `src/` |

**Review catches consistency. Only contact with reality catches correspondence.** Three for three.
Adding a reviewer buys more of what already works and none of what has been failing — and
**self-review has now failed three times**, which rules out the cheap version.

The waves fix this by construction: every one ends with the game running and the oracle green.
Correspondence is checked continuously and by a machine.

### The hole the oracle cannot see

**`CLAUDE.md`'s invariants are architectural, not behavioural, so no test in this plan checks them.**
Every one of these passes the full suite *and* the oracle:

- `if piece_id == "base:queen"` in core
- core registering `castle` itself instead of `base:chess` registering it
- a verb added on speculation that no content earns
- the `api` object bypassed by reaching into a registry directly

That is the entire point of the project, invisible to every check planned so far. **The fix is not a
reviewer — it is to make the invariants executable**, which is this project's own philosophy applied
to itself: we don't police the prime directive, we make the prime directive checkable.

| Gate | Check | Cost | Enforces |
|---|---|---|---|
| **G1** | **Disable `base:chess` → assert `castle` is not a registered move type** | ~5 lines | *The base game is a mod.* If core registered it, this fails. **The dogfooding claim, executable** — today it is a promise nobody can check |
| **G2** | **No `[a-z0-9_]+:[a-z0-9_]+` literal in `src/engine/` or `src/modding/`** (narrow allowlist for error-message examples) | ~10 lines | *Core may never name content.* Brutal, mechanical, catches the violation D1 found hiding in `cost: { ap: 3 }` |
| **G3** | **A golden list of registered verbs**; adding one requires editing it | ~5 lines | *Vocabulary is earned.* Puts "is this earned?" in the diff, where it cannot be skipped |
| **G4** | **The probes as a test fixture mod** — see below | ~100 lines, Wave 5 | *Extensibility.* The only gate that tests the goal rather than the implementation |

### G4 — the probes are the acceptance suite, and `CLAUDE.md` already said so

> *"A modder wanting HP ships a code mod registering a damage hook and a `modify_property` verb; HP is
> then data. We never write HP — we make HP writable."* — `CLAUDE.md`

So build exactly that, **in `tests/fixtures/`, never in `mods/`**: a code mod that registers the hook
and the verb, and a *data* mod that uses HP. Same for UC14 (conditional powers) and UC15 (missions),
both of which need triggers the v1 vocabulary does not have — which is the point: they must arrive
**via `api`**, not via an engine edit.

- It works → extensibility is proven by construction, continuously, for free.
- It cannot be written → **the API is incomplete**, and you learned it from a test rather than from a
  stranger's bug report a year later.

⚠️ **The failure mode to watch, stated because it is the exact thing `CLAUDE.md` warns about:** the
moment a probe is hard, the tempting fix is to add the mechanic to the engine. That is the probe
succeeding — it found a missing capability — and *implementing the probe* is the documented way to
misread the whole project. Add the capability, not the mechanic. **If a probe fixture ever moves out
of `tests/`, something has gone badly wrong.**

### What no gate covers

Honest boundaries, so nobody mistakes green for done:

- **D3 is not substituted by any of this.** The probes test whether the API can *express* things; D3
  tests whether a human can *learn* it. G4 passing says nothing about the modder guide. Gate 4 still
  has one leg.
- **Events are not oracle-tested** (§0) and G1–G4 do not touch them. Structural tests only.
- **Taste.** Whether the architecture is *good* is not checkable. That is what a reviewer would be
  for, and it is the one thing on this list a machine cannot do — so if a reviewer ever becomes
  available, point them at §2, not at the diffs.

---

## 8. What planning found that the spec did not

Recorded in E1's spirit — the spec is checked, not trusted.

1. **`capture:` already fixes a live chess bug** (§1). The schema is ahead of the engine.
2. **Selector context is unmodelled, and it is a validation rule nobody wrote.** `friendly: true/false`
   is defined as *"relative to the acting piece"*, and `of: self` / `include_self` all presuppose a
   `self`. **An event step has no acting piece.** So those are meaningless — and must be *errors* —
   inside an event, while being ordinary inside an ability. Checked against the base mod: **no event
   uses them**, so the files are consistent and nothing is broken. But nothing in `content-schemas.md`
   says a selector's legal keys depend on where it sits, and stage 5 cannot validate what is not
   written. **A modder writing `friendly: true` in an event gets an unknown-`self` crash at fire time
   — the exact `KeyError`-at-turn-20 failure the loader exists to prevent.**
3. **Status stacking needs an answer** (§2.7) and status-model deliberately left it open. The engine
   cannot; the loop has to do something. Most-restrictive-wins, for order-independence.
4. **`choose:` needs a validation fence** (§5.2). Earned only by promotion; expressible anywhere;
   implementable only where the choice precedes the move.
