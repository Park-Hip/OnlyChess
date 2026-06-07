# OOP Design

## Purpose

This document explains how Chess Fusion uses Object-Oriented Programming in the current implementation. It is written for a university OOP project presentation, so it focuses on practical design choices that can be shown in the code and explained clearly.

## Design Style

The project uses a basic OOP style:

- classes own related state and behavior
- inheritance is used for pieces, events, and abilities
- composition is used by `GameState` to coordinate helper objects and managers
- direct registries are used for creating pieces, events, and abilities from stable keys
- subsystem-specific behavior is kept outside one giant game class

The design avoids heavy patterns. There is no complex dependency injection container, event bus, or factory hierarchy. The main goal is understandable code that is still easy to extend.

## Core Classes And Responsibilities

`src.game.board.Board` owns the mutable board grid and the classic starting-piece setup. It also provides helper methods for safe board access, mutation, removal, and replacement.

`src.game.board.GameState` coordinates board state, turn flow, legal move generation, move execution, rollback for move validation, king positions, castling state, en passant state, promotion, scoring access, Action Points, fusion, shields, events, and ordered post-move systems.

`src.game.move.Move` represents one move. It stores start and end squares, moved and captured pieces, special-move flags, a deterministic move id, and rollback fields used by internal legal-move simulation.

`src.pieces.base.Piece` defines shared piece state and behavior: color, code, position, active state, movement hooks, capture checks, fusion hooks, sprite keys, and material values.

`src.events.base.ChessEvent` defines the event lifecycle contract: warning, execution, ticking, cleanup, and drawing.

`src.abilities.base.Ability` defines the active ability contract: AP validation, ownership checks, target validation, ability application, and turn consumption.

Managers and helpers keep focused runtime responsibilities out of `GameState`:

- `EventManager` owns event timing, queueing, warning, execution, ticking, and cleanup orchestration.
- `FusionManager` owns capture-triggered fusion resolution after real moves.
- `ActionPointTracker` owns AP values and move counts for each player.
- `CaptureTracker` owns captured-piece summaries for UI and ability captures.
- `ShieldTracker` owns temporary shield state and shield expiry.
- `TempoBurstState` owns the temporary extra-move state granted by Tempo Burst.

## Inheritance

Piece inheritance is the clearest OOP example:

- `Pawn`, `Knight`, `Bishop`, `Rook`, `Queen`, and `King` inherit from `Piece`.
- Each standard piece implements its own `_calculate_moves()` behavior.
- Shared movement helpers such as `_get_sliding_moves()` and `_get_one_step_moves()` live in `Piece`.
- `King` customizes `get_possible_moves()` so castling can be included or skipped during attack checks.
- `Archbishop` and `Chancellor` are fused pieces. `Archbishop` combines bishop and knight movement, while `Chancellor` combines rook and knight movement.

Event inheritance is also direct:

- concrete event classes inherit from `ChessEvent`
- each event can define its own warning, execution, duration, cleanup, ticking, and drawing behavior
- `EventManager` coordinates when events run, while event classes own what each event does

Ability inheritance follows the same simple structure:

- concrete abilities inherit from `Ability`
- each ability defines its key, display name, AP cost, owner piece codes, target validation, and effect
- the shared `Ability.use()` method handles common AP spending and turn consumption

## Composition

`GameState` uses composition by owning focused objects:

- `self.board = Board()`
- `self.capture_tracker = CaptureTracker()`
- `self.action_points = ActionPointTracker()`
- `self.event_manager = EventManager(self)`
- `self.fusion_manager = FusionManager(self)`
- `self.shield_tracker = ShieldTracker()`
- `self.post_move_systems = create_default_post_move_systems(self)`
- `self.tempo_burst_state = TempoBurstState()`

This is easier to explain than a large inheritance hierarchy. `GameState` remains the coordinator, while helper objects own details that would otherwise make it a God Object.

## Registries

The project uses simple registries for extension:

- `src.pieces.registry.PIECE_CLASS_BY_CODE` maps piece codes to piece classes.
- `src.events.registry` maps event keys to event classes.
- `src.abilities.registry` maps ability keys to ability instances.

These registries are intentionally basic. They avoid long conditional blocks in core code without introducing complex factory patterns.

## Separation Of Responsibilities

The current design separates responsibilities like this:

- pieces own movement behavior and piece metadata
- board helpers own board access and mutation safety
- `GameState` owns chess-core coordination and turn state
- post-move system classes own ordered side effects after real moves
- concrete events own event-specific behavior
- `EventManager` owns event timing and event lifecycle orchestration
- `FusionManager` owns fusion resolution
- ability classes own active ability behavior
- UI helpers own rendering and transient input state

This separation makes the codebase easier to discuss and easier to extend. For example, adding a new event should mainly involve adding a new event class and registering it, not changing piece movement or UI input code.

## Encapsulation And Boundaries

Board access usually flows through `Board.get_piece_at()`, `Board.set_piece_at()`, `Board.remove_piece_at()`, and `Board.replace_piece_at()`. These methods keep board access readable and centralize position updates when replacing a piece.

Pieces expose movement through `get_possible_moves()`, while each piece keeps its concrete movement calculation inside `_calculate_moves()`. This gives all pieces a shared public movement entry point while still allowing each subclass to define its own rules.

The UI reads public state and calls public operations. It does not decide whether a chess move is legal. Legal move decisions stay in `GameState.get_valid_moves()`, `GameState.make_move()`, and piece movement code.

Post-move side effects are controlled through `run_post_move_systems()` instead of being scattered across unrelated files. The default ordered systems handle capture tracking, fusion, Action Point gain, shield expiry, and event updates.

## Avoiding A God Object

`GameState` is still the central gameplay coordinator, so it is an important and busy class. The design avoids turning it into a full God Object by moving focused responsibilities out:

- event timing into `EventManager`
- event behavior into concrete event classes
- capture summaries into `CaptureTracker`
- Action Point bookkeeping into `ActionPointTracker`
- shield bookkeeping into `ShieldTracker`
- fusion resolution into `FusionManager`
- Tempo Burst state into `TempoBurstState`
- rendering and input state into `src/ui/`
- post-move side effects into `src/game/post_move_systems/`

The honest presentation message is that `GameState` coordinates many systems, but it no longer contains every subsystem's internal logic.

## Extension Points

The main extension points are:

- new event: create a concrete `ChessEvent` subclass and register it in the event registry
- new ability: create a concrete `Ability` subclass and register it in the ability package
- new fused piece: create a `Piece` subclass or fused-piece class and register it in `src.pieces.registry`
- new fusion pair: add the pair and result in `src.fusion.rules`
- new post-move mechanic: add a new post-move system class and include it in the ordered default systems
- UI-only change: update `src/ui/` helpers without changing domain rules

These extension points support a basic Open/Closed Principle: many new features can be added by creating a new class or adding a registry entry, while core classes need fewer changes.

## Testability

The current test layout supports subsystem-focused testing:

- `tests/pieces/` checks piece metadata, extension hooks, fused pieces, and registry behavior
- `tests/events/` checks event contracts, event manager flow, registry behavior, and concrete events
- `tests/fusion/` checks fusion rules, fusion manager behavior, and Tempo Burst
- `tests/abilities/` checks the ability registry and concrete abilities
- `tests/game/` checks core move behavior, helpers, post-move systems, trackers, and scoring
- `tests/ui/` checks UI helpers without running a full interactive game

This makes the design easier to verify because each subsystem can be tested near its own responsibility.

## Presentation Message

Chess Fusion uses OOP in a practical way. It keeps behavior close to the class that owns it, uses inheritance where the domain naturally has shared contracts, and uses composition to keep the main game state from owning every detail. The result is not a perfect architecture, but it is clear, explainable, and easier to extend than a single large game class.
