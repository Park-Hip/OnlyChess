# D1 — The base game, written as data

**Status:** complete. The files are in [`mods/`](../../mods/); this is the gap log.
**Method:** every content file hand-written against the Phase C spec, as a modder would, reading the
source for behaviour rather than the audit's summary of it. No loader, no engine, no validation.

**Written:** 34 files — 3 manifests · 10 pieces · 4 abilities · 10 events · 1 event pool · 1 fusion
table (6 pairs) · 3 statuses · 1 board layout · 1 resource.

> **Resolved since first writing.** All eight gaps below are now closed or consciously parked, and
> the spec and the files reflect it. Two needed a human call and got one:
>
> | Gap | Resolution |
> |---|---|
> | 1 `credit` → fusion | **Decided: displacement, not credit.** `fuses_on: displacing_captures` added to `type: fusion`. `base:fusion` is finishable; snipe still doesn't fuse |
> | 2 `random_zone` | `origin: { rows: [2, 5], cols: [0, 6] }` added. Deliberately a rectangle and nothing more |
> | 3 message model | Rewritten: `message:` vs `message: { each: }`, event-level `empty_message`, `{count}`/`{color}` cut as unearned |
> | 4 AP economy | **Decided: a `resource` content type.** `base:ap` is now data — and `cost: { ap: 3 }` was a prime-directive violation, now `cost: { base:ap: 3 }` |
> | 5 `components` vs moves | Parked. C3's claim corrected; no `include:` verb built |
> | 6 `include_self` | Defaults `false` in *every* scope, stated |
> | 7 `duration:` on shield | Optional; supplying one to a non-countdown status is a load error |
> | 8 `{square}` is 8×8 | Parked for E1 — engine-side, no schema change implied |
>
> The gap text below is left as written, because *how* they were found is the part worth keeping.

## The headline

**The spec expresses the base game, with one exception that stops an event from working and one that
stops a mod from being written at all.** Everything else transcribed cleanly, and several things were
better than expected: `components` collapsed two hand-enumerated code lists into one-line selectors,
the four statuses became three data files, and `base:events` turned out to need **no dependency on
`base:fusion`** — not one of the ten events names a fused piece, because the two selector axes reach
them through `components` instead.

The exception worth reading first is **gap 2**: the format's only binding verb cannot express the
only event that needs it.

## Gaps

Ranked by whether they block. The first two are found here for the first time; the rest are either
sharpened versions of known issues or new but small.

### 1 — `base:fusion` cannot be finished, and the schema has no field for the answer

**Blocks: `mods/base-fusion/fusion/rules.yaml`.** Known open (the `credit` → fusion question), but D1
sharpens it into something more specific than "a human must decide": **whichever way the human
decides, there is nowhere to write it.**

`type: fusion` has `match:` and `rules:` and nothing else. The recommendation in content-schemas is
that `base:fusion` declares which captures it fuses on — but the schema has no field for that, so the
recommendation is currently unimplementable as data. It needs something like
`fuses_on: displacing_captures`, and that field has to be designed, not just chosen.

Note the constraint that closes the obvious alternative: `base:chess` owns `bishop_snipe` and cannot
reference `base:fusion` (UC11), so the ability cannot opt out by name. The decision must live in
`base:fusion` regardless of which way it goes.

### 2 — `random_zone` cannot express `my_danh_iran`, its only consumer

**Blocks: `mods/base-events/events/my_danh_iran.yaml`.** New, and the most surprising finding in D1.

The schema offers exactly one binding verb, `random_zone`, earned by exactly one event. Written
against the source, it does not reproduce that event:

```python
def _choose_warning_area(self):
    row = random.randint(2, 5)                  # not 0..6
    col = random.randint(0, BOARD_COLS - 2)
    return (row, col)
```

The origin row is constrained to 2–5, so the 2×2 strike covers rows 2–6 and **can never touch rows 0,
1, or 7**. `{ type: random_zone, size: [2, 2] }` takes a size and nothing else, so it would hit the
whole board — a strike that can delete a king on its back rank on turn 10. That is a different game.

Two things make this worth more than its size. First, **the constraint is asymmetric and looks like a
bug**: black's pawn rank (1) is protected, white's (6) is not. It is live behaviour either way and D1
does not fix it. Second, and more useful: our single binding verb failed its single consumer, which
says the verb was written from the audit's description of the event ("random 2×2 zone") rather than
from the event. Anything else derived the same way is suspect.

The fix is a constrained origin — a region the zone's top-left must fall inside. **Resist making it
expressive.** `random_zone` needs to say "somewhere in this rectangle", not to grow a coordinate
language; the moment a binding takes an expression, the condition line has been crossed from the
other side.

### 3 — The message model does not match any of the ten events

**New.** C3 specifies a step-level `message` with the template vocabulary `{count}`, `{piece}`,
`{color}`, `{square}`, and gives `my_danh_iran` the message `"{count}x"`. Reading the source, all four
parts of that are wrong:

| Spec says | The game does |
|---|---|
| `{count}` | **No event uses a count.** `my_danh_iran` emits `x{piece}@{square}` per destroyed piece, joined with `", "` |
| `{color}` | Never used — `format_piece_fan` already returns `wN`, `bP`, so colour is inside `{piece}` |
| One `message` per step | **Two shapes.** Per-match-joined (`kho_ga`, `my_danh_iran`) *and* once-per-step (`gia_xang_tang`'s `"(All) R=N"`, however many rooks matched) |
| Step-level `empty_message` | **Event-level.** `mat_quyen_cong_dan` emits `"0x"` only if *both* steps produced nothing |

The files use a model that does fit all ten, and it is not much bigger:

- `message: "(All) R=N"` — one fragment for the step, if it matched anything.
- `message: { each: "x{piece}@{square}" }` — one fragment per match.
- The **event** joins every fragment from every step with `", "`, and emits `empty_message` only if
  there are none.

Template vocabulary shrinks to `{piece}` and `{square}`. `{count}` and `{color}` are unearned and
should be cut, per the rule.

This one was easy to get wrong and cheap to catch: messaging is the only part of an event most
players ever see, and it is the part the audit summarised in a single line.

### 4 — The AP economy has no home, and it is the Tuner's use case

**New, and structural.** *(Resolved: `type: resource`. See the note below — the fix turned out to
matter for a bigger reason than tuning.)* `cost: { ap: 3 }` is data. The economy that produces the AP
is not:

| Constant | Value | Where |
|---|---|---|
| `STARTING_AP` | 0 | `constants.py` |
| `MAX_AP` | 5 | `constants.py` |
| `AP_GAIN_MOVE_INTERVAL` | 2 | `constants.py` |
| one ability per turn | — | `Ability.can_use` reads `game_state.ability_used_this_turn` |

None has a content type. **UC1 and UC2 are the two highest-ranked use cases in the project** —
"change an ability's AP cost", "change an event's duration or odds" — and while both are literally
satisfied, the Tuner's *next* question ("give everyone AP twice as fast") is not answerable in data.

The roadmap's C3 brief listed the content types as "piece, event, ability, fusion rule, board layout,
**tuning**". C3 delivered six types and **tuning is not among them** — it was dropped without a note,
and the event pool absorbed the only tuning C3 happened to look at (`EVENT_CYCLE_TURNS` and friends).
The AP constants were never picked up.

**Resolved: a `resource` content type**, `base:ap`, in `base:chess`. And chasing it down turned up
something bigger than the tuning gap that started it:

> `cost: { ap: 3 }` means **the engine knows what AP is**. `ap` is a content identifier sitting as a
> literal key in a core schema — the exact thing `CLAUDE.md`'s prime directive forbids. It read as
> harmless for the same reason every violation of that rule reads as harmless: AP is the only
> resource the base game has, so the name never looked like a name.

Abilities now spend `base:ap` by ID; the engine tracks per-side quantities of registered resources
and knows nothing about what they mean; `mymod:mana` works on day one. `ability_used_this_turn` was
*also* in this gap's first draft and does **not** belong here — `Ability.use` calls
`finish_ability_turn`, so spending an ability is spending your turn. That is the turn lifecycle,
which is core's job.

### 5 — `components` tags a piece; it does not compose its moves

**New, and arguable.** C3 says fused pieces "are literally their components' parts concatenated,
which is why they cost four lines instead of a class". Written out, they are not concatenated by
anything — `archbishop.yaml` and `chancellor.yaml` re-type the knight's eight offsets by hand,
because `components:` is a tag field the selectors read and nothing else.

Consequences: the offsets are duplicated three times across the base mod, and **nothing checks that a
piece's `moves` have anything to do with its `components`**. A Warden declaring `components: [rook,
bishop]` and a knight's moves is valid content.

Both defensible. Fused pieces are *authored* content, and Warden's limited diagonal proves a
component's moves are not always copied wholesale — so a `moves: [{ include: base:knight }]` verb
would need an override story and might not pay for itself. But the claim in C3 should be corrected
either way: the four lines are the *tags*, not the moves.

### 6 — `include_self` is specified for one scope kind and needed by another

**Small, real.** `knight_swap` targets any friendly piece except itself (`target is not piece`). The
file writes `scope: board, filter: { friendly: true }`, which is only correct if a board scope
excludes the acting piece by default. C3 specifies `include_self` only for `of: self` scopes, so the
default for every other scope is unstated. One sentence fixes it; the sentence does not exist.

### 7 — `apply_status` takes a `duration:` that shield cannot use

**Small.** `rook_shield` applies `base:shield`, whose expiry is `after_opponent_turn` — not a
countdown, so there is no number to supply, and the file omits `duration:`. The effect table lists
`duration:` as an `apply_status` field without saying it is optional, and nothing says that a
`duration:` on an `after_opponent_turn` status is meaningless. It should be a load error: it is
exactly the kind of line a modder would copy from `kho_ga_tron_ba_mia` and never see fail.

### 8 — `{square}` hardcodes an 8×8 board

**Small, engine-side.** `format_square` contains `files = "abcdefgh"` and `rank = 8 - row`. Under
UC12 (9×9 shogi) every event message is wrong. Square naming probably belongs to the board layout,
which is the only thing that knows the size. Logged for E1 rather than C3 — no schema change is
implied yet.

## ADR-001's Norway problem, confirmed in our own base mod

Not a gap — a prediction paying out. ADR-001 argued that pinning YAML 1.2 was load-bearing because
our own notation uses `on:` as a key, and that stock PyYAML (YAML 1.1) would silently misparse it.
`pyyaml 6.0.2` is installed in this environment, so that is now testable rather than theoretical:

```
$ python -c "import yaml; print(list(yaml.safe_load(open('mods/base-chess/pieces/pawn.yaml'))))"
['type', 'id', 'name', 'material', 'moves', True]
                                              ^^^^
```

**The pawn's promotion block is gone.** `on:` parsed as the boolean `True`, so `'on' in piece` is
`False` and a loader would find a pawn that never promotes — no error, no warning, just a rule
quietly missing from chess. This is the exact failure mode ADR-001 describes, in the first file
anyone would write, and it is one `import yaml` away at all times.

It also sharpens ADR-001's consequence note from a caution into a requirement: the parse chokepoint
must **reject** stock PyYAML rather than merely avoid it. Nothing else catches this — the file is
valid YAML, it just means something different.

(All 33 files were syntax-checked this way, which is the only automated check available before a
validator exists: 33 parsed, 0 syntax errors. That says nothing about whether they are *correct* —
see "What D1 does not answer".)

## What transcribed cleanly, and what that is worth

Recorded because a gap log reads like a disaster otherwise, and because two of these were the
findings the whole preparation phase was built on.

**The two selector axes paid for themselves three times over.** `gia_xang_tang`'s hand-enumerated
`(Rook, Chancellor, Warden)` became `primary: base:rook`. `kho_ga_tron_ba_mia`'s seven-code list
`(R, N, B, A, C, W, I)` became `tag_any: [base:rook, base:knight, base:bishop]` — and it is *exactly*
that set, verified piece by piece, not an approximation of it. Both lists were principles all along.
And the payoff compounds: because events reach fused pieces through components rather than by ID,
**`base:events` needs no dependency on `base:fusion` at all.** With hand-enumerated code lists, every
event would have had to know the fusion roster.

**The transcription hazards all fired, and all were caught by the spec having written them down.**
Warden's `limit=4` is 3 squares. The pawn's double-step is `has_moved`, diverging deliberately from
the engine's rank check. Fusion's `captured` matches on `primary`, not exact identity. Each is a
silent, one-character mistake, and each was pre-empted by a hazard box rather than by luck.

**Statuses came out better than the schema promised.** Four became three files. `nguoi_chong_bat_luc`
and `viec_nhe_vol_cao` differ by one number, in the application, exactly as C6 predicted — and the
engine's own message already said `[stun]` for the immobilize event, which is as close to a
confession as source code gets.

**F2 is now visible.** `mat_quyen_cong_dan` respecting shields in step 1 and ignoring them in step 2
used to be `include_shielded=False` in one call and `include_shielded=True` in another, forty lines
apart. It is now two adjacent selectors in one file, and the inconsistency is impossible to miss.
That was the promise of the whole refactor and it is the first place it is observably true.

## What D1 does not answer

- **The non-coder test (D3) is untouched.** Everything above is our judgement of our own spec. Nine
  of the ten events fit, but nothing here says a stranger could have written them.
- **No file has been validated**, because there is no validator. Every claim of "this transcribes
  cleanly" is a human reading YAML. The `.lc` spike (Phase E) is still the highest-risk unknown.
- **`base:chess`'s `code/` is not written.** `castle` and `enpassant` are declared in
  `manifest.yaml` (`code: true`) and referenced by the pieces, but Gate 4 forbids implementation
  code, and the verbs are code. The dogfooding claim is therefore **still unproven** — D1 shows the
  data side of it only.
