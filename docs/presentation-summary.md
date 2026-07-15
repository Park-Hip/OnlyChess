# Presentation Summary

## Purpose

Short, presentation-ready talking points for explaining the Chess Fusion architecture, OOP choices, extension points, and honest design limits.

## Short Project Summary

Chess Fusion is a Python/Pygame chess variant built for an Object-Oriented Programming course. It keeps normal chess movement and legality as the base game, then adds capture-triggered fusion, timed board events, Action Points, active abilities, shields, captured-piece summaries, and UI helpers.

The main presentation message is that the project uses basic OOP to keep the code readable and expandable without using heavy frameworks or complex patterns.

## Architecture Summary

- Game: `GameState` coordinates board state, turns, legal moves, move execution, rollback, and post-move systems.
- Pieces: piece classes own movement behavior; standard and fused pieces inherit from `Piece`.
- Events: `EventManager` owns timing, while concrete `ChessEvent` subclasses own event behavior.
- Fusion: `FusionManager` handles capture-triggered fusion using a simple rules table.
- Abilities: concrete `Ability` subclasses own AP-backed target validation and effects.
- UI: `src/ui/` renders state and collects player intent, but does not enforce gameplay rules.

`GameState` is the central coordinator, but behavior is kept in focused classes, helpers, managers, trackers, registries, and subsystem modules.

## OOP Highlights

- Pieces inherit from `Piece`, which gives them a shared movement interface and common helper behavior.
- Events inherit from `ChessEvent`, which gives events a shared lifecycle contract.
- Abilities inherit from `Ability`, which gives active skills common AP, ownership, and turn-completion flow.
- `GameState` uses composition by owning `Board`, `EventManager`, `FusionManager`, `ActionPointTracker`, `CaptureTracker`, `ShieldTracker`, and `TempoBurstState`.
- Registries create pieces, events, and abilities from stable keys without long conditional blocks.
- UI modules read game state and delegate rule decisions to domain, fusion, event, and ability classes.

## Avoiding A God Object

`GameState` is intentionally central, but it is not responsible for every detail.

- Movement rules live in piece classes.
- Event timing lives in `EventManager`.
- Event behavior lives in concrete event classes.
- Fusion decisions and results live in `FusionManager` and `src/fusion/rules.py`.
- Action Point bookkeeping lives in `ActionPointTracker`.
- Captured-piece summaries live in `CaptureTracker`.
- Temporary shield state lives in `ShieldTracker`.
- UI rendering and input helpers live in `src/ui/`.
- `GameState` coordinates these systems and keeps the turn flow consistent.

## Extensibility Message

The project follows Open/Closed in a practical, basic way. Many common features can be added by creating a new class or updating a small registry or rule table instead of rewriting the main game loop.

- New event: add a `ChessEvent` subclass, register it, and add it to the mode event pool if needed.
- New ability: add an `Ability` subclass and register it.
- New fusion pair: update the fusion rule table.
- New fused piece: add a piece class, stable code, registry entry, fusion rule, and tests.
- UI-only change: update `src/ui/` without changing gameplay rules.
- New post-move mechanic: add a focused post-move system and insert it into the ordered system list.

Honest limits: new piece identities may need constants, new persistent systems may need a `GameState` field, new post-move systems need registration, and mechanics that affect both moves and ability turns may require careful changes around `GameState.finish_ability_turn()`.

## Subsystem Highlights

Game domain: owns board state, legal move generation, real move execution, simulated rollback, castling, en passant, promotion, and post-move coordination.

Events: use a simple base class plus registry. The manager controls warning, execution, ticking, and cleanup timing; each event owns its own effect.

Fusion: runs after real captures only. A rule table maps capture pairs to fused pieces (Archbishop, Chancellor, Warden, Inquisitor), while `FusionManager` applies the result.

Abilities: use Action Points. The base ability class handles common checks, and each concrete ability owns its target rules and effect.

UI: handles Pygame rendering, panels, highlights, promotion selection, ability selection, and input state. It packages player intent, then delegates legality to the domain and ability layers.

## Suggested Slide Structure

1. Project Goal: chess variant with fusion, events, AP, and abilities.
2. High-Level Architecture: game, pieces, events, fusion, abilities, UI.
3. GameState As Coordinator: central state owner, not the owner of all behavior.
4. Piece Inheritance: standard and fused pieces extend `Piece`.
5. Event System: `ChessEvent` subclasses plus `EventManager`.
6. Fusion System: capture rules, `FusionManager`, fused pieces (Archbishop, Chancellor, Warden, Inquisitor).
7. Ability System: AP tracker, `Ability` subclasses, registry.
8. UI Boundary: UI displays and collects intent, rules stay outside UI.
9. Avoiding A God Object: trackers, managers, helpers, and post-move systems.
10. Extensibility And Limits: practical Open/Closed design with honest remaining core changes.

## One-Minute Architecture Explanation

Chess Fusion is organized around a central `GameState` object that coordinates the board, turns, legal moves, and subsystem flow. The important point is that `GameState` does not contain every rule. Piece movement is handled by piece subclasses, event timing is handled by `EventManager`, event behavior is handled by event classes, fusion is handled by `FusionManager` and a rules table, Action Points are handled by `ActionPointTracker`, captures by `CaptureTracker`, shields by `ShieldTracker`, and UI behavior by modules in `src/ui`.

This gives the project a basic but clear OOP structure. Inheritance is used where the game naturally has shared contracts, such as pieces, events, and abilities. Composition is used so `GameState` can coordinate focused helpers. Registries keep creation simple and avoid long chains of conditionals. The result is not perfectly closed to modification, but it is practical: many new events, abilities, fusion pairs, and UI changes can be added with small, focused changes instead of editing one large God Object.
