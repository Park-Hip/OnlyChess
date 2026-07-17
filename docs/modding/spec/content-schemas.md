# Spec — Content Schemas

**Status:** draft (roadmap C3). Decides D9 (verb vocabulary) and D10 (open piece properties).
**Depends on:** [ADR-001](../adr/001-data-format.md) (YAML 1.2), [ADR-002](../adr/002-conflict-semantics.md)
(addressability), [mod-package.md](mod-package.md) (IDs, load order), [status-model.md](status-model.md)
(statuses — **already specified, not restated here**).
**Derived from:** [`content-audit.md`](../content-audit.md) (what exists),
[`feasibility-study.md`](../feasibility-study.md) (what is expressible).

Content types specified here: **piece**, **event**, **event pool**, **ability**, **fusion**,
**board layout**. Plus the three shared vocabularies they compose from: **selector**, **condition**,
**effect**.

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
```

`type` is what makes folders cosmetic (mod-package.md). The loader reads `type`, never the path.

**Unknown keys are a load error, not a warning.** A typo'd `limt: 3` must not silently mean "no
limit". This is `CLAUDE.md`'s *validate at load* invariant, and it is the single highest-value
validation rule in the spec — it converts the most common non-coder mistake from a mystery into a
message.

**Field names are API.** ADR-002 makes every field a patch target, so renaming one is a MAJOR bump
(mod-package.md). Name them once, carefully.

**Unqualified IDs resolve to the current mod's namespace** (mod-package.md). Inside `base:chess`,
`queen` means `base:queen`.

---

# Shared vocabulary 1 — Selector

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

`include_self: true` adds the origin piece to an `of: self` scope. Earned by `rook_shield`, which
shields the rook *and* its neighbours.

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

# Shared vocabulary 2 — Condition

**Conditions are pure predicates over game state.** No side effects, no loops, no assignment, no
arithmetic beyond comparison. This is the line from `CLAUDE.md`, and it is the whole reason this
format does not become a bad programming language.

The v1 set is tiny because F5 found that **no event needs a condition at all**. Conditions exist only
where pieces and abilities earned them:

| Condition | Meaning | Earned by |
|---|---|---|
| `at_promotion_rank: true` | the piece stands on its side's `promotes_at` rank | pawn promotion, `pawn_sprint` |
| `has_moved: false` | the piece has never moved | pawn double-step |
| `empty: true` | the destination square is vacant | pawn forward moves |
| `not_status: [base:stun]` | *(selector filter, reused as a condition on `self`)* | `pawn_sprint` |

Combinators — `all_of: [...]`, `any_of: [...]`, `not: {...}` — are **shape, not vocabulary**, and are
available from day one. No base content nests conditions, but a format where predicates cannot
compose is one that needs redesigning the moment a modder writes their second rule.

`when:` attaches a condition to a move part, an effect, or an ability.

---

# Shared vocabulary 3 — Effect

An effect changes the game. This is the complete v1 list — the audit's capability surface, minus one.

| Effect | Fields | Earned by |
|---|---|---|
| `destroy` | `credit:` (optional) | 5 events, `bishop_snipe` |
| `transform` | `into:`, `preserve:`, `choose:` | `comeout`, `gia_xang_tang`, `umamusume`, promotion |
| `set_color` | `to:` | `mat_quyen_cong_dan` — the only consumer |
| `apply_status` | `status:`, `duration:` | `kho_ga_tron_ba_mia`, `rook_shield`, 2 more |
| `move` | `what:`, `to:` | `pawn_sprint` |
| `swap` | `a:`, `b:` | `knight_swap` |

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

> **Open — does `credit` trigger fusion?** `bishop_snipe` today calls `record_capture` directly and
> does **not** fuse. Under this schema, `credit: self` is indistinguishable from a capture, so a
> naive fusion hook would make snipe fuse and change the game. Either `credit` means "scoring only"
> (and fusion listens to moves, not credits), or fusion needs its own explicit trigger. **Resolve in
> D1 before writing `base:fusion`.** This is adjacent to the retired D11 but is not the same
> question, and it is live regardless of HP.

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
```

Duration lives on the application, not the status definition — fully specified in
[status-model.md](status-model.md). Not restated here.

## `move` and `swap`

```yaml
- { type: move, what: self, to: $target }
- { type: swap, a: self, b: $target }
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
sprite: base:sprites/warden           # optional; defaults to the piece's own id
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

A piece's moves are the **sum of its parts**. Fused pieces are literally their components' parts
concatenated, which is why they cost four lines instead of a class.

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
  - { type: step, dirs: all, limit: 1 }
  - { type: castle, with: { tag_any: [base:rook] } }   # ← opaque verb
```

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
    zone: { type: random_zone, size: [2, 2] }     # computed once, at warning time
  message: "…"

execute:
  - select:
      scope: { zone: $zone }                       # …read back here
      filter: { not_status: [base:shield] }
      pick: all
    effect: { type: destroy }
    message: "{count}x"
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

Phase B checked whether `tai_xiu`'s random side needed a binding. It does not — `color: random_one`
covers it, because its message never names the chosen side. **Check that a binding is load-bearing
before adding one.** That check is the difference between a data format and a bad language.

## Messaging

Every event emits a compact notation string; `"0x"` is the universal "nothing happened" marker.
Messaging is a real schema dimension, not a detail — it is the only thing most players ever see of an
event.

```yaml
message: "{count}x{piece}"
empty_message: "0x"          # emitted when the selector matched nothing
```

Template vocabulary: `{count}`, `{piece}`, `{color}`, `{square}`. Resolved against the step's own
selection — **not a general expression language**. A message cannot reach into game state; if it
wants something the selection doesn't have, that is a signal the step is wrong, not that templates
need power.

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

The pool is content, not engine. It is currently hardcoded across `mode_config.py` and three
constants (`EVENT_CYCLE_TURNS`, `EVENT_WARNING_OFFSET`, `EVENT_EXECUTE_OFFSET`).

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

**Why a sixth content type rather than per-event scheduling:** the ten events do not each have a
schedule. There is one schedule, and it picks one event at random. Giving each event `every: 10`
would describe a different game — ten events all firing on turn 10.

This also makes the event cycle **tunable data**, which is the Tuner persona's most obvious request
after AP costs.

---

# Ability

Uniform shape, already the cleanest seam in the codebase (`Ability.use`: check → validate → spend →
apply → finish).

```yaml
type: ability
id: base:bishop_snipe
name: Bishop Snipe
owner: { tag_any: [base:bishop] }        # the "contains" axis — a Warden may use rook abilities
cost: { ap: 3 }
target:
  scope: { of: self, ray: diagonal }
  filter: { friendly: false, not_status: [base:shield] }
effect: { type: destroy, target: $target, credit: self }
```

`owner` uses `tag_any` — the **contains** axis. This is the one place the current code gets F3 right
(`_piece_has_ability` reads `get_fusion_tags()`), and the schema keeps it.

`target: self` replaces `requires_target = False`:

```yaml
type: ability
id: base:rook_shield
name: Rook Shield
owner: { tag_any: [base:rook] }
cost: { ap: 3 }
target: self
effect:
  type: apply_status
  status: base:shield
  to:
    scope: { of: self, adjacent: orthogonal, include_self: true }
    filter: { friendly: true }
```

`pawn_sprint`, showing a condition and a two-step effect:

```yaml
type: ability
id: base:pawn_sprint
name: Pawn Sprint
owner: { tag_any: [base:pawn] }
cost: { ap: 1 }
when: { self: { not_status: [base:stun] } }     # ← see finding 4
target:
  scope: { of: self, offset: [3, 0] }
  filter: { empty: true }
effect:
  - { type: move, what: self, to: $target }
  - { type: transform, into: base:queen, preserve: [has_moved], when: { at_promotion_rank: true } }
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
  - { id: base:white, forward: up,   promotes_at: 0, moves_first: true }
  - { id: base:black, forward: down, promotes_at: 7 }

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

`forward` is what makes the piece frame work — every `dirs: forward` and every `[forward, right]`
offset resolves through it. `promotes_at` is what makes `at_promotion_rank` a condition rather than a
hardcoded row. Both are currently colour-conditionals inside piece classes, which is precisely the
coupling that blocks UC12.

**Sides live in the board layout rather than in their own file** because they are inseparable from it:
`forward: up` is meaningless without knowing which end of the board is up, and `promotes_at: 0` is a
row index into this specific `size`. Splitting them would create two files that are only ever correct
together.

---

# What C3 found that the audit and Phase B did not

Writing the schemas against the source surfaced four things. Three are transcription hazards for D1;
one is a genuine gap.

### Finding 2 — normal promotion needs a player choice

Phase B sketched promotion from `pawn_sprint`, which auto-promotes to Queen. **Normal promotion does
not.** `Board._resolve_pawn_promotion` takes a `promotion_choice` and accepts Q, R, B, or N.

Nothing in this spec, the feasibility study, or the status model models a player *choice*. It is not
an effect (effects don't ask questions), not a condition (the condition line forbids it), and not a
selector. It is an interaction.

**Minimum viable form**, above:

```yaml
into: [base:queen, base:rook, base:bishop, base:knight]
choose: mover
```

`into` accepting a list means "offer these; `choose:` says who picks". One value of `choose` —
`mover` — is earned. This is a **new concept the roadmap did not anticipate**, it is required by
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
this schema reproduces current behaviour exactly: `pawn_sprint` carries `when: { self: { not_status:
[base:stun] } }` and the other three carry nothing.

This is **F2's pattern in a new place** — an invisible per-consumer inconsistency that nobody decided.
The schema does what it did for shields: makes it visible, in the file, and leaves the decision to a
human. Two coherent answers exist (an `abilities: { disable: true }` status modifier, or explicit
`when` on each ability); base content does not need the modifier, so it is not in this spec.

Added to the audit's bug list. **Do not fix it in C3.**

### Finding 5 — `limit` is off by one

See [the hazard box](#-migration-hazard--limit-is-off-by-one). Mechanical, silent, and it will bite
whoever transcribes `fused.py`.

---

# Open

- **Does `credit` trigger fusion?** ([above](#destroy)) — must be answered before `base:fusion` is
  written. Not the retired D11; live regardless of HP.
- **Player choice is a new concept** (finding 2) — needs a home in the move pipeline. C4 or E1.
- **`material` may belong in `properties`** ([above](#properties--the-open-bag-d10)) — depends on
  whether scoring is engine or base-game UI.
- **`has_status` has no consumer** ([above](#filter--which-qualify)) — cut it if a reviewer objects.
- **Asset IDs** — `sprite: base:sprites/warden` assumes an asset ID scheme that mod-package.md lists
  as open. Same question, still open.
- **Message templates on abilities?** Events have `message`; abilities emit nothing today. Left
  unspecified rather than guessed.

# Checklist for Gate 3

Every verb in the audit's capability surface has a home:

| Surface | Home |
|---|---|
| Selectors — all, code, code set, colour, exclude king, exclude shielded, zone, adjacency, LoS, friendly/enemy | `scope` + `filter` ✅ |
| Picks — all, random 1, random 1 per colour | `pick` ✅ |
| Effects — destroy, transform (+policy), change colour, apply status, move, swap, promote, record capture | 6 effects; `promote` → `transform`+`when`; record capture → `credit` ✅ |
| Durations — instant, N turns | status-model.md ✅ |
| Statuses — poison, stun, immobilize, shield | status-model.md (4 → 3) ✅ |
| Messaging — compact notation, `"0x"` | `message` / `empty_message` ✅ |
| Fusion asymmetry | ordered-pair table ✅ |
| Two selector axes (F3) | `components` → `tag_any` / `primary` ✅ |
| Pawn, King | opaque verbs registered by `base:chess` ✅ |
| Board size, layout, sides | board layout ✅ |

**Not covered, knowingly:** event triggers (F5, deferred with reasons), player choice (finding 2,
newly found, needs a home).
