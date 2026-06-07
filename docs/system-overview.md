# System Overview

## Purpose

This document is the entry point for the Chess Fusion technical documentation set. It explains what exists in the current implementation, how the major packages work together, and where to read next.

## Project Summary

Chess Fusion is a Python/Pygame chess variant for an Object-Oriented Programming course project. It keeps standard chess movement and rule validation as the base game, then adds advanced systems:

- capture-triggered fusion
- special board events
- Action Points
- active piece abilities
- UI helpers for rendering, input, promotion, and ability selection

The current system is the stable advanced-mode baseline. The docs describe the implemented code, not a future redesign.

## High-Level Package Structure

- `src/main.py`: Pygame entry point and application loop.
- `src/constants.py`: shared board, color, piece, UI, and rules constants.
- `src/game/`: board state, chess-domain rules, move execution, scoring, helper trackers, and ordered post-move systems.
- `src/pieces/`: standard and fused chess piece classes plus piece registry.
- `src/events/`: event contract, concrete events, event registry, and event lifecycle manager.
- `src/fusion/`: capture-based fusion rules, fusion manager, and Tempo Burst state.
- `src/abilities/`: active ability contract, concrete abilities, and ability registry.
- `src/ui/`: rendering helpers, input state, menus, sprites, and panel drawing.

## Runtime Flow

1. `src.main.main()` initializes Pygame, creates `GameState`, loads images, and starts the main loop.
2. `src.ui.input_handler.InputState` stores transient click, drag, promotion, and ability-selection state.
3. Input helpers convert mouse actions into either a move attempt or an ability attempt.
4. Standard moves are checked against `GameState.get_valid_moves()`.
5. `GameState.make_move(..., is_real_move=True)` applies the move, updates core chess state, and calls `run_post_move_systems()`.
6. `src.game.rules.run_post_move_systems()` loops through `game_state.post_move_systems`.
7. The default ordered systems handle capture tracking, fusion, Action Point gain, shield expiry, and event updates.
8. Active abilities go through `src.abilities.registry.use_ability()`, then `Ability.use()`, then `GameState.finish_ability_turn()`.
9. UI rendering helpers draw the board, pieces, panels, event overlays, promotion menu, and ability menu from public game state.

## Subsystem Interaction Summary

`GameState` coordinates the game, but subsystem details live elsewhere. Pieces own movement behavior. Events own event-specific behavior while `EventManager` owns event timing. `FusionManager` owns capture-based fusion resolution. Abilities own ability-specific validation and effects. UI modules handle presentation and input state, then delegate rule decisions back to the domain layer.

## Read Next

- `docs/oop-design.md`: OOP responsibilities, inheritance, composition, registries, and extension points.
- `docs/extensibility-and-change-impact.md`: concrete feature-change scenarios and Open/Closed evaluation.
- `docs/file-map.md`: practical source navigation guide.
- `docs/game-domain.md`: core chess engine and move validation.
- `docs/events-system.md`: global special events.
- `docs/fusion-system.md`: capture-triggered fusion.
- `docs/abilities-system.md`: Action Points and active abilities.
- `docs/ui-and-input.md`: UI and input boundaries.
- `docs/presentation-summary.md`: slide-ready talking points.

## Current Design Message

The project is intentionally modular but still basic. It uses simple classes, direct registries, focused helper objects, and an ordered post-move pipeline instead of heavy frameworks or complex patterns. This keeps the architecture explainable for an OOP course while still making new features easier to add.
