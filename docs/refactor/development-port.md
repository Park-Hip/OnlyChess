# Porting the `development` branch

**Status:** working plan. **Date:** 2026-07-19.

`origin/development` is the pre-refactor implementation — hardcoded content in `src/events/*.py`,
`src/abilities/*.py`, `src/fusion/`, with its own UI layer. It cannot be merged: its architecture is
the one this refactor removed. Every feature below is re-authored against the mod-driven engine, and
the classification says what that costs.

Two exhaustive inventories of that branch back this list; entries were read from its source rather
than inferred.

## How each row is classified

| Kind | Meaning |
|---|---|
| **DATA** | Expressible as YAML mod content with today's vocabulary. No engine change. |
| **WIDGET** | Needs a new built-in HUD widget type. Core grows one earned widget; mods arrange it in `hud_layout`. |
| **SHELL** | Application chrome — menus, overlays, navigation. Core's own, not mod content. |
| **SETTINGS** | Needs the app-level settings layer (a config file core owns, applied over mod defaults). |
| **ENGINE** | New engine state, action type, or snapshot field. |

`WIDGET` is deliberately not "register arbitrary widgets through `ModApi`". The base game needs a
clock and a captured-pieces row, so those widget types are earned; a general registration API is the
speculative version and would block every visible feature behind machinery no content has asked for.

## Done

| Feature | Kind | Notes |
|---|---|---|
| Dynamic fusion | ENGINE | `compose: union`; components accumulate, moves rebuilt from them |
| Pause overlay (Resume / Restart / Help / Main Menu) | SHELL | Esc backs out innermost-first; overlay swallows board input |
| Controls screen (`H`) | SHELL | Controls only — see the help note below |
| Per-side clock, flag ends the game | ENGINE + WIDGET | Session-level, outside the action log: undo does not refund time |

## Gameplay

| Feature | Kind | Notes |
|---|---|---|
| Pawn Kamikaze ability (3 AP) | DATA | Destroys self plus all non-royal, unshielded pieces in the 8 adjacent squares. Needs `adjacent: all` in the selector vocabulary if not already present |
| One ability per turn per player | ENGINE | `development` gates on `ability_used_this_turn`; confirm whether the current turn lifecycle enforces it |
| Pawn Sprint promoting on arrival | DATA | Dev's sprint auto-promotes to queen when it lands on the back rank |

## Board rendering

| Feature | Kind | Notes |
|---|---|---|
| Last-move highlight | ENGINE + presentation | `EngineState.last_move` exists; `PresentationSnapshot` has no field for it yet |
| Rank/file coordinate labels | SHELL | Core draws them; the board's own geometry, not content |
| Event-warning square overlay | ENGINE + presentation | Dev tints the squares an incoming event will hit. Needs the warning to carry its target squares into the snapshot |
| Shielded-piece outline | DATA | Already expressible: a status declares `presentation: { icon | glyph }` |
| Fused-piece component text (`+N+B`) | WIDGET-ish | Per-piece text overlay; currently "not yet" in the extensibility table |
| Drag-and-drop piece movement | SHELL | Input handling only; no engine or content change |
| Cursor changes over interactive elements | SHELL | |

## HUD

| Feature | Kind | Notes |
|---|---|---|
| Captured-pieces row | WIDGET + ENGINE | Captures are recorded; the snapshot needs to expose them per side |
| Material advantage | WIDGET + ENGINE | Needs piece `material` values summed into the snapshot |
| AP pill per player | WIDGET | Resources already reach the snapshot; this is presentation of existing data |
| Turn counter | WIDGET | `completed_turns` already in state |
| Event countdown ("Next Event in: X") | WIDGET + ENGINE | Pool schedule is in state; snapshot does not expose turns-remaining |
| Move log with algebraic notation | WIDGET + ENGINE | The largest single item. Dev writes its own notation (`e4`, `Nf3`, `O-O`, `e8=Q`) plus an ability notation (`~Ne3<>c2 [-2AP]`). Notation must be derived from content, never a hardcoded piece-letter table |
| Event warning card | WIDGET | |
| Scrollable log | SHELL | Mouse wheel over the panel |

## Application shell

| Feature | Kind | Notes |
|---|---|---|
| Main menu: New Game / Options / Quit | SHELL | Mode selection already covers "new game"; Options is new |
| Options screen | SETTINGS | Clock length (5/10/15) and four colours, cycled through presets |
| Colour-similarity validation | SETTINGS | Dev rejects choices closer than 60 in RGB distance, so pieces stay visible against squares |
| Config persistence | SETTINGS | Dev keeps `config.json` at the project root |
| Save / Load game | ENGINE | See the note below — this is the one item that needs a real decision |
| Quit from the game-over screen | SHELL | |

## Two decisions this plan does not make

**Help content that names content.** Dev's help overlay hardcodes fusion rules and an ability list.
Core cannot ship that text: it names pieces and abilities, and content is a mod's to describe. The
current controls screen covers what core owns. A real reference screen has to be generated from the
registries, or supplied by mods as content. Not yet designed.

**Save/load versus the action log.** Dev serialises `GameState` to `save_game.json`. This engine has
no serialisation format, and its undo is a log of reversible actions rather than a snapshot. Saving
could mean persisting the action log and replaying it, or capturing a state snapshot — and the two
differ in whether a save survives a mod being upgraded underneath it. The inventory also found two
bugs in dev's implementation (it references attributes that do not exist), so there is no working
version to copy. Needs a design pass before any code.

## Order

1. **Settings layer** — unblocks the options screen, colours, and clock configuration.
2. **Snapshot fields** — last move, captures, material, event countdown. Cheap, and unblocks four HUD widgets at once.
3. **HUD widgets** — turn counter, AP pill, captured pieces, material, event countdown.
4. **Board affordances** — coordinates, last-move highlight, event-warning tint, drag-and-drop.
5. **Move log with notation** — largest item; do it once the snapshot carries what it needs.
6. **Save/load** — after the design decision above.
