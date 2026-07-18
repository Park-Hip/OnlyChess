# Spec — Content Schemas

**Status:** current contract for content vocabulary and open piece properties.
**Depends on:** [ADR-001](../adr/001-data-format.md) (YAML 1.2), [ADR-002](../adr/002-conflict-semantics.md)
(addressability), [mod-package.md](mod-package.md) (IDs, load order), [status-model.md](status-model.md)
(statuses — **already specified, not restated here**).
**Scope:** the content shapes supported by the active loader and engine.

**Current type set:** the loader accepts thirteen content types: `piece`, `event`, `event_pool`,
`ability`, `fusion`, `board`, `status`, `patch`, `resource`, `game_mode`, `theme`, `hud_layout`,
and `sound`. The presentation types are specified in [presentation.md](presentation.md), and all
thirteen types use the same discovery, validation, patching, registration, and linking pipeline.
The older ten-type wording immediately below is retained as historical design context and must not
be used as an authoring reference.

**Historical ten-type draft:** Eight were originally specified here — **piece**, **event**, **event pool**,
**ability**, **fusion**, **board layout**, **resource**, **game mode**. **status** is specified in
[status-model.md](status-model.md) and **patch** in [Patches](#patch), but both are content types
like any other: they live in files, they declare `type` and `id`, and the loader treats them
identically. Plus the four shared vocabularies they compose from: **trigger**, **selector**,
**condition**, **effect**.

> **`game_mode` was added in E2**, after the loader lifecycle and the modder guide independently hit
> the same unanswered question. See [Game mode](#game-mode).

## How to read this

Every verb below is followed by what earned it. **If a verb has no base-game consumer, it is not in
this spec** — that is the rule from `CLAUDE.md`, and it is why you will not find `modify_property`,
`grant_ap`, counters, or arithmetic here. Those arrive when a code mod registers them.

Two things this spec deliberately does *not* do:

- It does not fix the inconsistencies the audit found (F2, F4). It makes them **visible** as explicit
  fields, so a human decides on purpose. Fixing them silently would change the game.
- It does not model anything UC13–15 need. Those are probes. See `CLAUDE.md`.

## Universal rules

**Every content file declares its type and ID:**

```yaml
type: piece               # required — determines the schema
id: base:warden           # required — namespaced, see mod-package.md
replaces: <id>            # optional, rare — ADR-002's blunt instrument. See Patches.
```

`type` is what makes folders cosmetic (mod-package.md). The loader reads `type`, never the path.
The thirteen legal values are: `piece`, `event`, `event_pool`, `ability`, `fusion`, `board`,
`status`, `patch`, `resource`, `game_mode`, `theme`, `hud_layout`, and `sound`.

**Parameterless choices are written bare; parameterised ones are a single-key mapping.** This is a
convention the schemas already use everywhere and never stated, which made it look like several
unrelated inconsistencies:

```yaml
pick: all                 # bare — takes no parameters
pick: { random: 2 }       # mapping — the key names the choice, the value parameterises it
scope: board
scope: { zone: $zone }
expiry: after_opponent_turn
expiry: { turns: 3 }
```

Stating it once is what lets stage 5 type-check these fields at all: a field of this kind accepts
*either* a name from its choice set *or* a one-key mapping whose key is from that set. Anything
else — two keys, an unknown key — is an error.

**Unknown keys are a load error, not a warning.** A typo'd `limt: 3` must not silently mean "no
limit". This is `CLAUDE.md`'s *validate at load* invariant, and it is the single highest-value
validation rule in the spec — it converts the most common non-coder mistake from a mystery into a
message.

**Field names are API.** ADR-002 makes every field a patch target, so renaming one is a MAJOR bump
(mod-package.md). Name them once, carefully.

**Unqualified IDs resolve to the current mod's namespace** (mod-package.md). Inside `base:chess`,
`queen` means `base:queen`.

---

# Shared vocabulary 1 — Trigger

A trigger answers *when*. It is the first term in `CLAUDE.md`'s trigger → condition → effect shape,
and it is the smallest vocabulary in this spec:

| Trigger | Fires when | Earned by |
|---|---|---|
| `moved` | the subject piece completes a move | pawn promotion |

**One entry, because one entry is earned.** F5 found that all ten events share a single hardcoded
trigger and none needs its own, so events have no `on:` block at all (see
[No triggers in v1](#no-triggers-in-v1--deliberate-and-stated-out-loud)). The only base content that
selects its own timing is pawn promotion, which fires on `moved`. That is the entire v1 set.

Triggers attach through an `on:` block, which is a list — a piece may react to several things:

```yaml
on:
  - trigger: moved
    when:   { at_promotion_rank: true }     # optional condition
    effect: { … }                           # or a list of effects
```

The current public `ModApi` does not yet register triggers, effects, conditions, or selectors. The
only code-mod verb kind currently implemented is `move_type`; `moved` is the built-in content hook
used by promotion. New trigger and effect kinds remain future extensions to be earned by real
content.

---

# Shared vocabulary 2 — Selector

A selector answers *which pieces*. Every effect that touches pieces takes one. This is the primitive
that deletes F6's copy-pasted board scans.

```yaml
select:
  scope: …        # where to look    (default: whole board)
  filter: …       # which qualify    (default: everything)
  pick: …         # how many         (default: all)
```

## `scope` — where to look

| Form | Meaning | Earned by |
|---|---|---|
| `board` | every square (default) | 8 of 10 events |
| `{ zone: $binding }` | a rectangular region | `my_danh_iran` |
| `{ of: self, adjacent: orthogonal }` | the 4 orthogonal neighbours | `rook_shield` |
| `{ of: self, ray: diagonal }` | unobstructed lines outward, stopping at the first piece | `bishop_snipe` |
| `{ of: self, offset: [3, 0] }` | one square, in the piece's own frame | `pawn_sprint` |

**`include_self` defaults to `false` in every scope, including `board`.** `include_self: true` adds
the acting piece back in — earned by `rook_shield`, which shields the rook *and* its neighbours.

The default matters outside `of: self` scopes, which the first draft did not say: `knight_swap`
selects `scope: board, filter: { friendly: true }` and must not offer the knight itself as a swap
target (`target is not piece`). Without a stated default that file is ambiguous, and the ambiguity is
invisible — it would produce a legal-looking "swap with yourself" move.

**Offsets are `[forward, right]` in the piece's own frame, never raw board coordinates.** `[3, 0]` is
"three squares forward" for either colour. This is not sugar: raw `[dr, dc]` would leak the engine's
row-0-is-black orientation into content, and every mod would encode our internal convention. The
frame also makes asymmetric pieces work on a flipped board for free.

## `filter` — which qualify

**The two axes (F3) — both required, neither expressible in terms of the other:**

| Filter | Axis | Matches | Earned by |
|---|---|---|---|
| `tag_any: [base:rook]` | **contains** | Rook, Chancellor, Warden, **and Inquisitor** | abilities |
| `primary: base:rook` | **is primarily** | Rook, Chancellor, Warden, **not Inquisitor** | `gia_xang_tang` |

Both read the piece's `components` list (see [Piece](#piece)). `tag_any` tests membership;
`primary` tests the first element. A schema with one axis cannot express the base game — this is the
audit's F3, and it is the finding most likely to be lost in a redesign.

Everything else:

| Filter | Meaning | Earned by |
|---|---|---|
| `is: base:queen` / `is: [a, b]` | exact piece identity | `long_toi_tan_nat` (all queens) |
| `not: base:king` | exact identity, negated | `tai_xiu`, `umamusume` (non-king) |
| `color: white` / `black` | a fixed side | `mat_quyen_cong_dan` |
| `color: random_one` | one side, chosen by coin flip | `tai_xiu` |
| `friendly: true` / `false` | relative to the acting piece | `knight_swap`, `bishop_snipe` |
| `has_status: [base:poison]` | carries all listed statuses | — *(see note)* |
| `not_status: [base:shield]` | carries none of the listed statuses | `my_danh_iran`, `tai_xiu` |
| `empty: true` | the square holds no piece | `pawn_sprint` |

Filters combine as **AND** within one `filter` block. There is no `or` between filters — no base
content needs it, and `is: [a, b]` already covers the one real case (a list is an implicit or).

> **`has_status` has no base-game consumer.** It is included as the mirror of `not_status`, which
> does. That is a judgement call, and the honest cost of an unearned verb: if a reviewer wants it
> cut, cut it — nothing in the base mod breaks.

**`not_status` is how shield-respect works (F2).** There is no engine rule about shields beyond
`capturable: false`. Seven events ignore shields today; under this schema they ignore shields by
*not writing the filter*, and that becomes visible in the file. The inconsistency is preserved and
surfaced, not fixed. Because the filter is generic, a modder's `mymod:ward` is filterable on day one.

## `pick` — how many

| Form | Meaning | Earned by |
|---|---|---|
| `all` | every match (default) | 5 events |
| `{ random: N }` | N at random from all matches | `comeout`, `tai_xiu` |
| `{ random: N, per: color }` | N at random **per side** | `kho_ga_tron_ba_mia` |

`per: color` is the only grouping key, and the only one earned. `random: N` accepts any N although
base content only ever uses 1 — restricting to exactly 1 would be arbitrary, and N costs nothing.

---

# Shared vocabulary 3 — Condition

**Conditions are pure predicates over game state.** No side effects, no loops, no assignment, no
arithmetic beyond comparison. This is the line from `CLAUDE.md`, and it is the whole reason this
format does not become a bad programming language.

The v1 set is tiny because F5 found that **no event needs a condition at all**. Conditions exist only
where pieces and abilities earned them:

| Condition | Meaning | Earned by |
|---|---|---|
| `at_promotion_rank: true` | the subject stands on its side's `promotes_at` rank | pawn promotion, `pawn_sprint` |
| `has_moved: false` | the subject has never moved | pawn double-step |
| `empty: true` | the destination square is vacant | pawn forward moves |
| `not_status: [base:stun]` | *(selector filter, reused as a condition on the subject)* | `pawn_sprint` |

Combinators — `all_of: [...]`, `any_of: [...]`, `not: {...}` — are **shape, not vocabulary**, and are
available from day one. No base content nests conditions, but a format where predicates cannot
compose is one that needs redesigning the moment a modder writes their second rule.

## The subject is implicit, always

`when:` attaches a condition to a move part, a trigger, an effect, or an ability. **A condition never
names what it is about** — there is no `self:` key, and no way to reach a piece other than the one
the enclosing construct is already about:

| `when:` sits on | The subject is |
|---|---|
| a move part | the moving piece |
| an `on:` trigger | the piece the trigger fired for |
| an effect | that effect's `target` |
| an ability | the owning piece |

Every one of those is "the thing this construct is already about", which is why the rule needs no
vocabulary and no escape. Allowing a condition to name a *different* subject would mean naming a
selector inside a predicate, and a predicate that runs a query is one step from a predicate that runs
a loop. That is the condition line in `CLAUDE.md`, and this is where it would be crossed first.

---

# Shared vocabulary 4 — Effect

An effect changes the game. This is the complete v1 list — the audit's capability surface, minus one.

| Effect | Own fields | Earned by |
|---|---|---|
| `destroy` | `credit:` (optional) | 5 events, `bishop_snipe` |
| `transform` | `into:`, `preserve:`, `choose:` | `comeout`, `gia_xang_tang`, `umamusume`, promotion |
| `set_color` | `to:` | `mat_quyen_cong_dan` — the only consumer |
| `apply_status` | `status:`, `duration:` | `kho_ga_tron_ba_mia`, `rook_shield`, 2 more |
| `move` | `to:` | `pawn_sprint` |
| `swap` | `with:` | `knight_swap` |

## Every effect takes `target:`, and it defaults

**`target:` names the pieces an effect acts on. Every effect has it, and it means the same thing in
all six.** It is omitted in almost all base content, because it defaults to the selection the
enclosing construct already made:

| The effect sits in | `target:` defaults to |
|---|---|
| an event step | that step's `select:` result |
| an ability | that ability's validated `target:` (`$target`) |
| an `on:` trigger | the piece the trigger fired for |

So an event step writes `effect: { type: destroy }` and destroys what it selected. `rook_shield`
writes `target:` explicitly *because* it is the one piece of base content whose effect acts on
something other than the thing it targeted — the ability targets `self`, the effect shields the
neighbours.

Everything an effect needs beyond its subject keeps its own name: `into:` (what to become), `to:`
(where to move, or which colour), `with:` (the other piece in a swap), `status:`, `credit:`.

**This replaces four separate spellings** — `to:` on `apply_status`, `what:` on `move`, `a:`/`b:` on
`swap`, and an undocumented `target:` on `bishop_snipe`'s `destroy` — that all meant "the pieces this
acts on". Four names for one concept is the kind of thing a modder learns by trial and error, and
each spelling would have had to be memorised per effect. It also matters for code mods: a registered
effect verb inherits `target:` and `when:` from the shape rather than reinventing them, so a new verb
composes with selectors on day one without its author thinking about it.

**`promote` is not a verb.** The audit listed it, but promotion is `transform` under a `when:
{ at_promotion_rank: true }` condition. Six effects instead of seven, with no loss. This is what
"vocabulary is earned" looks like in practice — the audit named a *behaviour*, not a *primitive*.

## `destroy`

```yaml
- { type: destroy }                    # events: nobody gets credit
- { type: destroy, credit: self }      # bishop_snipe: counts as a capture by the sniper
```

`credit:` records the removal against a side's capture tally. Without it, a destroyed piece simply
leaves the board — which is what all five destroying events do.

> ### Decided — `credit` does not itself trigger fusion. Displacement does.
>
> **Settled after D1** (it was the last thing blocking `base:fusion`). `bishop_snipe` calls
> `record_capture` and does **not** fuse; under this schema `credit: self` is indistinguishable from
> a capture, so a naive fusion hook would have made snipe fuse and changed the game.
>
> **A dependency constraint closed off most of the answer space before anyone chose.**
> `bishop_snipe` belongs to `base:chess`; fusion belongs to `base:fusion`; and `base:chess` must not
> reference `base:fusion`, because disabling fusion has to leave standard chess playable (UC11).
> **The ability therefore cannot opt out of fusion by name.** The decision had to live in
> `base:fusion` whichever way it went.
>
> The decision, in three parts:
>
> 1. **`credit` stays one concept** — "this counts as a capture by self" — emitting one capture on
>    the bus. Splitting it into scoring-credit and fusion-credit creates two near-identical concepts,
>    and every future listener (a mission counter, a bounty mod) must guess which one it wants. Half
>    will guess wrong and nothing will tell them. It also makes scoring a privileged core listener,
>    when scoring is arguably content.
> 2. **The capture carries whether the capturer displaced** onto the square. That is a move-pipeline
>    fact, not a content fact, so the engine exposes it without naming content. It is also what
>    fusion means physically: the fused piece is placed on the captured square.
> 3. **`base:fusion` declares which captures it fuses on**, via `fuses_on:`. `displacing_captures`
>    preserves today's behaviour exactly.
>
> `fuses_on` takes `displacing_captures` (the capturer ended on the captured square) or
> `any_capture`. Two values, and the second is only there because the first is meaningless without a
> contrast — if a reviewer wants it cut to a boolean, nothing breaks.
>
> **What this buys is not the answer, it is the location.** The question moved out of the engine and
> into a data file, where changing it is a one-line edit rather than a refactor. A modder's
> `mymod:assassinate` emits a capture; `base:fusion`'s rule decides; someone who wants remote
> captures to fuse patches that one field (ADR-002) — and note this is the **first genuine
> base-game-adjacent patch target ADR-002 has**, after C3 looked for one and found none.
> Consistent with `CLAUDE.md`: we don't settle the mechanic, we make the mechanic settleable.

## `transform`

```yaml
- { type: transform, into: base:knight, preserve: [has_moved] }
- { type: transform, into: base:queen,  preserve: all_except_identity }
```

**`preserve` is required — there is no default (F4).** Both current policies exist, unnamed, and they
disagree about whether statuses survive: `gia_xang_tang` drops poison, `comeout` keeps it. Naming
them makes the disagreement a decision. Making one the default would silently pick a winner.

| Policy | Keeps | Used by |
|---|---|---|
| `all_except_identity` | everything but `color`, `id`, `name`, `pos`, `direction` — **including statuses** | `comeout`, `mat_quyen_cong_dan` |
| `[has_moved]` | an explicit field list; **statuses dropped** | `gia_xang_tang`, `umamusume` |

`choose:` handles player-selected promotion — see [the promotion finding](#finding-2--normal-promotion-needs-a-player-choice).

## `apply_status`

```yaml
- { type: apply_status, status: base:poison, duration: 3 }
- { type: apply_status, status: base:shield }              # no duration — see below
```

Duration lives on the application, not the status definition — fully specified in
[status-model.md](status-model.md). Not restated here.

**`duration:` is optional, and supplying it to a status that cannot count is a load error.** Only
countdown statuses (`expiry: { turns: N }`) take one. `base:shield` expires
`after_opponent_turn`, so `rook_shield` supplies no duration and a `duration: 2` on it would be
meaningless. Erroring rather than ignoring it matters because that line is exactly what a modder
copies out of `kho_ga_tron_ba_mia` — and a silently-ignored duration is a shield that looks tunable
and isn't.

## `move` and `swap`

```yaml
- { type: move, target: self, to: $target }
- { type: swap, target: self, with: $target }
```

Both relocate pieces, and **both must go through the public relocation contract, not
`GameState._update_king_position_after_piece_relocation`** (F8). Any effect that moves a piece
maintains king tracking and castle rights. That is an engine gap, logged for E1 — the schema assumes
the contract exists.

---

# Piece

```yaml
type: piece
id: base:warden
name: Warden                          # human-facing
material: 7
components: [base:rook, base:bishop]  # ordered — first is primary
moves:
  - { type: slide, dirs: orthogonal, limit: unlimited }
  - { type: slide, dirs: diagonal,   limit: 3 }
```

That is Warden — the piece that needed a hand-written class with bespoke poison handling twice over.

## `components` — the field that kills F3

An ordered list of piece IDs this piece is composed of. **Defaults to `[<own id>]`.**

- `tag_any` tests **membership** → Warden matches `tag_any: [base:rook]` *and* `[base:bishop]`
- `primary` tests the **first element** → Warden's primary is `base:rook`; Inquisitor's is `base:bishop`

One ordered field, both axes, no redundancy. F3's real complaint was that a clean principle
("pieces that are primarily rooks") was encoded as a hand-written list needing re-auditing on every
new piece. Here the principle *is* the query, and a new piece declares its own components — so it
cannot be silently forgotten by an event written years earlier.

**`base:chess` pieces declare no `components`.** The default gives Rook `[base:rook]`, which is
exactly `get_fusion_tags()`'s behaviour today. This matters: `base:chess` must not depend on
`base:fusion` (UC11), and it doesn't — `components` is a generic tag field the engine reads, not a
fusion concept.

## `moves` — move parts

A piece's moves are the **sum of its parts**.

> **Correction (D1).** An earlier draft said fused pieces "are literally their components' parts
> concatenated, which is why they cost four lines instead of a class". Written out, they are not
> concatenated by anything: `components:` is a tag field the *selectors* read, and `moves:` is
> declared by hand. `base:archbishop` and `base:chancellor` each re-type the knight's eight offsets.
>
> **The four lines are the tags, not the moves**, and nothing checks the two agree — a piece
> declaring `components: [base:rook, base:bishop]` and a knight's moves is valid content.
>
> Deliberately left alone. Fused pieces are authored content, and Warden's 3-square diagonal proves a
> component's moves are *not* always copied wholesale — so an `include:` verb would need an override
> story, and would be a new verb serving four files that already work. Logged, not built.

```yaml
- { type: slide, dirs: diagonal, limit: 3, capture: allowed, when: {…} }
- { type: leap,  offsets: [[1,2],[2,1],[-1,2], …] }
```

| Field | Values | Notes |
|---|---|---|
| `type` | `slide` · `leap` | plus opaque verbs — see below |
| `dirs` | `orthogonal` · `diagonal` · `all` · `forward` · `backward` · `left` · `right` · `forward_diagonal` | piece's own frame |
| `limit` | `unlimited` · N | **N = number of squares.** See the hazard below. |
| `offsets` | list of `[forward, right]` | `leap` only |
| `capture` | `allowed` (default) · `false` · `only` | `false`/`only` earned by pawn |
| `when` | a condition | earned by pawn's double-step |

> ### ⚠️ Migration hazard — `limit` is off by one
>
> The engine's `_get_sliding_moves` uses `range(1, limit)`, so `limit` is **exclusive**: Warden's
> "diagonal up to 3 squares" is written `limit=4` in `fused.py`, with a comment explaining the
> discrepancy. **The schema's `limit: 3` means three squares**, because that is what an author means.
> The loader converts (`internal = N + 1`).
>
> This is small and it will bite. A transcription that copies `4` out of `fused.py` produces a Warden
> with a 4-square diagonal and no error — the exact class of silent breakage this spec exists to
> prevent. Flagged for D1.
>
> **`limit` means squares wherever it appears, not just here.** `base:poison`'s
> `movement.slide.limit: 1` (status-model.md) is the same unit in a different schema, and the loader
> must convert it too. Missing that would cap a poisoned bishop at *zero* squares — silently, since
> nothing in the data would look wrong. Stage 7 owns every `limit` in the vocabulary, not just the
> ones under `moves`.

`dirs` names are relative to the piece's own frame, so `forward` is colour-correct without the piece
knowing its colour. The frame's orientation comes from the side's `forward` (see
[Board layout](#board-layout)).

## Statuses and movement

**A piece never mentions statuses.** Poison's effect on movement is defined once, centrally, in
`base:poison`'s `modifies.movement` block (status-model.md), and the engine applies it to any piece's
move parts.

This is F1 resolved. Verified in Phase B against all ten pieces: one central rule reproduces all five
hand-written poison checks exactly. **A modder's new piece is poison-aware for free** — today it is
silently immune and nothing warns anyone.

## `properties` — the open bag (D10)

```yaml
properties:
  whatever: 3
```

The engine **stores and exposes `properties`; it never interprets them.** This is `CLAUDE.md`'s
mandated shape — *"content with open properties"* — and it is shape rather than vocabulary, so it is
earned by the extensibility requirement itself, not by content.

**The base mod ships zero properties.** That is the point. `hp` is what a modder puts here; we never
write HP, we make HP writable. If you are adding a property to `base:*`, re-read `CLAUDE.md`.

> **Open — `material` is a declared field, and that is arguable.** Core's `scoring.py` reads it, which
> is core knowing a chess concept. Under UC12 (shogi) material advantage is not a meaningful readout
> at all. It probably belongs in `properties` with the score panel as base-game UI. Left declared for
> now because moving it is a one-line change later and the UI question is out of C3's scope.

## Pawn and King — the opaque verbs

The two hard cases resolve as Phase B predicted: **only** by being handed verbs that no composition
of `slide`/`leap` can produce.

```yaml
type: piece
id: base:pawn
name: Pawn
material: 1
moves:
  - { type: slide, dirs: forward, limit: 1, capture: false }
  - { type: slide, dirs: forward, limit: 2, capture: false, when: { has_moved: false } }
  - { type: slide, dirs: forward_diagonal, limit: 1, capture: only }
  - { type: enpassant }               # ← opaque verb, registered by base:chess
on:
  - trigger: moved
    when: { at_promotion_rank: true }
    effect:
      type: transform
      into: [base:queen, base:rook, base:bishop, base:knight]
      choose: mover
      preserve: [has_moved]
```

```yaml
type: piece
id: base:king
name: King
material: 0
moves:
  - { type: slide, dirs: all, limit: 1 }
  - { type: castle, with: { tag_any: [base:rook] } }   # ← opaque verb
```

**There is no `step` move type.** A king is a slide with `limit: 1`, and an earlier draft of this
spec invented `step` for it out of habit. The engine's `_get_one_step_moves` is an *implementation*
of a limit-1 slide, not a second primitive — whether the loader maps limit-1 slides onto it is an
optimisation the author never sees. Two move types, `slide` and `leap`, plus whatever verbs mods
register. This is the earned-vocabulary rule catching a verb that had no distinct meaning.

**`enpassant` and `castle` are registered by `base:chess` through the public verb path — the same one
any code mod uses.** They are not engine special-cases and must never become them. If that path is
privileged, the dogfooding claim in `CLAUDE.md` is a lie, and the honest thing would be to delete the
claim rather than keep the privilege.

Note `castle` takes a `with:` selector rather than hardcoding a rook. Today `King.get_castle_moves`
contains `corner_piece.get_piece_code() == ROOK_CODE` — core naming content, exactly what
`CLAUDE.md` forbids. Parameterising it is nearly free and is the difference between "the engine knows
about rooks" and "base:chess knows about rooks".

The double-step's `when: { has_moved: false }` is a **deliberate divergence** — see
[finding 3](#finding-3--the-pawn-double-step-changes-meaning).

---

# Event

**Events are two-phase** (F9) and **each phase is a list of steps** (`mat_quyen_cong_dan` does two
unrelated things).

```yaml
type: event
id: base:my_danh_iran
name: Mỹ đánh Iran

warning:
  bind:
    zone:
      type: random_zone
      size: [2, 2]
      origin: { rows: [2, 5], cols: [0, 6] }      # inclusive; where the top-left may land
  message: "…"

execute:
  - select:
      scope: { zone: $zone }                       # …read back here
      filter: { not_status: [base:shield] }
      pick: all
    effect: { type: destroy }
    message: { each: "x{piece}@{square}" }

empty_message: "0x"
```

## Bindings — watch this closely

`warning.bind` computes a value at warning time; `execute` reads it as `$name`. **This is the only
place in the entire format where a name is bound to a value, and it exists for exactly one event.**

`CLAUDE.md`'s shape is trigger → condition → effect. Bindings are the seam where that stops being
declarative: a binding is an assignment, and assignments are how data formats become languages. The
guard rails, to be held:

- **Bindings are warning-phase only.** Execution reads; it cannot bind.
- **Bindings are values, not expressions.** `$zone` is a rectangle. There is no `$zone.x + 1`, and
  the condition line already forbids the arithmetic that would make it useful.
- **One binding verb: `random_zone`.** Earned by `my_danh_iran`, and nothing else.

> ### `origin` — added after D1, and a warning about how the rest of this spec was written
>
> `random_zone` originally took a `size` and nothing else. **D1 found it could not express the one
> event it was written for.** The engine constrains the origin:
>
> ```python
> row = random.randint(2, 5)                 # not 0..6
> col = random.randint(0, BOARD_COLS - 2)
> ```
>
> So the strike covers rows 2–6 and **can never touch rows 0, 1, or 7**. Without `origin`, the verb
> would hit the whole board — a strike that deletes a king off its back rank on turn 10. A different
> game, from a verb that looked finished.
>
> `origin` is a rectangle the top-left corner must land inside, inclusive, defaulting to anywhere the
> zone fits. **It must not grow past that.** The temptation will be to allow "not the back two ranks"
> or an expression over `size` — that is the condition line being crossed from the binding side, and
> a rectangle is enough for the only content that exists.
>
> **The real lesson is about method, not about zones.** `random_zone` was written from the audit's
> phrase *"random 2×2 zone, chosen at warning time"* — an accurate description and an insufficient
> specification. It was never checked against `_choose_warning_area`. Every verb derived from a
> summary rather than from source is suspect the same way; D1 found two (this and `message`), which
> is the entire reason D1 exists.
>
> Note also what the constraint *is*: rows 2–5 protects black's back rank and pawn rank, but white's
> pawn rank (row 6) is fair game. That asymmetry looks like a bug. It is live behaviour, and this
> spec preserves it rather than quietly correcting it — the same rule as F2 and F4.

Phase B checked whether `tai_xiu`'s random side needed a binding. It does not — `color: random_one`
covers it, because its message never names the chosen side. **Check that a binding is load-bearing
before adding one.** That check is the difference between a data format and a bad language.

## Messaging

Every event emits a compact notation string; `"0x"` is the universal "nothing happened" marker.
Messaging is a real schema dimension, not a detail — it is the only thing most players ever see of an
event.

**Rewritten after D1**, which found that the first draft matched none of the ten events. See
[finding 7](#finding-7--the-message-model-fitted-no-event).

**A step produces message fragments. The event joins them.**

```yaml
execute:
  - select: { … }
    message: "(All) R=N"                    # ONE fragment, however many matched
  - select: { … }
    message: { each: "x{piece}@{square}" }  # one fragment PER match

empty_message: "0x"                         # event-level: emitted iff no step produced anything
```

| Form | Emits | Earned by |
|---|---|---|
| `message: "…"` | one fragment for the step, if it matched anything | `gia_xang_tang`, `umamusume`, `viec_nhe_vol_cao`, `nguoi_chong_bat_luc`, `long_toi_tan_nat` |
| `message: { each: "…" }` | one fragment per match | `kho_ga_tron_ba_mia`, `my_danh_iran`, `comeout`, `tai_xiu`, `mat_quyen_cong_dan` |

The event concatenates every fragment from every step with `", "`. **`empty_message` is event-level,
not step-level** — `mat_quyen_cong_dan` has two steps and emits `"0x"` only if *both* produced
nothing.

Template vocabulary: **`{piece}` and `{square}`**. Resolved against the fragment's own match —
**not a general expression language**. A message cannot reach into game state; if it wants something
the match doesn't have, that is a signal the step is wrong, not that templates need power.

`{piece}` is the compact FAN — `wN`, `bP` — so it already carries the colour. `{count}` and
`{color}` were in the first draft and are **cut: no event uses either**, which is the earned-verb
rule applied to templates.

## No triggers in v1 — deliberate, and stated out loud

**All ten events share one hardcoded trigger** (F5). No event defines its own timing or condition, so
`on:` does not exist on events. They are invoked by a **pool**.

F5 asked for this to be a decision rather than an omission, so: **v1 events are pool-invoked only.**
"Fire an event when a queen is captured" is inexpressible and will be the first thing a modder asks
for. Accepted knowingly, on the "smallest engine" rule.

The cost of adding it later is low, which is what makes accepting it defensible: pieces already need
the event bus (pawn promotion is `trigger: moved`), so events gain `on:` by reusing machinery that
must exist anyway. What we are *not* doing is building a trigger vocabulary no base content
exercises.

---

# Event pool

The pool is content, not engine. The loader registers each `event_pool`; the selected mode names its
active pools, and the engine advances them according to the data fields below.

```yaml
type: event_pool
id: base:main_pool
every: 10                # turns between executions
warn_before: 1           # warning fires this many turns before execution
pick: { random: 1 }      # one event per cycle
members:
  - base:comeout
  - base:tai_xiu
  # … all 10
```

**Why its own content type rather than per-event scheduling:** the ten events do not each have a
schedule. There is one schedule, and it picks one event at random. Giving each event `every: 10`
would describe a different game — ten events all firing on turn 10.

This also makes the event cycle **tunable data**, which is the Tuner persona's most obvious request
after AP costs.

---

# Resource

**Added after D1.** Abilities cost something. This is the something.

```yaml
type: resource
id: base:ap
name: Action Points
starting: 0
max: 5
gain: { amount: 1, every_moves: 2 }
```

Replaces the old `STARTING_AP`, `MAX_AP`, and `AP_GAIN_MOVE_INTERVAL` constants. The current engine
loads resource definitions and applies their `gain` rules from `EngineState`/`Pipeline`.

**Why this is not gold-plating, given the "vocabulary is earned" rule.** D1 found the AP economy had
no home at all: `cost: { ap: 3 }` was data, but the numbers that decide whether a player *has* 3 AP
were Python constants. That alone is a Tuner-persona failure (UC1 and UC2 are the two
highest-ranked use cases in the project). But the sharper argument is a prime-directive violation
hiding in plain sight:

> `cost: { ap: 3 }` means **the engine knows what AP is.** `ap` is a content identifier, appearing as
> a literal key in a core schema — exactly what `CLAUDE.md` forbids ("core may never name specific
> content"). It read as harmless because AP is the only resource the base game has.

So the cost key becomes the resource's ID:

```yaml
cost: { base:ap: 3 }        # not `ap: 3` — the engine knows "resources", base:chess knows "AP"
```

The engine tracks per-side quantities of whatever resources are registered, and knows nothing about
what they mean. A modder's `mymod:mana` works on day one, and `base:ap` gets no privileges.

`gain: { amount: N, every_moves: M }` is the only accrual rule, and it is the only one earned —
The current pipeline counts completed moves per side and awards the configured amount on the
configured interval.

> **Not here: "using an ability ends your turn."** D1 initially read `ability_used_this_turn` as
> missing tuning, and it is not. Spending an ability *is* spending your turn — that is the **turn
> lifecycle**, which `CLAUDE.md` puts squarely in core. It is not a resource, not a cost, and not
> content. Left alone deliberately.
>
> ⚠️ **Corrected by E1 — the rule is not in core today; it is not implemented at all.** This box
> originally argued the point from the code: *"`Ability.use` calls `finish_ability_turn`, so spending
> an ability is spending your turn."* E1 verified otherwise
> `ability_used_this_turn` is **vestigial**
> — set `True` and back to `False` inside one synchronous call, so `can_use`'s read never sees it —
> and `can_use` never checks `white_to_move` either. **White can use two abilities in a row, the
> second on black's turn**, and the engine allows it. Only the UI's input gating prevents it.
>
> The conclusion stands: this belongs in core, not in a resource. But it is **a rule E2 must build,
> not preserve** — once abilities are data, core is the only caller and the UI's accidental
> enforcement disappears, handing every data-defined ability an unlimited-actions exploit.

---

# Ability

Uniform shape, already the cleanest seam in the codebase (`Ability.use`: check → validate → spend →
apply → finish).

```yaml
type: ability
id: base:bishop_snipe
name: Bishop Snipe
owner: { tag_any: [base:bishop] }        # the "contains" axis — a Warden may use rook abilities
cost: { base:ap: 3 }
target:
  scope: { of: self, ray: diagonal }
  filter: { friendly: false, not_status: [base:shield] }
effect: { type: destroy, credit: self }
```

`owner` uses `tag_any` — the **contains** axis. This is the one place the current code gets F3 right
(`_piece_has_ability` reads `get_fusion_tags()`), and the schema keeps it.

`target: self` replaces `requires_target = False`:

```yaml
type: ability
id: base:rook_shield
name: Rook Shield
owner: { tag_any: [base:rook] }
cost: { base:ap: 3 }
target: self
effect:
  type: apply_status
  status: base:shield
  target:                                  # ← explicit: the ability targets self, the effect does not
    scope: { of: self, adjacent: orthogonal, include_self: true }
    filter: { friendly: true }
```

`pawn_sprint`, showing a condition and a two-step effect:

```yaml
type: ability
id: base:pawn_sprint
name: Pawn Sprint
owner: { tag_any: [base:pawn] }
cost: { base:ap: 1 }
when: { not_status: [base:stun] }               # ← subject is the owning piece. See finding 4.
target:
  scope: { of: self, offset: [3, 0] }
  filter: { empty: true }
effect:
  - { type: move, target: self, to: $target }
  - { type: transform, target: self, into: base:queen, preserve: [has_moved],
      when: { at_promotion_rank: true } }
```

That last block is **trigger → condition → effect appearing spontaneously inside an ability**, in the
*existing* base game. The shape we committed to for the probes turns out to be needed by content that
shipped years ago. That is independent corroboration, arrived at from the opposite direction.

`$target` names the validated target square. It is not a binding in the `warning.bind` sense — it is
the ability's one implicit parameter, the way `self` is. No author writes it.

---

# Fusion

The explicit ordered-pair table (F10). **Do not derive it from a rule.**

```yaml
type: fusion
id: base:fusion_table
match: { capturer: exact, captured: primary }     # ← see finding 6; do not omit
fuses_on: displacing_captures                     # ← see below; decided after D1
rules:
  - { capturer: base:knight, captured: base:bishop, into: base:archbishop }
  - { capturer: base:bishop, captured: base:knight, into: base:archbishop }
  - { capturer: base:rook,   captured: base:knight, into: base:chancellor }
  - { capturer: base:knight, captured: base:rook,   into: base:chancellor }
  - { capturer: base:rook,   captured: base:bishop, into: base:warden }
  - { capturer: base:bishop, captured: base:rook,   into: base:inquisitor }
```

`capturer` and `captured` are distinct keys, so the asymmetry survives transcription. Any schema
modelling this as an unordered pair silently breaks the game: `(Rook, Bishop)` → Warden but
`(Bishop, Rook)` → Inquisitor.

## `match` — the two sides use different axes

**This is the third appearance of F3's two axes, and it is not optional.** `FusionManager.handle_move`
resolves the two sides differently:

```python
capturing_code = capturing_piece.get_piece_code()                      # exact identity
captured_code  = getattr(captured_piece, "primary_component_code", …)  # primary axis
```

So `captured: base:bishop` means **"is primarily a bishop"** — which includes **Inquisitor**
(Bishop+Rook). A Rook capturing an Inquisitor fuses into a Warden today. Reading `captured` as an
exact ID silently deletes that behaviour, and it is reachable in any game where a fused piece gets
taken.

| Capture | Captured's primary | Lookup | Result |
|---|---|---|---|
| Rook takes Bishop | bishop | `(rook, bishop)` | Warden |
| Rook takes **Inquisitor** | **bishop** | `(rook, bishop)` | **Warden** ✅ |
| Rook takes **Archbishop** | **knight** | `(rook, knight)` | **Chancellor** ✅ |
| Rook takes **Warden** | **rook** | `(rook, rook)` | not in table → nothing |
| Bishop takes **Chancellor** | **rook** | `(bishop, rook)` | **Inquisitor** ✅ |

`match` is declared rather than implied because the asymmetry is invisible otherwise, and because a
modder writing their own fusion-like table needs to be able to choose. The base table's value is
`{ capturer: exact, captured: primary }`.

The principle is "the capturer's movement dominates" — and it is **only half-applied**: knight pairs
collapse to Archbishop regardless of direction, both components full. A derivation rule would have to
special-case knights, which is a table with extra steps.

> ### Finding 1 — fusion eligibility needs no field
>
> `Piece.can_fuse()` (`not self.has_fused`) and `King.can_fuse()` (always `False`) are both
> **redundant under this schema**. Eligibility falls out of table membership:
>
> - King captures a bishop → `(base:king, base:bishop)` is not in the table → no fusion ✅
> - Warden captures a bishop → `(base:warden, base:bishop)` is not in the table → no fusion ✅
> - Pawn, Queen, Archbishop → same ✅
>
> The table is already total. **No `can_fuse` field, in core or in content** — one fewer concept, one
> fewer thing to keep in sync. Logged for E1: two engine predicates become deletable.
>
> ⚠️ **This depends on `match.capturer: exact` and breaks without it.** Were the capturer matched on
> the `primary` axis, a Warden (primary: rook) capturing a bishop would look up `(rook, bishop)` and
> fuse into a second Warden — precisely what `can_fuse()` exists to prevent. The two halves of
> `match` are load-bearing for different reasons: `captured: primary` preserves fusing *with* fused
> pieces, `capturer: exact` prevents fusing *as* one.
>
> This also means base:fusion has **no reason to patch base:chess**, which leaves ADR-002's
> "three patch ops with no base-game consumer" flag exactly where it was. I looked for a consumer
> here and did not find one. Reporting that rather than inventing one.

---

# Board layout

Currently `Board.setup_classic` plus `STANDARD_PIECE_ORDER` in `constants.py`. Promoted to the first
migration wave because UC12 (total conversion) is a stated goal — a fixed 8×8 with a hardcoded back
rank makes shogi impossible regardless of how good the piece schema is.

```yaml
type: board
id: base:standard
size: [8, 8]

sides:
  - { id: base:white, name: White, forward: up,   promotes_at: 0, moves_first: true }
  - { id: base:black, name: Black, forward: down, promotes_at: 7 }

rows:
  - { row: 0, side: base:black, pieces: [base:rook, base:knight, base:bishop, base:queen,
                                         base:king, base:bishop, base:knight, base:rook] }
  - { row: 1, side: base:black, fill: base:pawn }
  - { row: 6, side: base:white, fill: base:pawn }
  - { row: 7, side: base:white, pieces: [base:rook, base:knight, base:bishop, base:queen,
                                         base:king, base:bishop, base:knight, base:rook] }
```

`fill:` places one piece type across the whole row; `pieces:` is positional and must match `size`'s
width. Rows not listed are empty.

## `sides` — where colour stops being a constant

`WHITE = "w"` / `BLACK = "b"` are constants today, and `Pawn.__init__` derives `direction` from
`color`. Both must become data.

| Field | Purpose | Replaces |
|---|---|---|
| `forward` | which way this side's pieces face | `self.direction = -1 if color == WHITE else 1` |
| `promotes_at` | the rank `at_promotion_rank` tests | `promotion_row = 0 if color == WHITE else BOARD_ROWS - 1` |
| `moves_first` | turn order | the assumption that white starts |
| `name` | player-facing side label | deriving a label from an ID suffix |

`forward` is what makes the piece frame work — every `dirs: forward` and every `[forward, right]`
offset resolves through it. `promotes_at` is what makes `at_promotion_rank` a condition rather than a
hardcoded row. Both are currently colour-conditionals inside piece classes, which is precisely the
coupling that blocks UC12.

**Sides live in the board layout rather than in their own file** because they are inseparable from it:
`forward: up` is meaningless without knowing which end of the board is up, and `promotes_at: 0` is a
row index into this specific `size`. Splitting them would create two files that are only ever correct
together.

---

# Game mode

**Game mode.** A mode is a playable configuration: a
board, and the event pools that run on it.

```yaml
type: game_mode
id: base:advanced
name: Advanced
board: base:standard
pools: [base:main_pool]
```

## The question it answers, and why nothing else could

[loader-lifecycle](loader-lifecycle.md) → Open asked *"which board layout does a session use?"* when
several are registered, and marked it as needing an owner in Phase D. It never got one. Writing
[modder-guide](../modder-guide.md) surfaced **the identical question for event pools** — a modder's
event fires only if some pool lists it, and nothing said which pool is live.

**They are one question:** *which of the N registered X is active?* And it has a hard constraint that
kills the obvious answers: **core may never name a mod**, so "the base one" is not available, and a
total conversion (UC12) that replaces `base:chess` must still boot.

**The recursion is what makes this a content type rather than a setting.** Any engine rule for
picking a board needs a rule for picking *that* rule. The recursion has to terminate somewhere, and
the only legitimate terminator is **a player choice** — which already exists, in `menu_screen.py`.
So: modes are registered content, the engine requires ≥1, and the player picks one. The engine still
names no mod; it names a *kind*.

`mode_config.py` is this type's ancestor, which is what earns it under the vocabulary rule — this is
not a new mechanic, it is an existing hardcoded one becoming data.

## What it buys, beyond answering the question

**UC11 stops being a disable chain and becomes data:**

```yaml
# base:chess — no dependency on base:events, so `pools` cannot reference one
type: game_mode
id: base:vanilla
name: Standard Chess
board: base:standard
pools: []                    # ← UC11: vanilla chess, as a menu entry
```

Until now, "disabling `base:events` must yield playable standard chess" was the requirement, and it
required a *mod manager*. With a mode, **standard chess is a menu option in the shipped game**, and
the disable path still works as a second route. The requirement is met twice, one of which a player
can actually reach.

Note where each mode has to live, and that the dependency rules force it:

| Mode | Lives in | Because |
|---|---|---|
| `base:vanilla` | `base:chess` | References only `base:standard`. **No `base:events` dependency** — which is exactly UC11's constraint, now enforced by the ID it doesn't mention |
| `base:advanced` | `base:events` | References `base:main_pool`, so it must live where that ID is visible |

`base:fusion` ships no mode: it adds pieces and a fusion table, and applies to whichever mode is
running. That is D2's boundary holding up under a new content type without adjustment — a decent sign
the split was cut in the right place.

## Fields

| Field | Meaning |
|---|---|
| `board` | the board layout id this mode plays on — required |
| `pools` | event pools to run; `[]` is legal and means "no events" |
| `name` | what the menu shows |

**`pools` is a list because the schema costs nothing by allowing it**, not because base content needs
two. One pool is the base game. If a reviewer wants it narrowed to a single `pool:`, nothing breaks —
but two mods each contributing a pool to one mode is the obvious first thing the ecosystem will want,
and a list is how they do it without patching each other.

> **Stage 9 changes.** [loader-lifecycle](loader-lifecycle.md)'s activation requirement was "at least
> one board layout is registered". It becomes **at least one `game_mode`** — which transitively
> requires a board, since `board:` is required and stage 8 links it. Strictly stronger, still names
> no mod.

---

# Patch

ADR-002 decided *what* patching means. This is the file it lives in — a content type like any other,
so it declares `type` and `id` and goes through the same nine stages.

```yaml
type: patch
id: mymod:queen_tweaks
patches:
  - { target: base:queen, op: set,    path: moves[0].limit, value: 3 }
  - { target: base:queen, op: add,    path: moves, value: { type: leap, offsets: [[1,2]] } }
  - { target: base:pawn,  op: remove, path: moves[1] }
```

Three ops, exactly as decided: `set` · `add` · `remove`. The `id` exists because the universal rule
says every definition has one, and because ADR-002's collision report needs something to name that is
more precise than "some mod".

`path` addresses **author-facing field names**, which is why stage 6 runs before normalization: a
patch setting `limit: 3` must land while `limit` still means squares. See
[the hazard](#-migration-hazard--limit-is-off-by-one).

## `replaces` — the blunt instrument

ADR-002's third mode is definition-level, not field-level, so it is not an op. A content definition
declares it:

```yaml
type: piece
id: mymod:queen           # ← defined in mymod's namespace, as the ID rules require
replaces: base:queen      # ← and substituted for base:queen everywhere
```

**A replacement cannot work by redefining `base:queen`**, because a mod may only define IDs in its
own namespace (mod-package.md) and a duplicate ID is a stage 5 error. `replaces:` is how a total
conversion (UC12) swaps a piece out without claiming someone else's namespace — the two rules only
look like an obstacle until you notice they force the honest spelling, where the file says outright
what it is doing and to whom.

Last-wins, discouraged, and reported when two mods replace the same ID (ADR-002). Patches apply to
whatever survives replacement — both happen at stage 6, replacement first.

---

# Historical design findings

> This section records how the contract was derived. It is rationale, not an additional runtime
> surface; the schemas above define what a mod can use today.

Writing the schemas against the source surfaced five things. Three are transcription hazards for D1;
one is a genuine gap; one is a correction to this spec's own first draft.

**Findings 7 and 8 were added by D1**, which wrote the base game against this spec and found two
places where a verb was derived from the audit's *summary* of an event rather than from the event.
That is the pattern worth carrying forward, and it is why D1 exists.

### Finding 2 — normal promotion needs a player choice (closed)

Phase B sketched promotion from `pawn_sprint`, which auto-promotes to Queen. **Normal promotion does
not.** `Board._resolve_pawn_promotion` takes a `promotion_choice` and accepts Q, R, B, or N.

The interaction is now part of the active content contract. It is not an effect (effects do not ask
questions), not a condition (the condition line forbids it), and not a selector; it is a move-pipeline
choice presented by the runtime.

**Minimum viable form**, above:

```yaml
into: [base:queen, base:rook, base:bishop, base:knight]
choose: mover
```

`into` accepting a list means "offer these; `choose:` says who picks". One value of `choose` —
`mover` — is earned. This is the required concept used by the active content contract and is
covered by runtime tests.
standard chess, and it drags in a UI contract (the engine must be able to *ask*, and the ability
pipeline must be able to suspend). Flagged for C4: the loader lifecycle is not affected, but the
**move pipeline** is, and E1 should expect it.

The alternative — hardcode promotion to Queen — is a rules change to standard chess. Not on the table.

### Finding 3 — the pawn double-step changes meaning

The code gates the double-step on **rank** (`r == BOARD_ROWS - 2` for white), not on `has_moved`. The
schema above uses `has_moved: false`. These are not equivalent, and the difference is reachable:

`mat_quyen_cong_dan` converts a white pawn to black. Under rank semantics, that pawn (now black,
sitting on row 6) can never double-step, because black's start rank is 1. Under `has_moved` semantics,
an unmoved converted pawn **can** double-step southward from row 6.

**Recommendation: take `has_moved: false` and accept the divergence.** Rank-gating hardcodes a board
size and a starting layout into a piece, which is exactly what UC12 forbids — `base:pawn` would stop
working the moment someone changes `size`. `has_moved` is also arguably the correct rule: a pawn that
has never moved getting its first-move double is what the rule *means*; the rank check is an
implementation shortcut that happens to coincide on a standard board.

Logged as a **deliberate behaviour change**, not a silent one. D1 should confirm it.

### Finding 4 — stun does not stop abilities, and only one ability noticed

`pawn_sprint` checks that its own piece is not stunned. **`bishop_snipe` does not** — a stunned bishop
can snipe today. `knight_swap` and `rook_shield` don't check either.

Under status-model.md, `movement: { disable: true }` governs **move generation**, not abilities. So
this schema reproduces current behaviour exactly: `pawn_sprint` carries
`when: { not_status: [base:stun] }` and the other three carry nothing.

This is **F2's pattern in a new place** — an invisible per-consumer inconsistency that nobody decided.
The schema does what it did for shields: makes it visible, in the file, and leaves the decision to a
human. Two coherent answers exist (an `abilities: { disable: true }` status modifier, or explicit
`when` on each ability); base content does not need the modifier, so it is not in this spec.

Added to the audit's bug list. **Do not fix it in C3.**

### Finding 5 — `limit` is off by one

See [the hazard box](#-migration-hazard--limit-is-off-by-one). Mechanical, silent, and it will bite
whoever transcribes `fused.py`.

### Finding 6 — fusion's two sides match on different axes

`FusionManager.handle_move` reads the capturer by **exact identity** and the captured piece by its
**primary component**. So `(rook, bishop) → Warden` also fires when a Rook takes an *Inquisitor*,
because Inquisitor is primarily a bishop.

Neither the audit's fusion table nor Phase B's "the ordered-pair table transcribes directly" records
this. **The first draft of this spec got it wrong**, reading `captured` as an exact ID, which would
have silently removed fusion-with-fused-pieces from the game — a behaviour that fires in any game
where a fused piece is taken.

This is **F3's two axes appearing a third time**, in the one place nobody thought to look for them.
The audit found the axes in event selectors and ability owners; they were in the fusion table all
along. That is a decent argument that `components` earning both axes is not a convenience but a
structural property of this game. See [`match`](#match--the-two-sides-use-different-axes).

### Finding 7 — the message model fitted no event

**Found by D1.** The first draft specified a step-level `message` with the templates `{count}`,
`{piece}`, `{color}`, `{square}`, and gave `my_danh_iran` the message `"{count}x"`. Read against the
source, all four parts of that are wrong:

| First draft | The game |
|---|---|
| `{count}` | **No event uses a count.** `my_danh_iran` emits `x{piece}@{square}` per destroyed piece, joined with `", "` |
| `{color}` | Never used — `format_piece_fan` returns `wN`, `bP`, so colour is already inside `{piece}` |
| One `message` per step | **Two shapes:** per-match-joined, *and* once-per-step (`"(All) R=N"`, however many rooks matched) |
| Step-level `empty_message` | **Event-level** — `mat_quyen_cong_dan` emits `"0x"` only if *both* steps produced nothing |

Rewritten above, and it fits all ten. Two template variables instead of four, which is the
earned-verb rule reaching a corner of the spec nobody thought to apply it to.

The cause is the same as finding 8's: the audit summarised messaging as "compact notation per effect;
`0x` when nothing matched" — accurate, and insufficient. Messaging is also the only part of an event
most players ever see, which is a poor thing to have specified from a one-line summary.

### Finding 8 — `random_zone` could not express its only consumer

**Found by D1**, and the sharpest of the lot. The spec offered exactly one binding verb, earned by
exactly one event, and it did not reproduce that event: the engine constrains the zone origin to
`randint(2, 5)`, so the strike can never touch rows 0, 1, or 7. `{ type: random_zone, size: [2, 2] }`
would have hit the whole board.

Fixed with `origin:` — see [the box](#origin--added-after-d1-and-a-warning-about-how-the-rest-of-this-spec-was-written).
Worth reading even if zones never interest you: a verb written from a description rather than from
source looked complete, was reviewed, passed Gate 3, and was wrong.

---

# Future capabilities

- ~~**Does `credit` trigger fusion?**~~ **Decided after D1** ([above](#destroy)): no — displacement
  does. `base:fusion` declares `fuses_on: displacing_captures`, which preserves today's behaviour and
  keeps `bishop_snipe` from fusing. It is also ADR-002's first plausible base-game patch target.
- ~~**Player choice is a new concept** (finding 2)~~ **Closed by the runtime cutover** — promotion
  uses `choose: mover`, with the UI suspending the move until the player selects a destination piece.
- **`material` may belong in `properties`** ([above](#properties--the-open-bag-d10)) — depends on
  whether scoring is engine or base-game UI.
- **`has_status` has no consumer** ([above](#filter--which-qualify)) — cut it if a reviewer objects.
- **Message templates on abilities?** Events have `message`; abilities emit nothing today. Left
  unspecified rather than guessed.

## Milestone 1 correction: independently loadable base chess

The historical `pawn_sprint` example and finding 4 below describe an earlier state. Strict
reference linking made its hidden dependency visible: `base:stun` belongs to the independently
disableable `base:events` mod. To preserve UC11, shipped `base:chess` no longer names that status.
The current YAML is authoritative; this note prevents the historical discussion being read as a
live content requirement.

# Checklist for Gate 3

Every verb in the audit's capability surface has a home:

| Surface | Home |
|---|---|
| Selectors — all, code, code set, colour, exclude king, exclude shielded, zone, adjacency, LoS, friendly/enemy | `scope` + `filter` ✅ |
| Picks — all, random 1, random 1 per colour | `pick` ✅ |
| Effects — destroy, transform (+policy), change colour, apply status, move, swap, promote, record capture | 6 effects; `promote` → `transform`+`when`; record capture → `credit` ✅ |
| Durations — instant, N turns | status-model.md ✅ |
| Statuses — poison, stun, immobilize, shield | status-model.md (4 → 3) ✅ |
| Messaging — compact notation, `"0x"` | `message` / `message: {each:}` / event-level `empty_message` ✅ *(rewritten by D1 — finding 7)* |
| AP economy — starting, max, accrual | `resource` ✅ *(added by D1; C3 shipped without it)* |
| Fusion asymmetry | ordered-pair table + `match` (two axes again — finding 6) ✅ |
| Two selector axes (F3) | `components` → `tag_any` / `primary` ✅ |
| Pawn, King | opaque verbs registered by `base:chess` ✅ |
| Board size, layout, sides | board layout ✅ |

**Not covered, knowingly:** event triggers (F5, deferred with reasons), player choice (finding 2,
newly found, needs a home).

## What the Gate 3 review changed here

The completeness half of Gate 3 — the table above — survived review unchanged. The **consistency**
half did not. Six defects in this document, all found by reading it against its siblings rather than
against the source, all fixed above:

| Was | Now |
|---|---|
| `status` and `patch` had no `type` value and no place in the type list | Eight content types, listed under [Universal rules](#universal-rules) |
| Effects named their subject four ways (`to:`, `what:`, `a:`/`b:`, an undocumented `target:`) | One `target:`, defaulting to the enclosing selection |
| `type: step` used by the King, absent from the move-type table | Deleted — a king is `slide` with `limit: 1` |
| `on: trigger: moved` used by the Pawn, with no trigger vocabulary | [Shared vocabulary 1](#shared-vocabulary-1--trigger) |
| `when: { self: {…} }` in one ability, bare conditions everywhere else | The subject is always implicit |
| `pick: all` vs `pick: { random: 1 }` — a convention used everywhere, stated nowhere | Stated once under [Universal rules](#universal-rules) |

Worth noticing what these have in common: **every one is an omission rather than a mistake**. Each
verb was earned by real content and each rule was decided correctly — what was missing was the
sentence that said so, and nothing catches an unstated convention except reading the whole spec at
once against itself. That is what the gate is for, and it is why it is a review pass rather than a
formality.
