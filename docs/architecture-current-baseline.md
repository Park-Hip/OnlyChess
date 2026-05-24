# Chess Fusion Current Architecture Baseline

This document describes the **stable classic-plus-events baseline** after Phase 5 of the refactor.  
It is the current verified project structure **before** any Fusion, AP, or advanced-mode implementation begins.

## Core Structure

- `src/game/`
  - Owns the main gameplay state and turn flow.
  - `GameState` is the coordinator for move execution, internal legal-move simulation rollback, capture summaries, scoring access, and event-manager integration.
  - Smaller helpers support focused responsibilities such as castling, capture tracking, scoring, and post-move systems.

- `src/pieces/`
  - Owns piece behavior and metadata.
  - Each piece class defines its own movement rules, sprite key, material value, active-state flag, and small extension hooks such as `can_fuse()` and `is_minor_piece()`.
  - The piece registry creates piece instances from stable piece codes.

- `src/events/`
  - Owns the event lifecycle and orchestration.
  - `ChessEvent` defines the common event contract.
  - `EventManager` handles warning timing, execution timing, and queueing.
  - Concrete events, such as `GiaXangTang`, contain only their own warning, execution, and drawing behavior.

- `src/ui/`
  - Owns rendering and transient input state.
  - The UI package handles board rendering, player panels, promotion menu behavior, sprite loading, click/drag interaction state, and UI-only constants.
  - UI helpers consume public game state and package user intent; they do not enforce chess rules.

## Current Runtime Flow

1. `src.main.main()` initializes Pygame and creates `GameState`.
2. UI input helpers collect selection and drag/click intent.
3. `GameState` validates and executes legal moves.
4. Post-move systems update capture summaries and timed events.
5. UI render helpers draw the board, panels, overlays, and promotion menu.

## Why This Baseline Matters

- It is the first project state where:
  - gameplay coordination is separated from piece behavior
  - event logic is separated from event timing
  - UI logic is separated from the main game loop
- It is the intended handoff point before future work adds Fusion rules, AP, active abilities, or more advanced global events.

## Out of Scope for This Baseline

The following are **not implemented in this baseline**:

- Fusion resolution
- Action Points (AP)
- Active piece abilities
- Advanced event types from `mode.md` beyond the current extracted event system foundation

Future work should start from this baseline rather than mixing new gameplay systems into earlier refactor phases.
