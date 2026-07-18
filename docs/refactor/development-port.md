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
| Event-warning tint and card | ENGINE + WIDGET | Only squares a warning actually committed to; an event that picks at execution shows a name and no squares |
| Status markers, game-over Quit, scrollable log | DATA + SHELL | Shield, poison and stun were invisible until 2026-07-19 |
| Player settings + options screen | SETTINGS | Clock length and colours; overrides mod palette tokens narrowly |
| Material advantage, turn counter, event countdown | WIDGET | Derived from state, so undo reverses them for free |
| Captured-pieces row | ENGINE + WIDGET | `RecordCapture`; the one presentation datum stored rather than derived |
| Last-move highlight, board coordinates | SHELL | Coordinates count from the board's own size |
| Pawn Kamikaze | DATA | Needed no new verb — two interpreter limits removed instead |
| Move log with notation | ENGINE + WIDGET | Named by content glyphs, not chess letters |
| Drag-and-drop, cursor feedback, fused-piece component text | SHELL | Drag is an addition to click-then-click, not a replacement |

## Still to do

| Feature | Kind | Notes |
|---|---|---|
| Save / Load game | ENGINE | Needs the decision below |
| An in-game content reference | — | Needs the decision below |

Everything else from both inventories is done, including two things that turned out already to be
satisfied: Pawn Sprint promotes on arrival via `when: { at_promotion_rank: true }`, and only one
ability per turn is possible because using one advances the turn.

## Two decisions this plan does not make

**Help content that names content.** `development`'s help overlay hardcodes fusion rules and an
ability list. Core cannot ship that text: it names pieces and abilities, and content is a mod's to
describe. The controls screen covers what core owns. A real reference has to be generated from the
registries — which is possible, every ability declares a name and cost — or supplied by mods as a new
content type. Not yet designed.

**Save/load versus the action log.** `development` serialises `GameState` to `save_game.json`. This
engine has no serialisation format, and its undo is a log of reversible actions rather than a
snapshot. Saving could persist the log and replay it, or capture a state snapshot, and the two differ
in whether a save survives a mod being upgraded underneath it. The inventory also found that dev's
implementation references attributes that do not exist, so there is no working version to copy.
