# Chess Fusion Current Architecture Baseline

This document describes the **stable advanced-mode baseline** after the event, fusion, Action Points, and active ability implementation phases.

## Core Structure

- `src/game/`
  - Owns the main gameplay state and turn flow.
  - `GameState` coordinates move execution, internal legal-move simulation rollback, capture summaries, scoring access, AP state, fusion state, shield tracking, and event-manager integration.
  - Smaller helpers support focused responsibilities such as castling, capture tracking, scoring, action-point tracking, post-move systems, and mode configuration.

- `src/pieces/`
  - Owns piece behavior and metadata.
  - Each piece class defines its own movement rules, sprite key, material value, active-state flag, and small extension hooks such as `can_fuse()` and `get_fusion_tags()`.
  - The piece registry creates standard and fused piece instances from stable piece codes.
  - `Archbishop` combines Knight/Bishop movement, `Chancellor` combines Rook/Knight movement, and `Warden`/`Inquisitor` combine Rook/Bishop movement with a limited second range.

- `src/fusion/`
  - Owns capture-based fusion rules and resolution.
  - `rules.py` maps valid capture pairs (in both directions) to fused pieces.
  - `FusionManager` applies fusion only after real eligible captures and keeps simulated move generation side-effect free.

- `src/events/`
  - Owns the event lifecycle and orchestration.
  - `ChessEvent` defines the common event contract.
  - `EventManager` handles warning timing, execution timing, active-event cleanup, and queueing.
  - Concrete events contain their own warning, execution, duration, and drawing behavior.

- `src/abilities/`
  - Owns active piece ability behavior.
  - `Ability` defines shared AP validation and turn-consumption flow.
  - The ability registry exposes `KnightSwap`, `BishopSnipe`, `RookShield`, and `PawnSprint`.
  - Ability captures update captured-piece summaries but do not trigger fusion.

- `src/ui/`
  - Owns rendering and transient input state.
  - The UI package handles board rendering, player panels, AP display, promotion menu behavior, ability-menu state, sprite loading, click/drag interaction state, and UI-only constants.
  - UI helpers consume public game state and package user intent; they do not enforce chess rules.

## Current Runtime Flow

1. `src.main.main()` initializes Pygame and creates `GameState`.
2. UI input helpers collect selection, drag/click intent, promotion choices, and ability target intent.
3. `GameState` validates and executes legal moves, while the ability registry validates and executes active abilities.
4. Post-move systems update capture summaries, resolve eligible fusion captures, award AP for real moves, expire shields, and update timed events.
5. Runtime helpers and configuration objects keep subsystem-specific state and default advanced-mode setup out of the main post-move function.
5. UI render helpers draw the board, panels, overlays, ability menu, and promotion menu.

## Why This Baseline Matters

- It is the first project state where:
  - gameplay coordination is separated from piece behavior
  - event logic is separated from event timing
  - fusion rules are separated from move execution
  - active ability behavior is separated from the UI loop
  - UI logic is separated from the main game loop
  - post-move side effects are separated into ordered systems instead of one hardcoded function

## Out of Scope for This Baseline

Future work should start from this baseline rather than mixing new gameplay systems into earlier refactor phases.
