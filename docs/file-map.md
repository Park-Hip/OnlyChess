# File Map

## Purpose

This document helps teammates quickly find the right source files when reading, debugging, or changing Chess Fusion.

## Top-Level Runtime Files

- `run.py`: canonical launch wrapper for the game.
- `main.py`: compatibility wrapper that forwards to `src.main.main()`.
- `src/main.py`: Pygame application loop, move attempt handling, promotion handling, and ability attempt handling.
- `src/constants.py`: shared constants for board size, colors, piece codes, UI dimensions, and rules values.

## `src/game/`

This package owns the core chess-domain engine and turn coordination.

- `board.py`: defines `Board` and `GameState`; owns board setup, move execution, rollback, legal move generation, turn flow, king state, castling state, subsystem composition, and public runtime state used by UI.
- `move.py`: defines `Move`, including move identity and flags such as promotion, en passant, castling, real move status, and fusion result state.
- `rules.py`: contains `run_post_move_systems()`, the ordered side-effect pipeline entry point for real moves.
- `post_move_systems/`: focused classes for capture tracking, fusion, Action Point gain, shield expiry, and event updates.
- `action_points.py`: tracks each player's AP.
- `capture_tracker.py`: records captured-piece summaries.
- `shield_tracker.py`: owns shielded-piece bookkeeping and expiry.
- `castling.py`: owns castling rights and castle move generation helpers.
- `scoring.py`: calculates material advantage.
- `state_helpers.py`: safe board-boundary and board-grid helper functions.
- `mode_config.py`: stores explicit advanced-mode configuration such as the default event pool.

Start here when changing legal move flow, turn flow, board state, castling, en passant, promotion, scoring, or global post-move mechanics.

## `src/pieces/`

This package owns piece behavior and piece creation.

- `base.py`: shared `Piece` state, capture checks, movement helper methods, fusion hooks, sprite keys, and material values.
- `standard.py`: standard chess pieces and their movement rules.
- `fused.py`: fused piece mixin and fused pieces such as `Archbishop` and `Chancellor`.
- `registry.py`: maps stable piece codes to piece classes.
- `__init__.py`: package exports for piece classes and registry helpers.

Start here when changing movement, material values, fusion tags, piece metadata, or adding fused pieces.

## `src/events/`

This package owns special global events.

- `base.py`: `ChessEvent` lifecycle contract.
- `manager.py`: `EventManager` timing, warning, execution, cleanup, active-event list, and queued-event selection.
- `registry.py`: event registration, lookup, construction, and random event-key selection.
- concrete event files: each implements one special event.
- `__init__.py`: imports concrete event modules so decorators register them.

Start here when adding, debugging, or presenting special events.

## `src/fusion/`

This package owns capture-triggered fusion.

- `manager.py`: `FusionManager` decides whether a real capture can fuse and applies fusion results.
- `rules.py`: `FUSION_RESULTS` lookup table for valid capture pairs.
- `__init__.py`: package exports.

Start here when changing fusion eligibility, fusion pairs, or fused-result replacement.

## `src/abilities/`

This package owns active abilities.

- `base.py`: `Ability` contract, AP validation, ability ownership checks, turn consumption flow, and shared enemy-piece helper.
- `registry.py`: ability registration, lookup, available-ability discovery, and public `use_ability()` helper.
- `knight_swap.py`: Knight Swap ability.
- `bishop_snipe.py`: Bishop Snipe ability.
- `rook_shield.py`: Rook Shield ability.
- `pawn_sprint.py`: Pawn Sprint ability.
- `__init__.py`: imports abilities so registration happens.

Start here when adding a new active ability or changing AP-backed ability behavior.

## `src/ui/`

This package owns presentation and transient input state.

- `input_handler.py`: `InputState`, click/drag handling, board-square conversion, promotion state, ability state, and move-attempt readiness.
- `render_board.py`: board, piece, highlight, shield, event-overlay, drag, and endgame rendering.
- `render_panels.py`: player panels, material text, AP text, ability error text, and captured-piece row rendering.
- `message_log.py`: `MessageLog` history plus log side-panel, help-button, and entry-formatting rendering.
- `help_overlay.py`: modal help overlay drawing and close-control resolution.
- `ability_menu.py`: ability menu position, available ability keys, click resolution, and drawing.
- `promotion_menu.py`: promotion menu position, click resolution, and drawing.
- `assets.py`: sprite-key lookup and image loading.
- `ui_constants.py`: UI-only constants.

Start here when changing how something looks or how mouse input is interpreted. Do not put rule enforcement here.

## Test Map

- `tests/game/`: core game state, move, helper, tracker, scoring, and post-move system tests.
- `tests/pieces/`: piece metadata, movement extension hooks, fused pieces, and registry tests.
- `tests/events/`: event contract, manager flow, registry, and concrete event tests.
- `tests/fusion/`: fusion manager, fusion rules, and fused-piece tests.
- `tests/abilities/`: ability registry and concrete ability tests.
- `tests/ui/`: input, menu, asset, board rendering, and panel helper tests.

## Where To Start For Common Changes

- New event: `src/events/base.py`, then `src/events/registry.py`, then a concrete event file.
- New ability: `src/abilities/base.py`, then `src/abilities/registry.py`, then a concrete ability file.
- New fusion pair: `src/fusion/rules.py`.
- New fused piece: `src/pieces/fused.py`, `src/pieces/registry.py`, `src/constants.py`, and `src/fusion/rules.py`.
- New post-move mechanic: `src/game/post_move_systems/base.py`, then a new post-move system file, then `src/game/post_move_systems/__init__.py`.
- UI-only presentation change: `src/ui/` and matching `tests/ui/`.

## Layout Note

`src/game/` is intentionally still mostly flat. The ordered post-move systems are split into a subpackage because they are the current extension seam for global side effects. A deeper package hierarchy is not needed unless the project grows further.
