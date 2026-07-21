# What changed on `refactor_2`

A record of the 28 commits on `origin/refactor_2` that are not on
`refactor/mod-driven-prep`. Written 2026-07-21 from the branch's own commit messages.

`refactor_2` is a strict superset of `refactor/mod-driven-prep` — nothing diverges, so
merging it is a fast-forward. **110 files, +3814 / −191.** The test suite grew from 222 to
**295 tests, all passing** at the branch head.

The short version: the engine already worked, but the game did not look or behave like one.
This branch ports what `development` had — artwork, sound, HUD, drag-and-drop, save/load,
clocks, settings — and rewrites fusion along the way. Roughly a third of the diff is tests.

---

## 1. The one behaviour change to know about

**Fusion moved from a lookup table to composition** (`f31a448`).

The old `mods/base-fusion/fusion/rules.yaml` named a hand-authored result for six specific
ordered pairs. Only those six could fuse, and capture order changed the outcome — Rook takes
Bishop produced a Warden, Bishop takes Rook produced an Inquisitor.

Now `compose: union` accumulates the captured piece's components and rebuilds the capturer's
moves from everything it contains. Any pair fuses, and order no longer matters.

**What this costs, since a previous decision defended it:** Warden's diagonal was deliberately
capped at 3 squares, and no derived rule can express a cap like that. Under composition a
rook-bishop moves as a full rook *and* a full bishop. **This is a chosen balance change, not an
oversight** — it is recorded as such in the YAML and the commit message.

The four authored fused pieces (Archbishop, Chancellor, Warden, Inquisitor) remain valid,
placeable content. Nothing produces them any more.

Supporting details:
- Identity follows the capturer. `components[0]` stays the original piece, so every selector
  reading `primary` keeps working and the piece still resolves its own sprite and abilities.
- Royalty is not absorbed — expressed as a **property check, not a piece id**, because core
  naming a king would be the special-casing the prime directive forbids.
- `rules` is still supported for a mod that wants authored pairs.
- Move generation drops duplicate destinations for multi-component pieces only (a queen
  absorbing a rook contributes orthogonal slides twice). Single-component generation, which the
  perft oracle measures, is unchanged.

---

## 2. Presentation — why the game now looks like the one on `development`

**Piece artwork, sounds, and backdrop** (`20cf90d`). Base chess declared no sprites at all, so
every piece rendered as a letter. The twenty PNGs had been sitting at the repository root the
whole time, never wired up. `presentation.sprite` names one image per piece and cannot express
one picture per side — the per-side form already existed and was used by the menu preview, so
the board now reads that same convention rather than a second one. Move and capture play the
pre-refactor recordings (converted to ogg; the loader accepts wav and ogg only). The other eight
cues remain placeholders.

**Per-player HUD panels** (`31c433f`). The board sits between two panels — clock, resources,
material lead, captures — with the side panel keeping what belongs to the game rather than a
player. Which player a panel describes comes from the **slot, not a name in the layout**: a
layout naming `base:white` would only work for mods that happen to have a white, so the snapshot
carries seating order and the widget reads that. The layout validator was relaxed from one
widget per type per *layout* to one per type per *slot*, which is what makes a per-seat panel
expressible at all.

**Derived HUD fields** (`cb09e5e`). Material, turn, event countdown, and last move — each
derived from state rather than stored beside it, so they cannot drift and undo reverses them for
free. `material:` was already declared and validated by content but was dropped at normalization
and never reached the engine. A fused piece keeps the capturer's worth rather than the sum of
what it ate, because summing would count each capture twice.

**Move log** (`66e736e`, `823b1d5`, `319c890`). Standard algebraic notation could not be reused:
`Nf3` depends on knowing knights are called N, which is a fact about chess, not about this
engine. A piece's own declared glyph names it, squares are lettered from the board's own size,
and only `x` and `=` survive as conventions — they describe shape rather than chess. Long
algebraic rather than short, since short form needs the position *before* the move and a log is
read afterwards. Castling is recognised **by shape** (two pieces relocating in one move) so a
mod's own two-piece move reads correctly. History derives from the action log, so undo shortens
it for free. Rendered as a table with per-side columns taken from the board's own side names.

**Also:** drag-and-drop alongside click-then-click (`03e5306`), status markers for shield,
poison and stun — previously all three were invisible (`e2abdb9`), captured-piece tray and board
coordinates counted from the board's own dimensions (`3b8bea9`), event warnings that tint only
squares the event has actually committed to (`fe6a700`), a pause overlay and controls screen
(`4f3119c`), and a reference screen **generated from the registries** rather than written, since
hardcoded help text would name content (`51cbaf2`).

---

## 3. New subsystems

**Save/load** (`2cd5c9e`). A save is a state snapshot, not a replay. The project had already
rejected replay for undo because it forces every random effect through an RNG core owns; a
replayed save has the same hole and hides it better — undo fails when you press it, a replayed
save fails hours later having reconstructed a game that never happened. A save records the mod
set *and manifest versions* it was played against and refuses to load against a different one,
naming both sides of the mismatch. The action log is **not** saved, so a loaded game cannot be
undone past the load point — a deliberate trade recorded in the module docstring.

Later fixed to one slot per mode (`bffb351`): a single `save_game.json` meant saving one mode
silently destroyed another's game. Now `saves/<mode>.json`, with unreadable slots skipped rather
than raised so one corrupt file cannot hide the others.

**Settings** (`92d9b32`). The one layer allowed to overrule a mod, kept narrow: preferences may
replace palette tokens a theme already has and supply a clock length, but cannot invent tokens a
theme lacks. `Settings()` with nothing configured is byte-for-byte the old behaviour. Colours
cycle through curated presets rather than a picker, because a fixed list cannot produce an
unreadable board by accident. A corrupt settings file falls back to defaults instead of stopping
startup — deliberately the opposite of the loader's fail-loud rule, since the worst case is a
player seeing default colours.

**Clocks** (`bccc205`). Per-side time limits, charged to whoever is to move. Clocks live on
`EngineSession` rather than `EngineState` — **a deliberate documented exception** to "every state
change is an action": undo reverses the log, so a clock recorded there would refund the time
spent on the move being taken back, making undo a way to buy thinking time. The session never
reads a wall clock (callers pass elapsed seconds), so a time scramble is deterministically
testable.

---

## 4. Bug fixes worth knowing

| Fix | What was wrong |
|---|---|
| `9a3fd22` | Dragging began only when nothing was selected, so the **second** piece you touched could never be dragged. This is why dragging worked intermittently. |
| `823b1d5` | Pawn sprint could never be used — explicit targeting read `board.at(square)` and refused when it found nothing, and sprint's destination is empty by definition. |
| `d444977` | `RecordAbility` read the owner's position *after* actions applied, so an ability that moves its owner was logged at its destination labelled as its origin. |
| `bffb351` | `completed_turns` was declared, saved, restored and drawn — and never incremented. The turn counter read 1 for an entire game. |
| `22e7d21` | The piece-colour setting overrode a palette token used only for glyphs, so once real artwork shipped it changed a colour nothing used. |
| `28cdfb6` | A mode declaring no prompt widget left the board looking frozen during promotion, with nothing on screen explaining why. |

Several of these were **mutation-checked** — the fix was reverted to confirm the new test
actually goes red. `28cdfb6` records that its first test version passed with the fix removed and
had to be rewritten.

---

## 5. Housekeeping

- **Test fixtures moved out of shipped content** (`632f897`, `b5bb1c0`). The walking skeleton and
  the proof mod lived in `mods/`, so they were discovered at startup and offered to players as
  selectable game modes. Both now live under `tests/fixtures/`. Core cannot filter them out at
  discovery, because that would mean naming a mod — the directory is the only place the
  shipped/not-shipped distinction can live. The proof mod was kept rather than deleted: it is the
  check that core holds no chess assumption, and it has caught real defects.
- **Menu leads with Continue** when a save exists (`b5bb1c0`).
- **README documents a plain-venv setup** (`f6b8f18`). The only documented path needed uv and
  PowerShell, which is why the suite had never run on another platform.
- **Preview sign-off gate defined** (`1e68949`, `fbaad60`) — names the audience (contributors and
  modders running from a checkout) and bounds what may be claimed about extensibility, claim by
  claim. Data mods composing content and code mods registering `move_type` verbs are true today
  and gate-enforced; effects, conditions, selectors, triggers, custom HUD widgets and
  presentation effects are **not** yet, and are marked M7+.

---

## Architectural check

I read the `src/` diff against the prohibitions in `CLAUDE.md`. Every match for hardcoded piece
names, `piece_code ==`-style branching, or base-mod special-casing landed in a **comment or
docstring, never in logic**. The places where it could plausibly have gone wrong — fusion's
royalty rule, the reference screen, per-seat HUD panels, the move log's piece names — each took
the property-driven or content-declared route instead, with the reasoning recorded at the site.

**Not verified:** the suite was not run locally while producing this document. The 295-passing
figure is the branch's own claim from commit `22e7d21`.
