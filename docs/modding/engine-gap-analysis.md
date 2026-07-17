# E1 — Engine gap analysis

**Status:** complete. Plan-only, as Phase E requires — no code was changed.
**Method:** every file in `src/` read against the finished spec. Where a claim was cheap to test
rather than argue, it was tested; those are marked **verified** and the transcript is reproducible.
**Scope:** what in `src/` blocks the spec, and what that implies for E2's ordering.

**Input to:** [E2 migration plan](migration-plan.md) (not yet written).
**Reads against:** [content-schemas](spec/content-schemas.md), [status-model](spec/status-model.md),
[loader-lifecycle](spec/loader-lifecycle.md), [mod-package](spec/mod-package.md).

> **Gate 4 was passed on one leg** (roadmap). The non-coder test never ran. Nothing in E1 depends on
> it, but the field names this document treats as settled are the ones D3 would have challenged.

---

## The headline

**The three known blockers are all real, and none of them is the biggest problem.**

`CLAUDE.md` names import-time registration, identity in `constants.py`, and the missing status
system. All three confirmed. But the survey found a fourth that outranks them, and it is the one
thing nobody has been treating as a blocker:

> **`Move.__init__` knows what a pawn is.** Every `Move` ever constructed — thousands per turn, in
> the inner loop of move generation — reads `PAWN_CODE` and the board's dimensions to decide
> `is_pawn_promotion`. The most-constructed object in the engine is content-aware, and it is
> upstream of everything: pieces build `Move`s, so `Move` cannot be fixed after pieces are.

Second: **the ability path and the move path are two pipelines that have already drifted**, and the
drift is not cosmetic. `finish_ability_turn` reimplements three of the five post-move systems inline
and silently omits the other two. That is why `bishop_snipe` hand-calls `record_capture`, and it is
the actual reason snipe does not fuse — which is **not** the reason the spec recorded.

Two live defects were found and verified, both in the seams the refactor is about to remove. One of
them (§5.1) is a **permanent piece-freeze that stock tuning hides and the spec's own tunable event
pool would expose**.

**Working in our favour, and it is significant:** 182 tests pass, the post-move pipeline is already
an ordered list of objects, movement is already primitive-based, and `Ability.use` is already
check → validate → spend → apply → finish. The seams the spec assumes mostly exist. They are just
full of content.

---

## 1. The three known blockers, confirmed

### 1.1 Import-time registration — confirmed, and one case is worse than described

`CLAUDE.md` describes `@register_event` + an import list. Accurate. But the three registries are at
**three different levels of badness**, and only the survey makes that visible:

| Registry | Mechanism | Registration hook? |
|---|---|---|
| Events | `@register_event` on the class + a 10-line import list in `events/__init__.py` | Yes, but firing on import |
| Abilities | `@register_ability` — which **instantiates**: `_ABILITY_REGISTRY[key] = ability_class()` | Yes, but firing on import |
| **Pieces** | `_PIECE_REGISTRY = { PAWN_CODE: Pawn, … }` — **a literal dict** | **None. There is no hook at all.** |

`pieces/registry.py` is the blunt one: adding a piece means editing a dict literal in core. There is
no decorator to repurpose, so the piece path is a **build**, not a migration.

Two consequences the spec's stage 7 has to absorb, neither of which is in the spec:

- **`register_ability` constructs the instance at import.** Abilities are stateless singletons, so
  this works — but stage 7 must produce ability *instances* from data, and `use_ability` looks them
  up by key. The registry's value type is an object, not a class.
- **`EventManager.__init__` instantiates the queued event immediately**, from a module-level
  `DEFAULT_EVENT_POOL` computed at import from `mode_config`. So event content is bound at
  `GameState()` construction, one layer below the loader.

### 1.2 Identity in `constants.py` — confirmed, and it reaches well past `constants.py`

Every code in `constants.py` (`PAWN_CODE`, `WHITE`, `STANDARD_PIECE_ORDER`, …) is what the spec
replaces with namespaced IDs. That much is known. What the survey adds is **where those constants are
read**, because that is the actual migration surface:

| Site | What it names | Why it is not just a rename |
|---|---|---|
| **`Move.__init__`** | `PAWN_CODE`, `LAST_BOARD_INDEX` | Computes `is_pawn_promotion` on **every Move**. See §2.1 |
| `Move.ranks_to_rows` etc. | 8×8 chess notation | Class-level dicts. `a`–`h`, `1`–`8` |
| `castling.get_piece_moves` | `KING_CODE` | Core dispatching on a piece code. See §2.4 |
| `King.get_castle_moves` | `ROOK_CODE` | Named in the spec; core naming content |
| `castling.update_castle_rights_for_move` | `KING_CODE`, `ROOK_CODE`, corner columns | Rights logic keyed to two piece codes and board corners |
| `Board.setup_classic` | `STANDARD_PIECE_ORDER`, `Pawn`, rows 0/1/N-2/N-1 | Called **from `Board.__init__`**. See §2.5 |
| `Pawn.__init__` | `WHITE` | `direction = -1 if color == WHITE else 1` — the spec's `sides.forward` |
| `Pawn._calculate_moves` | `BOARD_ROWS - 2`, `1` | The rank-gated double-step (spec finding 3) |
| `ActionPointTracker.__init__` | `WHITE`, `BLACK` | `{WHITE: …, BLACK: …}` — two sides baked into a dict literal |
| `state_helpers.format_square` | `"abcdefgh"`, `8 - row` | D1 gap 8, confirmed |
| `state_helpers.format_piece_fan` | `"p"` | `letter = "P" if code == "p" else code.upper()` — core special-casing the pawn's code inside a **formatter** |
| `scoring.calculate_material_advantage` | `WHITE` | The `material` open question, live |

**`format_piece_fan` deserves a callout.** It is the implementation of the spec's `{piece}` template,
and it contains a magic string for one specific piece. The spec's message vocabulary is therefore
resting on a function that knows what a pawn is.

### 1.3 No status system — confirmed; four statuses, **three** different mechanisms

Worse than "ad-hoc twice". The four statuses use three storage strategies and two owners:

| Status | Stored as | Ticked by | Blocks moves via |
|---|---|---|---|
| poison | `piece.poisoned_turns` | the event that applied it | **five `getattr` checks inside piece classes** |
| stun | `piece.stunned_turns` **and** `piece.is_active = False` | the event that applied it | `is_active` in `get_possible_moves` |
| immobilize | `piece.immobilized_turns` **and** `piece.is_active = False` | the event that applied it | `is_active` |
| shield | `piece.is_shielded` + `shield_owner` + `shield_turns` | **`ShieldTracker`** | n/a — `can_capture_target` |

Confirming the spec's claims:

- **Poison is checked in exactly five places** — `Knight`, `Bishop`, `Rook` (`standard.py`) and
  `Warden`, `Inquisitor` (`fused.py`), all as `getattr(self, "poisoned_turns", 0) > 0`.
- **The Queen has no poison check**, and is unreachable: `KhoGaTronBaMia.ELIGIBLE_CODES` omits her.
  status-model's account is exactly right.
- **`shield_turns = 1` is vestigial** — written by `ShieldTracker.add`, read by nothing.
- **`can_capture_target` calls `getattr(target, "is_shielded", False)`** in the hot path of every
  move generation, and **`render_board.py:122` reads the same attribute** to draw the shield.

**`stunned_turns` and `immobilized_turns` are two names for one thing**, and neither is load-bearing:
both events set `is_active = False`, which is what actually stops the piece. The counters exist to be
displayed and to be reset. status-model unifying stun and immobilize is confirmed as free.

**`_is_piece_on_board` is copy-pasted into three events**, each an O(64) scan (F6). Confirmed.

---

## 2. New blockers, not in `CLAUDE.md` or the spec

### 2.1 ⚠️ `Move` is content-aware — the finding that reorders E2

```python
# src/game/move.py
self.is_pawn_promotion = (
    self.piece_moved.name == PAWN_CODE and (self.end_row == 0 or self.end_row == LAST_BOARD_INDEX)
)
```

**Every `Move` object decides whether it is a pawn promotion, at construction, by naming the pawn and
the board's edges.** `Move` is built inside `_get_sliding_moves`'s inner loop, so this runs for every
candidate square of every piece on every move generation.

Why this outranks the three known blockers:

- **It is a prime-directive violation in the engine's most fundamental object.** Not a registry, not
  a config — the move.
- **It is upstream of the piece migration.** Pieces construct `Move`s. Data-defined pieces still
  construct `Move`s. So `Move` must lose `PAWN_CODE` **before or with** the piece work, not after.
- **It blocks UC12 twice over** — the pawn reference and the `end_row == 0 or LAST_BOARD_INDEX`
  promotion-rank hardcode, which the spec replaces with `sides.promotes_at`.
- **The notation tables are the same problem**: `ranks_to_rows`/`files_to_cols` hardcode `a`–`h` and
  `1`–`8` as class attributes on `Move`.

The spec has a home for the behaviour — promotion is `on: trigger: moved` + `when:
{ at_promotion_rank: true }` on `base:pawn`, and `at_promotion_rank` reads `sides.promotes_at`. So
**`is_pawn_promotion` should not exist as a `Move` field at all.** That is a bigger change than it
looks: `Move.is_pawn_promotion` is read by `GameState._resolve_pawn_promotion` and by the UI's
promotion menu.

### 2.2 ⚠️ The ability path and the move path have already drifted

Two pipelines run turn side effects. They do not agree, and nothing enforces that they should.

| Post-move system (real moves) | Also in `finish_ability_turn`? |
|---|---|
| `CaptureTrackingPostMoveSystem` | ❌ **omitted** — `bishop_snipe` hand-calls `record_capture` in its own `apply()` |
| `FusionPostMoveSystem` | ❌ **omitted** |
| `ActionPointsPostMoveSystem` | ✅ duplicated inline (`action_points.gain_for_move`) |
| `ShieldExpiryPostMoveSystem` | ✅ duplicated inline (`expire_shields_after_turn`) |
| `EventUpdatePostMoveSystem` | ✅ duplicated inline (`event_manager.update()`) |

**Three duplicated by hand, two silently missing.** `run_post_move_systems` is an ordered, extensible
list; `finish_ability_turn` is a hardcoded copy of most of it. Any system added to the list is
invisible to abilities, and nothing says so.

**This changes what the roadmap's `fuses_on` decision means.** The spec records that `bishop_snipe`
does not fuse, and settles it with `fuses_on: displacing_captures` on `base:fusion` — framed as a
game-design call about displacement. In the code, **snipe does not fuse because the ability path never
calls `FusionPostMoveSystem` at all.** Displacement has nothing to do with it. The current mechanism
is "went through `make_move`".

Do the two rules agree? **Yes — checked against all four abilities.** `knight_swap`, `pawn_sprint` and
`rook_shield` produce no capture; `bishop_snipe` captures without displacing. So `displacing_captures`
reproduces today's behaviour exactly. **But it agrees by coincidence of the current ability set, not
by derivation** — the first mod whose ability captures *and* displaces (a charge, a trample) makes the
two rules diverge, and the spec's rule is the one that will apply. That is the better rule and the
decision stands. It should be recorded as **behaviour-preserving but mechanism-changing**, because the
next person to read "snipe doesn't fuse, therefore displacement" will go looking for a displacement
check in `FusionManager` and not find one.

### 2.3 ⚠️ `ability_used_this_turn` is vestigial — the turn rule is not in the engine

**Verified, not inferred.** The flag is written in four places and read in exactly one
(`abilities/base.py:22`). The only writer that sets it `True` (`board.py:304`) sets it back to
`False` seven lines later, inside the same synchronous call, and no `can_use` runs in that window.
**The read never sees `True`.**

And `Ability.can_use` never checks `white_to_move`. So at the engine level there is **no
one-ability-per-turn rule and no whose-turn-is-it rule**. Both live in the UI's input gating.

Verified by driving the engine directly — white snipes twice, the second time on black's turn:

```
turn=white. snipe 1: True
  white_to_move is now: False (black to move)
turn=black. white snipes AGAIN: True
  both black knights gone? None None
  captures recorded for white: ['bN', 'bN']
```

This **contradicts two spec documents**, and both should be corrected:

- [d1-findings](d1-findings.md) gap 4 lists "one ability per turn — `Ability.can_use` reads
  `game_state.ability_used_this_turn`" as live behaviour. It reads it; it is always `False`.
- [content-schemas](spec/content-schemas.md) → Resource says *"`Ability.use` calls
  `finish_ability_turn`, so spending an ability **is** spending your turn — that is the turn
  lifecycle, which `CLAUDE.md` puts squarely in core."* The **turn flip** is in core. The **rule** is
  not enforced anywhere in core.

The conclusion the spec drew is still right — the turn lifecycle belongs in core and is not a
resource. But it is being cited as *already true*, and it is not. **When abilities become data, core
becomes the only caller, and the UI's accidental enforcement disappears.** If nothing replaces it,
every data-defined ability inherits an unlimited-actions exploit. **E2 must build the rule, not
preserve it.**

### 2.4 The King breaks the piece contract, and core pays for it

`Piece.get_possible_moves(self, gs)` — but `King.get_possible_moves(self, gs, include_castle=True)`.
A subclass widening its signature is why this exists:

```python
# src/game/castling.py
def get_piece_moves(piece, game_state, include_castle=True):
    if piece.get_piece_code() == KING_CODE:
        return piece.get_possible_moves(game_state, include_castle=include_castle)
    return piece.get_possible_moves(game_state)
```

**Core dispatching on a piece code to work around one subclass's signature.** `castle` is meant to be
an opaque verb registered by `base:chess`; this is the shape of the hole it has to fit. Under the
spec, `include_castle=False` (used by `square_under_attack` to avoid infinite recursion) becomes a
property of the *verb* — "this move type does not participate in attack generation" — which the verb
registration contract does not currently have a field for. **Flagged for E2: it is a small gap in the
public verb path, in the exact place the dogfooding claim is tested.**

### 2.5 `Board.__init__` calls `setup_classic()`

```python
def __init__(self):
    self.grid = [[None] * BOARD_COLS for _ in range(BOARD_ROWS)]
    self.setup_classic()
```

**A board cannot exist without the standard chess layout.** Construction and content are welded, and
`GameState.__init__` constructs a `Board()` with no arguments. The loader's stage 9 hands over
registered board layouts; `Board` must take one. Small change, blocks the walking skeleton.

Likewise `GameState.__init__` hardcodes the construction of all six subsystems. `post_move_systems`
is the only injected seam (`create_default_post_move_systems`), and it is the shape everything else
needs.

### 2.6 `limit: unlimited` breaks on non-square boards

```python
def _get_sliding_moves(self, gs, directions, limit=BOARD_ROWS):
    for i in range(1, limit):
```

The "unlimited" default is `BOARD_ROWS`. On a square board that is exactly right (max distance
N−1 = `range(1, N)`). **On a 9-wide × 5-tall board a rook would slide 4 squares horizontally**, not 8.

Invisible today because `BOARD_ROWS == BOARD_COLS == BOARD_SIZE` by construction. It becomes real the
moment `size: [rows, cols]` from a board layout allows them to differ — which is UC12, a stated goal.
The loader's `unlimited` normalization must map to `max(rows, cols)`, not to either one.

**This is the `limit` hazard's third instance**, after `moves` and `base:poison`'s
`movement.slide.limit`. C3's hazard box said normalization is defined over the vocabulary; this says
the *sentinel* is too.

### 2.7 No relocation contract (F8) — confirmed, and narrow

`knight_swap.apply` calls `game_state._update_king_position_after_piece_relocation(piece)` — **an
ability reaching into a private method of `GameState`**. It is the only caller, and it is the whole
of F8: `move`/`swap` effects must maintain king tracking, and today exactly one ability remembers to.

Narrow but real. No event needs it (none relocates a king: `umamusume` skips kings, `comeout` and
`mat_quyen_cong_dan` touch pawns only). So the contract has one consumer today and will have every
`move`/`swap` effect tomorrow.

### 2.8 `move_log` is heterogeneous

`make_move` appends a `Move`; `finish_ability_turn` appends `{"ability_turn": color}` — a **dict**.
`get_half_turn_count()` is `len(move_log)`, so the event clock counts ability turns, which is
correct and is presumably why the dict is there.

`_rollback_last_move` pops the log and immediately touches `move.piece_moved`. **On a dict that is an
`AttributeError`.** Not reachable today — its only production caller is `get_valid_moves`, which
always pairs `make_move` with a rollback — but the tests call `_rollback_last_move` directly, and any
future undo feature pops whatever is on top. A landmine, not a bug.

The spec's turn lifecycle needs one turn-record type covering both. **Nothing in the spec models
this**; it is a gap on the core side of the line, so it needs no schema — but E2 should not discover
it while migrating.

### 2.9 Duplicated ability-ownership predicate

`Ability._piece_has_ability(piece)` and `registry.get_abilities_for_piece(piece)` implement the same
`any(code in piece.get_fusion_tags() ...)` test. One is the spec's `owner: { tag_any: [...] }`. Two
implementations, one rule.

Also: `Piece.get_fusion_tags()` returns `[self.get_piece_code()]` — recomputed — while
`Piece.__init__` separately sets `self.fusion_components = [self.get_piece_code()]`. **For non-fused
pieces `fusion_components` is written and never read**, because only `FusedPiece` overrides
`get_fusion_tags()` to read it. The spec's `components` field defaulting to `[<own id>]` unifies both;
worth knowing one of the two is currently dead.

---

## 3. Where the spec is wrong about the engine

E1's job is to check the spec against source. Two claims do not survive it.

### 3.1 status-model's UI warning is a false alarm

> ⚠️ *"This changes what 'active event' means to the UI. `render_panels` currently displays events
> that are active because their status is still ticking. Once statuses are independent, an event is
> instant and there is nothing to display."* — [status-model](spec/status-model.md)

**`render_panels` does not read `active_events`. Nothing in `src/ui/` does.** The panels draw AP,
captured pieces, material advantage, turn number, and `"Next Event in: N"`. The only UI reads of event
state are `message_log.py:175` (`queued.warning_active`, for the warning banner) and
`game_screen.py:354` (`recently_executed_events`, for the log lines). Both survive the status rewrite
untouched — a warning is still a warning, and an executed event still emits messages.

So the flagged UI migration **does not exist**. What *does* need doing is the opposite and smaller:
`render_board.py:122` draws the shield by reading `getattr(piece, "is_shielded", False)`, and that
one call site must become a generic status read, or a modder's `mymod:ward` is invisible. status-model
is right that the UI should show statuses on pieces; it is wrong about what currently shows what.

**Worth noticing how this got in:** the claim describes plausible behaviour that nobody checked
against `render_panels`. It is D1's finding 8 pattern again — a statement derived from a reasonable
mental model of the code rather than the code — and it survived Gate 3 for the same reason
`random_zone` did. That is now **three** instances of the same failure across three documents. It is
the project's characteristic defect, and it argues that every remaining unverified claim about `src/`
in the spec should be treated as suspect until E-phase code touches it.

### 3.2 The `fuses_on` rationale describes a mechanism that isn't there

See §2.2. The decision is right and should stand; the stated reason ("displacement is what fusion
means physically") is a *justification*, not a description of the current code, which fuses on
"arrived via `make_move`". Fine as design, misleading as archaeology.

---

## 4. What the migration deletes

Recorded because it is the argument for doing this at all, and because E2 should be able to check
them off.

| Deleted | Why it goes | Lines |
|---|---|---|
| `events/__init__.py`'s import list + `@register_event` | Stage 7 populates registries | ~32 |
| `@register_ability` + `abilities/__init__.py` import list | Same | ~20 |
| `_PIECE_REGISTRY` literal | Same | ~43 |
| `mode_config.DEFAULT_ADVANCED_EVENT_POOL` | Becomes `type: event_pool` | ~12 |
| `ShieldTracker` | Central status system | 26 |
| `ChessEvent.tick()` / `cleanup()` + every override | Statuses outlive their source | ~60 across 4 events |
| `_is_piece_on_board` ×3 | One status system, one tick site | ~30 |
| `Piece.can_fuse()` / `King.can_fuse()` | Table membership is total (C3 finding 1) | ~6 |
| 5 × `getattr(self, "poisoned_turns", 0)` | `base:poison`'s `modifies.movement` | ~10 |
| `castling.get_piece_moves` | If the King's signature is fixed | ~5 |
| `ActionPointTracker` | `type: resource` | 36 |
| `get_ability`/`get_event_class` `KeyError` paths | Stage 8 makes dangling refs unreachable | — |

Roughly **280–300 lines of core deleted**, against 4,430 total. The replacement (loader, validator,
status system, verb registry) is certainly larger — but the deletions are all *rules and identity*,
which is the point: what remains is engine.

---

## 5. Live defects found

Both verified by driving the engine. Neither is in any existing bug list.

### 5.1 ⚠️ A transformed piece keeps a status forever — and tuning the event pool exposes it

**Verified.** `ViecNheVolCao` stuns every pawn (`is_active = False`). `Comeout` then transforms a
pawn into a queen, copying the pawn's `__dict__` — including `is_active = False` and
`stunned_turns = 2` — onto the new queen. When the stun expires, `ViecNheVolCao.cleanup()` walks its
own `stunned_pawns` list and calls `_is_piece_on_board(pawn)`. **The pawn object is no longer on the
board — the queen replaced it — so the check returns `False` and the queen is never restored.**

```
pawn after stun: is_active= False stunned_turns= 2
comeout queen: wQ(6,5) | is_active= False | stunned_turns= 2
after stun expires -> queen is_active= False | moves available: 0
```

**The piece is frozen for the rest of the game.** No message, nothing in the UI, no way to recover it.

**Not reachable at stock tuning.** The pool fires one event per 10-turn cycle and the longest status
lasts 3 turns, so two events can never overlap. **It becomes reachable the moment `every:` drops below
the longest duration** — and `every:` is a field in `base:main_pool`, i.e. **exactly the tuning knob
the spec introduces and the Tuner persona (UC1/UC2, the two highest-ranked use cases) reaches for
first.** A modder who sets `every: 2` for a faster game gets permanently frozen pieces and no
explanation.

Three things worth taking from it:

1. **This is the strongest argument yet for the status system going first in E2.** The spec's model
   fixes it *by construction*: statuses live on pieces, a central system ticks them, and `preserve`
   decides whether they survive a transform. There is no list of stale references to go wrong.
2. **It validates D1's `preserve: all_except_identity` for `comeout` as more correct than today**,
   not merely equivalent. The spec keeps the status *and* keeps ticking it. Today's code keeps it and
   loses the ticker.
3. **The class of bug is "the event owns the status's lifetime"** — precisely what status-model
   identified as the architectural problem, found in the wild before anyone refactored anything.

### 5.2 The engine enforces no turn rule for abilities

§2.3. Verified. Currently masked by the UI being the only caller; unmasked by the refactor.

### 5.3 Latent, not live: `primary_component_code` leaks through `Comeout`

The comeout queen inherits `primary_component_code = 'p'` from the pawn (visible in the transcript in
§5.1). So `FusionManager` reads that queen as "primarily a pawn". **Unobservable today**: a rook
capturing her looks up `(R, p)` → not in the table → no fusion, and `(R, Q)` is not in the table
either. Same outcome by luck. Recorded because the spec's `preserve` policies make this an explicit
choice, and because it shows `__dict__`-copying transforms carry identity fields nobody intended.

---

## 6. What this says about E2

Not the migration plan — inputs to it.

**The roadmap's proposed order needs one change.** It currently reads: statuses → namespaced IDs →
loader → content types → delete. `Move` (§2.1) is not in it, and it is upstream of the piece work.
Suggested:

1. **Status system.** Self-contained, no loader dependency, deletes the most code, and **fixes a live
   bug** (§5.1). The roadmap's reasoning holds and E1 strengthens it.
2. **`Move` and the turn record.** Strip `PAWN_CODE`/`LAST_BOARD_INDEX` from `Move.__init__`; give
   `move_log` one record type (§2.8). Before pieces, because pieces build `Move`s.
3. **The two pipelines, unified** (§2.2, §2.3). One path for "a turn's side effects", used by both
   moves and abilities — **and build the turn rule the UI has been faking.** Doing this before
   content migration means data-defined abilities land on a pipeline that is already correct.
4. Namespaced IDs, board dimensions, layout. As the roadmap has it, plus `Board.__init__` (§2.5) and
   the `unlimited` sentinel (§2.6).
5. Loader + registries. Then content types, base mod last-to-first.

Steps 2 and 3 are new and both sit **before** the loader. Neither is large; both are upstream of
everything the loader will feed.

**The walking skeleton is unaffected** — "load one trivial mod, put one piece on the board" needs
§2.5 and the piece registry, and nothing else here.

**One open question E2 must answer that E1 cannot:** `include_castle=False` (§2.4) is core telling a
verb "you don't count for attack generation". The verb registration contract has no field for it, and
`square_under_attack` recurses infinitely without it. That is a real gap in the public verb path, and
it lands on the exact seam the dogfooding claim rests on.

---

## 7. Confidence

- **Verified by execution:** §2.3, §5.1, §5.2, §5.3, and the 182-test baseline.
- **Verified by reading, high confidence:** §1.1–1.3, §2.1, §2.2, §2.4–2.9, §3.1, §4.
- **Judgement, argue with it:** §6's ordering; §2.2's claim that `displacing_captures` and "went
  through `make_move`" agree only coincidentally; §4's line counts, which are approximate.
- **Not covered:** `src/ui/` beyond its couplings to game state (2,000+ lines, and the spec says
  nothing about rendering); audio; assets. The asset ID scheme is open in mod-package.md and
  `src/ui/assets.py` builds fixed paths — that is E2's problem and nobody has looked at it.
