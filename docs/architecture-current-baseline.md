# Chess Fusion Current Architecture Baseline

This document describes the **stable event-complete baseline** after all 10 `mode.md` global events have been implemented.

Fusion, Action Points, and active piece abilities are intentionally outside this checkpoint.

## Core Structure

- `src/game/`
  - Owns the main gameplay state and turn flow.
  - `GameState` coordinates move execution, internal legal-move simulation rollback, capture summaries, scoring access, and event-manager integration.
  - Smaller helpers support focused responsibilities such as castling, capture tracking, scoring, state helpers, and post-move systems.

- `src/pieces/`
  - Owns piece behavior and metadata.
  - Each standard piece class defines its own movement rules, sprite key, material value, active-state flag, and small extension hooks.
  - The piece registry creates standard piece instances from stable piece codes.

- `src/events/`
  - Owns the event lifecycle and orchestration.
  - `ChessEvent` defines the common event contract.
  - `EventManager` handles warning timing, execution timing, active-event cleanup, and event queueing.
  - Concrete events contain their own warning, execution, duration, and drawing behavior.
  - The implemented event pool contains all 10 events from `mode.md`.

- `src/ui/`
  - Owns rendering and transient input state.
  - The UI package handles board rendering, player panels, event overlays, promotion menu behavior, sprite loading, click/drag interaction state, and UI-only constants.
  - UI helpers consume public game state and package user intent; they do not enforce chess rules.

## Current Runtime Flow

1. `src.main.main()` initializes Pygame and creates `GameState`.
2. UI input helpers collect selection and drag/click intent.
3. `GameState` validates and executes legal moves.
4. Post-move systems update capture summaries and advance timed events after completed full turns.
5. UI render helpers draw the board, panels, event overlays, and promotion menu.

## Why This Baseline Matters

- It is the project state where:
  - gameplay coordination is separated from piece behavior
  - event logic is separated from event timing
  - UI logic is separated from the main game loop
  - all planned global events are implemented and covered by tests

## Out of Scope for This Baseline

- Fusion mechanics
- Action Points
- Active piece abilities

Future advanced systems should start from this event-complete baseline and add their own plans before implementation.
