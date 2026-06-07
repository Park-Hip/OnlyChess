# Technical Documentation Set Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a focused technical documentation set that explains the current Chess Fusion implementation, its OOP design choices, subsystem boundaries, and real extension costs.

**Architecture:** This is a documentation-only change. The new docs should describe the implemented system using current source files as evidence, keep `README.md` short, and layer the explanation from overview to OOP design, extensibility analysis, subsystem guides, and presentation support.

**Tech Stack:** Markdown documentation for a Python/Pygame OOP project using `unittest` regression tests and the existing `src/` package structure.

---

## Source Context To Use

Read these files before writing the docs in this plan:

- `README.md`
- `docs/architecture-current-baseline.md`
- `docs/open-closed-refactor-report.md`
- `docs/superpowers/specs/2026-05-30-technical-documentation-set-design.md`
- `src/main.py`
- `src/constants.py`
- `src/game/board.py`
- `src/game/rules.py`
- `src/game/post_move_systems/__init__.py`
- `src/game/action_points.py`
- `src/game/capture_tracker.py`
- `src/game/shield_tracker.py`
- `src/game/mode_config.py`
- `src/pieces/base.py`
- `src/pieces/standard.py`
- `src/pieces/fused.py`
- `src/pieces/registry.py`
- `src/events/base.py`
- `src/events/manager.py`
- `src/events/registry.py`
- `src/fusion/manager.py`
- `src/fusion/rules.py`
- `src/fusion/tempo_burst_state.py`
- `src/abilities/base.py`
- `src/abilities/registry.py`
- `src/ui/input_handler.py`
- `src/ui/render_board.py`
- `src/ui/render_panels.py`
- `src/ui/ability_menu.py`
- `src/ui/promotion_menu.py`

Keep the documentation grounded in those files. Planning docs under `docs/*/plans/` may be used as historical context, but they must not become the main explanation.

## File Structure

Create these documentation files:

- `docs/system-overview.md`: main entry point and high-level runtime map.
- `docs/oop-design.md`: teacher-facing explanation of OOP choices and responsibilities.
- `docs/extensibility-and-change-impact.md`: concrete Open/Closed and change-cost analysis.
- `docs/file-map.md`: practical navigation guide for source folders and feature changes.
- `docs/game-domain.md`: core chess engine, move execution, validation, rollback, and post-move boundary.
- `docs/events-system.md`: event contract, registry, manager lifecycle, UI overlays, and event extension.
- `docs/fusion-system.md`: capture-triggered fusion, valid fusion pairs, fused pieces, and Tempo Burst.
- `docs/abilities-system.md`: Action Points, ability base contract, registry, turn flow, and limitations.
- `docs/ui-and-input.md`: rendering/input boundaries and how user actions become domain calls.
- `docs/presentation-summary.md`: short presentation-ready architecture and OOP speaking points.

Modify these existing files:

- `README.md`: add links to the new technical documentation set while keeping the README short.

Do not modify gameplay code.

---

### Task 1: Documentation Entry Point

**Files:**
- Create: `docs/system-overview.md`
- Modify: `README.md`

- [ ] **Step 1: Read the entry-point sources**

Run:

```powershell
Get-Content -LiteralPath README.md
Get-Content -LiteralPath docs/architecture-current-baseline.md
Get-Content -LiteralPath src/main.py
Get-Content -LiteralPath src/game/board.py -TotalCount 140
Get-Content -LiteralPath src/game/rules.py
Get-Content -LiteralPath src/game/post_move_systems/__init__.py
```

Expected: output shows `src.main.main()`, `GameState`, `Board`, and the ordered post-move systems.

- [ ] **Step 2: Create `docs/system-overview.md`**

Write:

```markdown
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
```

- [ ] **Step 3: Update `README.md` with technical docs links**

Add this under the existing `## Architecture Note` section:

```markdown
## Technical Documentation

The focused technical documentation set starts here:

- [docs/system-overview.md](docs/system-overview.md)
- [docs/oop-design.md](docs/oop-design.md)
- [docs/extensibility-and-change-impact.md](docs/extensibility-and-change-impact.md)
- [docs/file-map.md](docs/file-map.md)

Subsystem guides:

- [docs/game-domain.md](docs/game-domain.md)
- [docs/events-system.md](docs/events-system.md)
- [docs/fusion-system.md](docs/fusion-system.md)
- [docs/abilities-system.md](docs/abilities-system.md)
- [docs/ui-and-input.md](docs/ui-and-input.md)

Presentation support:

- [docs/presentation-summary.md](docs/presentation-summary.md)
```

- [ ] **Step 4: Verify entry-point links**

Run:

```powershell
Test-Path docs/system-overview.md
Select-String -Path README.md -Pattern "docs/system-overview.md","docs/oop-design.md","docs/presentation-summary.md"
Select-String -Path docs/system-overview.md -Pattern "Runtime Flow","Read Next","ordered post-move"
```

Expected: all commands return matching paths and lines.

- [ ] **Step 5: Commit**

Run:

```bash
git add README.md docs/system-overview.md
git commit -m "docs: add technical documentation entry point"
```

---

### Task 2: OOP Design Guide

**Files:**
- Create: `docs/oop-design.md`

- [ ] **Step 1: Read OOP source files**

Run:

```powershell
Get-Content -LiteralPath src/game/board.py
Get-Content -LiteralPath src/pieces/base.py
Get-Content -LiteralPath src/pieces/standard.py
Get-Content -LiteralPath src/pieces/fused.py
Get-Content -LiteralPath src/events/base.py
Get-Content -LiteralPath src/abilities/base.py
Get-Content -LiteralPath src/events/registry.py
Get-Content -LiteralPath src/abilities/registry.py
Get-Content -LiteralPath src/pieces/registry.py
```

Expected: output shows `GameState`, `Piece`, standard piece subclasses, `FusedPiece`, `ChessEvent`, `Ability`, and three registries.

- [ ] **Step 2: Create `docs/oop-design.md`**

Write:

```markdown
# OOP Design

## Purpose

This document explains how Chess Fusion uses Object-Oriented Programming in the current implementation. It focuses on practical design choices that the team can explain during a project presentation.

## Design Style

The project uses a basic OOP style:

- classes own related state and behavior
- inheritance is used for pieces, events, and abilities
- composition is used by `GameState` to coordinate helpers and managers
- direct registries are used for creating pieces, events, and abilities from stable keys
- subsystem-specific behavior is kept outside one giant game class

The design avoids heavy patterns. There is no complex dependency injection container, event bus, or factory hierarchy.

## Core Classes And Responsibilities

`src.game.board.Board` owns the mutable board grid and starting-piece placement.

`src.game.board.GameState` coordinates board state, turn flow, legal move generation, move execution, rollback for move validation, capture summaries, scoring access, Action Points, fusion, shields, events, and post-move systems.

`src.game.move.Move` represents a move and stores the state needed by execution and rollback.

`src.pieces.base.Piece` defines shared piece state, movement hooks, capture checks, fusion hooks, sprite keys, and material values.

`src.events.base.ChessEvent` defines the event lifecycle contract: warning, execution, ticking, cleanup, and drawing.

`src.abilities.base.Ability` defines shared AP validation, target validation, application, and turn consumption.

Managers and helpers such as `EventManager`, `FusionManager`, `ActionPointTracker`, `CaptureTracker`, `ShieldTracker`, and `TempoBurstState` keep focused runtime responsibilities out of `GameState`.

## Inheritance

Piece inheritance is the clearest OOP example:

- `Pawn`, `Knight`, `Bishop`, `Rook`, `Queen`, and `King` inherit from `Piece`.
- Each standard piece implements its own `_calculate_moves()` behavior.
- `Archbishop` and `Chancellor` are fused pieces that combine movement from existing piece behavior.

Event inheritance is also direct:

- concrete event classes inherit from `ChessEvent`
- each event keeps its own warning, execution, duration, cleanup, and drawing behavior

Ability inheritance follows the same simple structure:

- concrete abilities inherit from `Ability`
- each ability defines its key, display name, AP cost, owner piece codes, target validation, and effect

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

These registries are intentionally basic. They support extension without requiring complex factory patterns.

## Separation Of Responsibilities

The current design separates responsibilities like this:

- pieces own movement behavior
- board helpers own board access and mutation safety
- `GameState` owns chess-core coordination and turn state
- post-move system classes own ordered side effects after real moves
- events own event-specific behavior
- `EventManager` owns event timing
- `FusionManager` owns fusion resolution
- ability classes own active ability behavior
- UI helpers own rendering and transient input state

This separation makes the codebase easier to discuss and easier to extend.

## Encapsulation And Boundaries

Board access usually flows through `Board.get_piece_at()`, `Board.set_piece_at()`, `Board.remove_piece_at()`, and `Board.replace_piece_at()`.

Pieces expose movement through `get_possible_moves()`, while each piece keeps its concrete movement calculation inside `_calculate_moves()`.

The UI reads public state and calls public operations. It does not decide whether a chess move is legal. Legal move decisions stay in `GameState` and piece movement code.

Post-move side effects are controlled through `run_post_move_systems()` instead of scattered global mutation.

## Avoiding A God Object

`GameState` is still the central gameplay coordinator, so it is an important class. The design avoids turning it into a full God Object by moving focused responsibilities out:

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

- add a new event class and register it in the event registry
- add a new ability class and register it in the ability package
- add a new fused piece class and register it in `src.pieces.registry`
- add a fusion pair in `src.fusion.rules`
- add a post-move mechanic as a new `PostMoveSystem`
- add UI-only changes inside `src/ui/` without changing domain rules

## Testability

The current test layout supports subsystem-focused testing:

- `tests/pieces/` checks piece metadata, extension hooks, fused pieces, and registry behavior
- `tests/events/` checks event contracts, event manager flow, registry behavior, and concrete events
- `tests/fusion/` checks fusion rules, fusion manager behavior, and Tempo Burst
- `tests/abilities/` checks the ability registry and concrete abilities
- `tests/game/` checks core move behavior, helpers, post-move systems, trackers, and scoring
- `tests/ui/` checks UI helpers without running a full interactive game

## Presentation Message

Chess Fusion uses OOP in a practical way. It keeps behavior close to the class that owns it, uses inheritance where the domain naturally has shared contracts, and uses composition to keep the main game state from owning every detail. The result is not a perfect architecture, but it is clear, explainable, and easier to extend than a single large game class.
```

- [ ] **Step 3: Verify OOP terms and concrete class names**

Run:

```powershell
Select-String -Path docs/oop-design.md -Pattern "GameState","Piece","ChessEvent","Ability","composition","registries","God Object"
Select-String -Path docs/oop-design.md -Pattern "ActionPointTracker","CaptureTracker","ShieldTracker","TempoBurstState"
```

Expected: each important class and OOP theme appears at least once.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/oop-design.md
git commit -m "docs: explain oop design"
```

---

### Task 3: Extensibility And Change Impact Analysis

**Files:**
- Create: `docs/extensibility-and-change-impact.md`

- [ ] **Step 1: Read extensibility sources**

Run:

```powershell
Get-Content -LiteralPath docs/open-closed-refactor-report.md
Get-Content -LiteralPath src/game/rules.py
Get-Content -LiteralPath src/game/post_move_systems/base.py
Get-Content -LiteralPath src/game/post_move_systems/__init__.py
Get-Content -LiteralPath src/events/registry.py
Get-Content -LiteralPath src/abilities/registry.py
Get-Content -LiteralPath src/fusion/rules.py
Get-Content -LiteralPath src/pieces/registry.py
Get-Content -LiteralPath src/game/board.py
```

Expected: output shows the ordered post-move pipeline, registries, and `GameState.finish_ability_turn()`.

- [ ] **Step 2: Create `docs/extensibility-and-change-impact.md`**

Write:

```markdown
# Extensibility And Change Impact

## Purpose

This document explains how easy it is to add or change features in the current Chess Fusion architecture. It gives concrete file-level scenarios instead of only claiming that the code is extensible.

## What Counts As Core

In this project, core files are the files that coordinate the main game loop, turn flow, move execution, and global side-effect order:

- `src/main.py`
- `src/game/board.py`
- `src/game/rules.py`
- `src/game/post_move_systems/__init__.py`
- `src/game/move.py`
- `src/constants.py`

Editing one of these files is not always wrong, but repeated edits to them for every new feature would weaken the Open/Closed story.

## Main Extension Seams

The current design has these extension seams:

- event classes under `src/events/`
- event registry in `src/events/registry.py`
- ability classes under `src/abilities/`
- ability registry in `src/abilities/registry.py`
- fusion rules in `src/fusion/rules.py`
- fused piece classes in `src/pieces/fused.py`
- piece registry in `src/pieces/registry.py`
- ordered post-move systems under `src/game/post_move_systems/`
- UI helpers under `src/ui/`

## Ordered Post-Move Systems

`src/game/rules.py` now contains a small loop:

```python
def run_post_move_systems(game_state, move):
    """Run ordered post-move systems that should only happen after real moves."""
    for system in game_state.post_move_systems:
        system.apply(game_state, move)
```

The ordered systems are created in `src/game/post_move_systems/__init__.py`. This reduced change pressure on `run_post_move_systems()` because the pipeline entry point no longer needs to know each side effect's internal logic.

## Scenario 1: Add A New Global Event

Files changed:

- create `src/events/new_event.py`
- modify `src/events/__init__.py` if the package imports concrete events there
- modify `src/game/mode_config.py` if the event should appear in the default advanced event pool
- add `tests/events/test_new_event.py`
- add or update registry tests if needed

Core impact:

- `GameState`: no change expected
- `run_post_move_systems()`: no change expected
- `finish_ability_turn()`: no change expected

Assessment: mostly extension-friendly. The event contract and registry allow a new event to be added without changing move execution.

## Scenario 2: Add A New Active Ability For An Existing Piece Type

Files changed:

- create `src/abilities/new_ability.py`
- modify `src/abilities/__init__.py` so registration happens when the package is imported
- add `tests/abilities/test_new_ability.py`
- update UI tests only if ability-menu display behavior changes

Core impact:

- `GameState`: no change expected if the ability can use `Ability.use()` and `finish_ability_turn()`
- `run_post_move_systems()`: no change expected
- `finish_ability_turn()`: change required only if the ability needs a different completion path from current ability turns

Assessment: extension-friendly for normal abilities. Less flexible for abilities that should trigger the exact same post-move flow as real moves, because ability turns currently complete through `finish_ability_turn()`.

## Scenario 3: Add A New Fusion Pair That Produces An Existing Fused Result

Files changed:

- modify `src/fusion/rules.py`
- add or update `tests/fusion/test_fusion_rules.py`
- add or update `tests/fusion/test_fusion_manager.py` if behavior needs runtime coverage

Core impact:

- `GameState`: no change expected
- `run_post_move_systems()`: no change expected
- `finish_ability_turn()`: no change expected

Assessment: low-impact. This is one of the strongest extension points because pair lookup is isolated in `FUSION_RESULTS`.

## Scenario 4: Add A Brand-New Fused Piece

Files changed:

- modify `src/constants.py` to add a stable piece code
- modify `src/pieces/fused.py` to add the fused piece class
- modify `src/pieces/registry.py` to map the new code to the class
- modify `src/fusion/rules.py` to produce the new code from a capture pair
- add or update `tests/pieces/test_fused_pieces.py`
- add or update `tests/pieces/test_piece_registry.py`
- add or update `tests/fusion/test_fusion_rules.py`
- add or update `tests/fusion/test_fusion_manager.py`

Core impact:

- `GameState`: no change expected
- `run_post_move_systems()`: no change expected
- `finish_ability_turn()`: no change expected
- `src/constants.py`: core constants change required for the new stable piece code

Assessment: moderately extension-friendly. The behavior stays inside pieces and fusion, but adding a new stable code requires a constants and registry edit.

## Scenario 5: Add A New Persistent Gameplay Mechanic Across Turns

Files changed:

- create a focused state helper such as `src/game/new_mechanic_tracker.py` or a subsystem-owned helper
- create `src/game/post_move_systems/new_mechanic.py`
- modify `src/game/post_move_systems/__init__.py` to register the system in the correct order
- modify `GameState.__init__()` only if the mechanic needs persistent state owned by the game coordinator
- add `tests/game/test_new_mechanic_tracker.py`
- add `tests/game/test_post_move_systems.py` coverage for ordering

Core impact:

- `GameState`: may need one new composed helper field
- `run_post_move_systems()`: no change expected
- `finish_ability_turn()`: may need a change if ability turns must trigger the same mechanic

Assessment: improved but not perfect Open/Closed. The ordered pipeline makes the mechanic easier to add, but registration and persistent state can still touch core coordination.

## Scenario 6: Change Only UI Presentation Of An Existing Mechanic

Files changed:

- modify one or more files under `src/ui/`, such as `render_board.py`, `render_panels.py`, `ability_menu.py`, or `promotion_menu.py`
- add or update matching tests under `tests/ui/`

Core impact:

- `GameState`: no change expected
- `run_post_move_systems()`: no change expected
- `finish_ability_turn()`: no change expected

Assessment: low-impact when the change is presentation-only. UI code reads public state and delegates rules back to game logic.

## Scenario 7: Rename Or Clean Up The Ordered Post-Move Pipeline Without Changing Behavior

Files changed:

- modify `src/game/rules.py`
- modify files under `src/game/post_move_systems/`
- update imports in tests and source if names move
- update `tests/game/test_game_rules_pipeline.py`
- update `tests/game/test_post_move_systems.py`
- update docs that mention the old names

Core impact:

- `GameState`: no behavior change expected, but imports may need updating
- `run_post_move_systems()`: likely touched because this is the object being renamed or cleaned
- `finish_ability_turn()`: no change expected

Assessment: this is a core cleanup, not an extension. It should be done carefully with regression tests because it changes the pipeline naming or shape.

## Honest Open/Closed Assessment

The architecture is more open for extension than a single hardcoded `GameState` design:

- events, abilities, pieces, and fusion rules have focused extension points
- post-move side effects are split into ordered systems
- shield and Tempo Burst state moved closer to focused helpers
- UI presentation changes can usually stay inside `src/ui/`

The architecture is not fully closed to modification:

- new post-move systems still need registration
- new stable piece codes still touch `src/constants.py`
- `GameState` is still the main coordinator
- ability turns still use `finish_ability_turn()` instead of the exact real-move post-processing path
- some future cross-cutting mechanics may still need core edits

## Presentation Answer

If a lecturer asks whether the project follows the Open/Closed Principle, the accurate answer is:

The project follows a basic, practical version of Open/Closed. Many new features can be added by creating focused classes and updating simple registries, especially events, abilities, fusion pairs, and UI presentation changes. Some changes still require core edits because `GameState` coordinates the chess engine and turn flow. The important improvement is that new behavior no longer has to be crammed into one giant game class or one hardcoded post-move function.
```

- [ ] **Step 3: Verify all required scenarios are present**

Run:

```powershell
Select-String -Path docs/extensibility-and-change-impact.md -Pattern "Scenario 1","Scenario 2","Scenario 3","Scenario 4","Scenario 5","Scenario 6","Scenario 7"
Select-String -Path docs/extensibility-and-change-impact.md -Pattern "GameState","run_post_move_systems","finish_ability_turn","Open/Closed"
```

Expected: all seven scenarios and all core-impact terms are present.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/extensibility-and-change-impact.md
git commit -m "docs: analyze extensibility and change impact"
```

---

### Task 4: File Map

**Files:**
- Create: `docs/file-map.md`

- [ ] **Step 1: Generate file list for verification**

Run:

```powershell
rg --files src tests | Sort-Object
```

Expected: output includes `src/game/`, `src/pieces/`, `src/events/`, `src/fusion/`, `src/abilities/`, `src/ui/`, and matching test folders.

- [ ] **Step 2: Create `docs/file-map.md`**

Write:

```markdown
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
- `tempo_burst_state.py`: focused state helper for Tempo Burst extra-move behavior.
- `__init__.py`: package exports.

Start here when changing fusion eligibility, fusion pairs, fused-result replacement, or Tempo Burst.

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
- `render_panels.py`: player panels, material text, AP text, Tempo Burst text, ability error text, and captured-piece row rendering.
- `ability_menu.py`: ability menu position, available ability keys, click resolution, and drawing.
- `promotion_menu.py`: promotion menu position, click resolution, and drawing.
- `assets.py`: sprite-key lookup and image loading.
- `ui_constants.py`: UI-only constants.

Start here when changing how something looks or how mouse input is interpreted. Do not put rule enforcement here.

## Test Map

- `tests/game/`: core game state, move, helper, tracker, scoring, and post-move system tests.
- `tests/pieces/`: piece metadata, movement extension hooks, fused pieces, and registry tests.
- `tests/events/`: event contract, manager flow, registry, and concrete event tests.
- `tests/fusion/`: fusion manager, fusion rules, and Tempo Burst tests.
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
```

- [ ] **Step 3: Verify major folders and common-change guide**

Run:

```powershell
Select-String -Path docs/file-map.md -Pattern "src/game/","src/pieces/","src/events/","src/fusion/","src/abilities/","src/ui/"
Select-String -Path docs/file-map.md -Pattern "Where To Start For Common Changes","New event","New ability","New fusion pair","New post-move mechanic"
```

Expected: all major folders and common-change cases are present.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/file-map.md
git commit -m "docs: add source file map"
```

---

### Task 5: Game Domain Guide

**Files:**
- Create: `docs/game-domain.md`

- [ ] **Step 1: Read game-domain sources and tests**

Run:

```powershell
Get-Content -LiteralPath src/game/board.py
Get-Content -LiteralPath src/game/move.py
Get-Content -LiteralPath src/game/castling.py
Get-Content -LiteralPath src/game/rules.py
Get-Content -LiteralPath tests/game/test_move_and_undo.py
Get-Content -LiteralPath tests/game/test_game_rules_pipeline.py
```

Expected: output shows move execution, rollback, legal move generation, castling helpers, and post-move pipeline tests.

- [ ] **Step 2: Create `docs/game-domain.md`**

Write:

```markdown
# Game Domain

## Purpose

This document explains the core chess engine: board state, move execution, legal move validation, rollback, and the boundary between chess-domain rules and advanced systems.

## Responsibility

The game-domain layer owns:

- board setup and board mutation
- current turn state
- legal move generation
- check, checkmate, and stalemate detection
- move execution
- simulation rollback for legal move validation
- castling rights
- en passant
- promotion
- material scoring access
- post-move side-effect coordination

It does not own concrete event behavior, concrete ability behavior, rendering, or input presentation.

## Main Classes And Files

- `src/game/board.py`: `Board` and `GameState`.
- `src/game/move.py`: `Move`.
- `src/game/castling.py`: castling rights and castle move helpers.
- `src/game/rules.py`: ordered post-move system runner.
- `src/game/post_move_systems/`: real-move side-effect handlers.
- `src/game/action_points.py`: AP tracker.
- `src/game/capture_tracker.py`: captured-piece summaries.
- `src/game/shield_tracker.py`: shield runtime state.
- `src/game/scoring.py`: material scoring.
- `src/game/state_helpers.py`: board boundary and grid helpers.

## `Board`

`Board` owns the mutable `grid` and classic starting setup. It also provides helper methods:

- `get_piece_at(row, col)`
- `set_piece_at(row, col, piece)`
- `remove_piece_at(row, col)`
- `replace_piece_at(row, col, piece)`
- `is_inside_board(row, col)`

These helpers keep board access more controlled than direct grid mutation everywhere.

## `GameState`

`GameState` is the main coordinator. It owns:

- `board`
- current turn flag
- move log
- king positions
- checkmate and stalemate flags
- en passant target
- castle rights and castle-rights log
- capture tracker
- Action Point tracker
- event manager
- fusion manager
- shield tracker
- ordered post-move systems
- Tempo Burst state
- ability-turn flag

It coordinates many systems, but focused helpers and managers own subsystem-specific details.

## Move Execution Flow

`GameState.make_move()` applies a move in this order:

1. record previous state onto the `Move`
2. mark whether the move spends Tempo Burst
3. move the piece on the board
4. resolve en passant capture
5. resolve pawn promotion
6. update en passant target
7. move the rook for castling
8. update castling rights
9. finalize the move

Finalization logs the move, flips the turn, updates king position, marks whether it is a real move, and runs post-move systems only for real moves.

## Legal Move Generation

`GameState.get_valid_moves()` starts with pseudo-legal moves from `get_all_possible_moves()`. It temporarily applies each move, checks whether the moving side would be in check, removes illegal moves, and then rolls the move back.

This simulation approach keeps legal move validation based on the same movement code used by real moves.

## Simulation And Rollback

Move simulation uses `make_move()` with the default `is_real_move=False`. That means the board and chess-core state can be temporarily changed, but real-move side effects such as fusion, AP gain, capture summaries, shield expiry, and events do not run.

Rollback is handled by `_rollback_last_move()` and its helper methods. It restores piece positions, en passant state, turn state, castling state, rook position after castle simulation, king position, and checkmate/stalemate flags.

## Castling, En Passant, And Promotion

Castling rights are managed through `src/game/castling.py` and stored in `GameState.current_castle_rights`. Castle move generation is delegated to the king and castling helpers.

En passant uses `GameState.enpassant_possible` to track the target square available on the next turn.

Promotion is resolved inside `GameState._resolve_pawn_promotion()`. Invalid promotion choices default to queen.

## Post-Move Boundary

Real move side effects start at `src/game/rules.py`:

```python
def run_post_move_systems(game_state, move):
    """Run ordered post-move systems that should only happen after real moves."""
    for system in game_state.post_move_systems:
        system.apply(game_state, move)
```

The default order is:

1. capture tracking
2. fusion
3. Action Point gain
4. shield expiry
5. event update

This boundary keeps simulation side-effect safe and makes global real-move effects easier to extend.

## Interactions With Other Subsystems

- Pieces provide pseudo-legal movement.
- Fusion runs after eligible real captures.
- Capture tracking records real captures for UI summaries.
- Action Points increase after real moves and successful ability turns.
- Shields expire through post-move handling and ability-turn handling.
- Event updates happen after completed full turns.
- UI reads public state and calls public game operations.

## OOP Design Notes

The core domain uses composition heavily. `GameState` owns a board, trackers, managers, and ordered systems. Pieces own movement through inheritance. Post-move systems are small classes with a shared `apply(game_state, move)` contract.

## Extension Points

- Add a new post-move side effect through `src/game/post_move_systems/`.
- Add a new tracker object if a mechanic needs persistent state.
- Add new piece movement by implementing or extending piece classes.
- Add UI-only display of domain state in `src/ui/` without changing move rules.

## Change Impact

Move-rule changes are high-impact because they affect legal move generation and rollback. Post-move mechanics are lower-impact because the ordered system pipeline isolates real-move side effects.

## Risks And Limitations

`GameState` is still a central coordinator. Changes to core move execution, rollback, and turn flow require careful tests because many systems depend on the move lifecycle. Ability turns still use `finish_ability_turn()` rather than the exact real-move post-move pipeline.
```

- [ ] **Step 3: Verify domain coverage**

Run:

```powershell
Select-String -Path docs/game-domain.md -Pattern "Board","GameState","Move Execution Flow","Legal Move Generation","Simulation And Rollback","Post-Move Boundary"
Select-String -Path docs/game-domain.md -Pattern "castling","en passant","promotion","Action Point","fusion","events"
```

Expected: all chess-domain topics are present.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/game-domain.md
git commit -m "docs: document game domain flow"
```

---

### Task 6: Events System Guide

**Files:**
- Create: `docs/events-system.md`

- [ ] **Step 1: Read event sources and tests**

Run:

```powershell
Get-Content -LiteralPath src/events/base.py
Get-Content -LiteralPath src/events/manager.py
Get-Content -LiteralPath src/events/registry.py
rg --files src/events tests/events | Sort-Object
Get-Content -LiteralPath tests/events/test_event_manager_flow.py
Get-Content -LiteralPath tests/events/test_event_registry.py
```

Expected: output shows `ChessEvent`, `EventManager`, registry helpers, concrete event files, and tests.

- [ ] **Step 2: Create `docs/events-system.md`**

Write:

```markdown
# Events System

## Purpose

The events system adds timed special board events to Chess Fusion. Events create advanced-mode surprises while keeping event-specific logic out of the core move engine.

## Responsibility

The events subsystem owns:

- event lifecycle contract
- event registration and creation
- event warning timing
- event execution timing
- active-event ticking and cleanup
- event-specific board effects
- event-specific overlay drawing

## Main Classes And Files

- `src/events/base.py`: `ChessEvent` base contract.
- `src/events/manager.py`: `EventManager`.
- `src/events/registry.py`: event registry helpers.
- `src/game/mode_config.py`: default advanced-mode event pool.
- concrete event files under `src/events/`: implemented events.
- `src/ui/render_board.py`: draws active event overlays by calling event draw hooks.

## `ChessEvent` Contract

`ChessEvent` defines:

- `event_key`
- `name`
- `duration`
- `warning_active`
- `trigger_warning()`
- `execute()`
- `cleanup()`
- `tick()`
- `draw(screen, font, width, height, info_panel_height)`

Concrete events override the methods they need.

## Registry-Based Event Creation

`src/events/registry.py` uses a simple dictionary:

- `register_event(event_class)` stores a concrete class by `event_key`
- `get_event_class(event_key)` returns the class
- `create_event(event_key, game_state)` constructs the event
- `get_registered_event_keys()` lists registered keys
- `choose_random_event_key(event_keys)` chooses from the configured pool

This is a basic registry, not a complex factory framework.

## Event Manager Lifecycle

`EventManager` stores:

- `turn_counter`
- `active_events`
- `queued_event`
- `queued_event_key`
- `event_pool`

On update:

1. it reads the completed full-turn count from `GameState`
2. it ticks active events after play has started
3. it triggers a warning when the full-turn count reaches the warning timing
4. it executes the queued event at execution timing
5. it cleans up zero-duration events immediately
6. it queues the next event from the pool

## Timing

The current manager warns before a 10-turn boundary and executes on the 10-turn boundary. The manager relies on `GameState.get_full_turn_count()` and is updated by post-move systems after real moves, plus by `finish_ability_turn()` when an ability completes a full turn.

## Interactions With Board State And UI

Events can read and mutate `GameState` through the game-state reference passed into each event. UI rendering does not implement event rules. It draws event overlays by calling event draw hooks from `draw_event_overlays()`.

## Implemented Events

Concrete events live in `src/events/` and are covered by `tests/events/`. The current files include:

- `comeout.py`
- `gia_xang_tang.py`
- `kho_ga_tron_ba_mia.py`
- `long_toi_tan_nat_khi_nhan_ra_toi_la_gay.py`
- `mat_quyen_cong_dan.py`
- `my_danh_iran.py`
- `nguoi_chong_bat_luc.py`
- `tai_xiu.py`
- `umamusume.py`
- `viec_nhe_vol_cao.py`

Use the event files and matching tests for exact behavior when presenting or debugging a specific event.

## How To Add A New Event Safely

1. Create a new concrete event file under `src/events/`.
2. Inherit from `ChessEvent`.
3. Set a stable `event_key`.
4. Implement warning, execution, ticking, cleanup, or drawing behavior as needed.
5. Register the event using the existing registry pattern used by other event files.
6. Add the event key to `src/game/mode_config.py` if it should be in the default pool.
7. Add tests under `tests/events/`.

## OOP Design Notes

The event subsystem uses inheritance for a shared lifecycle contract and composition through `EventManager`. Concrete events own behavior; the manager owns timing.

## Extension Points

- new event class
- new event key in the default event pool
- event-specific drawing hook
- event-specific cleanup behavior

## Change Impact

Adding a normal event should not require changes to `GameState`, move execution, or `run_post_move_systems()`. Changing global timing rules requires editing `EventManager` and its tests.

## Risks And Limitations

Events can mutate game state through `GameState`, so concrete event code should stay focused and covered by tests. Event behavior should not duplicate core movement validation unless the event specifically changes movement rules.
```

- [ ] **Step 3: Verify events coverage**

Run:

```powershell
Select-String -Path docs/events-system.md -Pattern "ChessEvent","EventManager","registry","warning","execution","cleanup","How To Add A New Event"
Select-String -Path docs/events-system.md -Pattern "comeout.py","tai_xiu.py","umamusume.py"
```

Expected: event contract, manager lifecycle, and implemented event list are present.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/events-system.md
git commit -m "docs: document events system"
```

---

### Task 7: Fusion System Guide

**Files:**
- Create: `docs/fusion-system.md`

- [ ] **Step 1: Read fusion sources and tests**

Run:

```powershell
Get-Content -LiteralPath src/fusion/manager.py
Get-Content -LiteralPath src/fusion/rules.py
Get-Content -LiteralPath src/fusion/tempo_burst_state.py
Get-Content -LiteralPath src/pieces/fused.py
Get-Content -LiteralPath tests/fusion/test_fusion_manager.py
Get-Content -LiteralPath tests/fusion/test_fusion_rules.py
Get-Content -LiteralPath tests/fusion/test_tempo_burst_state.py
```

Expected: output shows fusion eligibility, `FUSION_RESULTS`, fused pieces, and Tempo Burst tests.

- [ ] **Step 2: Create `docs/fusion-system.md`**

Write:

```markdown
# Fusion System

## Purpose

The fusion system is the signature Chess Fusion mechanic. After eligible real captures, the capturing piece can transform into a fused piece or trigger a special fusion effect.

## Responsibility

The fusion subsystem owns:

- checking whether a real capture can attempt fusion
- looking up valid fusion results
- replacing the capturing piece with a fused result
- preventing repeated fusion from the same piece
- starting Tempo Burst
- preserving simulation safety by only running after real moves

## Main Classes And Files

- `src/fusion/manager.py`: `FusionManager`.
- `src/fusion/rules.py`: valid fusion pair lookup.
- `src/fusion/tempo_burst_state.py`: Tempo Burst runtime state.
- `src/pieces/fused.py`: fused piece classes.
- `src/pieces/registry.py`: fused piece creation by code.
- `src/game/post_move_systems/fusion.py`: calls `FusionManager` during real post-move processing.

## When Fusion Can Happen

Fusion is attempted only when:

- the move is marked as a real move
- the move captured a piece
- the game has reached the configured minimum half-turn count
- the capturing piece can still fuse
- the capture pair exists in `FUSION_RESULTS`

Simulated moves do not trigger fusion because `run_post_move_systems()` only runs for real moves.

## Fusion Rules

`src/fusion/rules.py` contains the current lookup:

```python
FUSION_RESULTS = {
    (KNIGHT_CODE, BISHOP_CODE): ARCHBISHOP_CODE,
    (ROOK_CODE, KNIGHT_CODE): CHANCELLOR_CODE,
    (ROOK_CODE, BISHOP_CODE): TEMPO_BURST_KEY,
}
```

`get_fusion_result(capturing_code, captured_code)` returns the configured result or `None`.

## `FusionManager`

`FusionManager.handle_move(move)` checks eligibility, reads the capturing and captured piece codes, looks up the fusion result, and then either:

- starts Tempo Burst, or
- replaces the capturing piece with a fused piece

For fused captures, captured piece code uses `primary_component_code` when available so fusion rules stay stable.

## Fused Pieces

Fused pieces live in `src/pieces/fused.py`.

`FusedPiece` is a mixin that:

- marks the piece as already fused
- stores component codes
- prevents future fusion
- exposes fusion tags for abilities
- reuses an existing sprite key until custom art exists

Implemented fused pieces:

- `Archbishop`: Knight + Bishop, moves as bishop plus knight
- `Chancellor`: Rook + Knight, moves as rook plus knight

## Tempo Burst

Tempo Burst is produced by a rook capturing a bishop according to the current rules. Instead of creating a fused piece, `FusionManager` calls `TempoBurstState.start(rook)`.

`GameState.get_all_possible_moves()` respects pending Tempo Burst by allowing only the Tempo Burst piece to move while the extra move is pending. `GameState.clear_tempo_burst()` clears the state after the extra real move is used.

## Interactions With Other Subsystems

- Capture tracking records the captured piece for summaries.
- Fusion runs after capture tracking in the ordered post-move pipeline.
- Fused pieces provide fusion tags that abilities can use.
- UI panels can display Tempo Burst state through render helpers.
- Events and abilities can interact with the same board state but do not own fusion rules.

## OOP Design Notes

Fusion uses a focused manager for orchestration, a rules table for pair lookup, and piece classes for movement. This keeps fusion behavior out of `GameState.make_move()`.

## Extension Points

- add a pair to `FUSION_RESULTS`
- add a fused piece class in `src/pieces/fused.py`
- register the fused piece in `src/pieces/registry.py`
- add a new special fusion result with focused state if it behaves like Tempo Burst

## Change Impact

Adding a new pair for an existing result is low-impact. Adding a brand-new fused piece requires touching constants, fused piece classes, registry, fusion rules, and tests. Changing fusion timing or eligibility requires editing `FusionManager`.

## Risks And Limitations

Fusion is intentionally limited to real captures. Ability captures update captured-piece summaries but do not trigger fusion. This keeps ability behavior simple, but it is a known difference from standard move captures.
```

- [ ] **Step 3: Verify fusion coverage**

Run:

```powershell
Select-String -Path docs/fusion-system.md -Pattern "FusionManager","FUSION_RESULTS","Archbishop","Chancellor","Tempo Burst","real move"
Select-String -Path docs/fusion-system.md -Pattern "Ability captures","do not trigger fusion"
```

Expected: fusion rules, fused pieces, Tempo Burst, and ability-capture limitation are present.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/fusion-system.md
git commit -m "docs: document fusion system"
```

---

### Task 8: Abilities System Guide

**Files:**
- Create: `docs/abilities-system.md`

- [ ] **Step 1: Read ability and AP sources**

Run:

```powershell
Get-Content -LiteralPath src/game/action_points.py
Get-Content -LiteralPath src/abilities/base.py
Get-Content -LiteralPath src/abilities/registry.py
Get-Content -LiteralPath src/abilities/knight_swap.py
Get-Content -LiteralPath src/abilities/bishop_snipe.py
Get-Content -LiteralPath src/abilities/rook_shield.py
Get-Content -LiteralPath src/abilities/pawn_sprint.py
Get-Content -LiteralPath src/game/board.py
Get-Content -LiteralPath tests/abilities/test_ability_registry.py
```

Expected: output shows AP tracking, `Ability.use()`, registry lookup, concrete abilities, and `finish_ability_turn()`.

- [ ] **Step 2: Create `docs/abilities-system.md`**

Write:

```markdown
# Abilities System

## Purpose

The abilities system lets pieces spend Action Points to perform active abilities. It adds strategic actions without putting every ability rule into `GameState` or the UI.

## Responsibility

The abilities subsystem owns:

- ability registration and lookup
- AP cost checks
- ability ownership checks
- target validation
- ability-specific effects
- public ability execution through `use_ability()`

Action Point storage is owned by the game layer through `ActionPointTracker`.

## Main Classes And Files

- `src/game/action_points.py`: `ActionPointTracker`.
- `src/abilities/base.py`: `Ability` base contract.
- `src/abilities/registry.py`: ability registration and public lookup helpers.
- `src/abilities/knight_swap.py`: Knight Swap.
- `src/abilities/bishop_snipe.py`: Bishop Snipe.
- `src/abilities/rook_shield.py`: Rook Shield.
- `src/abilities/pawn_sprint.py`: Pawn Sprint.
- `src/game/board.py`: `GameState.finish_ability_turn()`.
- `src/ui/ability_menu.py`: ability-menu display and click resolution.

## Action Points

`ActionPointTracker` stores AP by color. It supports checking whether a player can spend AP, spending AP, and gaining AP after moves or successful ability turns.

Standard real moves gain AP through the ordered post-move system. Successful abilities spend AP through `Ability.use()` and then complete the turn through `GameState.finish_ability_turn()`.

## Ability Base Class

`Ability` defines:

- `ability_key`
- `display_name`
- `ap_cost`
- `owner_piece_codes`
- `can_use(game_state, piece)`
- `use(game_state, piece, target_square)`
- `is_valid_target(game_state, piece, target_square)`
- `apply(game_state, piece, target_square)`

`can_use()` checks that a piece exists, an ability was not already used this turn, the player can spend AP, and the piece has the ability through its piece code or fusion tags.

`use()` validates the ability, spends AP, applies the effect, and calls `GameState.finish_ability_turn()`.

## Ability Registry

`src/abilities/registry.py` stores registered ability instances by key. It provides:

- `register_ability(ability_class)`
- `get_ability(ability_key)`
- `get_registered_ability_keys()`
- `get_abilities_for_piece(piece)`
- `use_ability(ability_key, game_state, source_square, target_square)`

The UI uses registry helpers to show available abilities for the selected piece.

## Current Abilities

- `KnightSwap`: active ability for knight-style pieces.
- `BishopSnipe`: active ability for bishop-style pieces.
- `RookShield`: active ability for rook-style pieces; uses shield tracking.
- `PawnSprint`: active ability for pawns.

Fused pieces can inherit ability access through `Piece.get_fusion_tags()` and `FusedPiece.get_fusion_tags()`.

## Ability Turn Flow

1. UI selects an ability and source square.
2. UI selects a target square.
3. `src.main.process_ability_attempt()` calls `use_ability()`.
4. The registry finds the ability and source piece.
5. `Ability.use()` checks AP, ownership, and target validity.
6. The ability spends AP and applies its effect.
7. `GameState.finish_ability_turn()` consumes the turn, grants AP for the completed action, expires shields, and updates events if a full turn just completed.

## Interactions With Move Flow And Capture Summaries

Abilities use a separate completion path from standard moves. Some ability effects can capture or affect pieces and update capture summaries, but ability captures do not currently trigger fusion.

This keeps abilities simple, but it means ability turns are not identical to real move post-processing.

## OOP Design Notes

Abilities use inheritance for a shared active-ability contract and concrete subclasses for specific behavior. The registry keeps UI and main loop code from knowing every ability class directly.

## Extension Points

To add a normal ability:

1. create a new ability class under `src/abilities/`
2. inherit from `Ability`
3. set `ability_key`, `display_name`, `ap_cost`, and `owner_piece_codes`
4. implement `is_valid_target()`
5. implement `apply()`
6. import/register it through the existing ability package pattern
7. add tests under `tests/abilities/`

## Change Impact

New normal abilities stay mostly inside `src/abilities/`. Abilities that need a new kind of turn completion, post-move side effect, or fusion interaction may require changes to `GameState.finish_ability_turn()` or the post-move pipeline.

## Risks And Limitations

The key limitation is that ability turns use `finish_ability_turn()` instead of the exact standard move post-processing path. This is acceptable for the current project, but it should be explained honestly because it affects future abilities that want move-like side effects.
```

- [ ] **Step 3: Verify abilities coverage**

Run:

```powershell
Select-String -Path docs/abilities-system.md -Pattern "ActionPointTracker","Ability","registry","KnightSwap","BishopSnipe","RookShield","PawnSprint"
Select-String -Path docs/abilities-system.md -Pattern "finish_ability_turn","do not currently trigger fusion","separate completion path"
```

Expected: AP lifecycle, current abilities, registry, and current limitation are present.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/abilities-system.md
git commit -m "docs: document abilities system"
```

---

### Task 9: UI And Input Guide

**Files:**
- Create: `docs/ui-and-input.md`

- [ ] **Step 1: Read UI sources and tests**

Run:

```powershell
Get-Content -LiteralPath src/main.py
Get-Content -LiteralPath src/ui/input_handler.py
Get-Content -LiteralPath src/ui/render_board.py
Get-Content -LiteralPath src/ui/render_panels.py
Get-Content -LiteralPath src/ui/ability_menu.py
Get-Content -LiteralPath src/ui/promotion_menu.py
Get-Content -LiteralPath tests/ui/test_input_handler.py
Get-Content -LiteralPath tests/ui/test_ability_menu.py
```

Expected: output shows `InputState`, mouse flow, drawing helpers, ability menu helpers, and promotion menu helpers.

- [ ] **Step 2: Create `docs/ui-and-input.md`**

Write:

```markdown
# UI And Input

## Purpose

This document explains how the Pygame UI is separated from gameplay rules. The UI presents state, collects player intent, and delegates rule decisions to game-domain and ability code.

## Responsibility

The UI layer owns:

- transient click and drag state
- board-square conversion from mouse coordinates
- promotion menu state and click resolution
- ability menu state and click resolution
- board drawing
- piece drawing
- highlights
- shield overlays
- event overlays
- player panels
- captured-piece rows
- AP and Tempo Burst text

The UI layer does not own legal move rules, event rules, fusion rules, or ability effects.

## Main Classes And Files

- `src/main.py`: game loop and high-level wiring between input, game state, abilities, promotion, and rendering.
- `src/ui/input_handler.py`: `InputState` and mouse-state helpers.
- `src/ui/render_board.py`: board, pieces, highlights, shield overlays, event overlays, drag rendering, and endgame text.
- `src/ui/render_panels.py`: info panels, captured pieces, material, AP, Tempo Burst, and ability error text.
- `src/ui/ability_menu.py`: ability menu geometry, available ability keys, click resolution, and drawing.
- `src/ui/promotion_menu.py`: promotion menu geometry, click resolution, and drawing.
- `src/ui/assets.py`: sprite-key and image loading.
- `src/ui/ui_constants.py`: UI-only constants.

## Input Flow

1. Pygame events are read in `src.main.main()`.
2. Mouse down, motion, and mouse up events update `InputState` through `src.ui.input_handler`.
3. `move_attempt_ready(input_state)` tells the main loop when a move attempt exists.
4. `process_move_attempt()` compares the attempted move against `GameState.get_valid_moves()`.
5. Promotion moves open promotion state instead of executing immediately.
6. Valid normal moves call `GameState.make_move(..., is_real_move=True)`.
7. Ability selection uses the ability menu and then calls `process_ability_attempt()`.
8. Ability attempts call `src.abilities.registry.use_ability()`.

## Promotion Menu Behavior

Promotion is detected when a valid move has `is_pawn_promotion`. The UI stores the pending move in `InputState`. A later promotion-menu click resolves a piece choice, then calls `GameState.make_move()` with that choice.

The UI chooses a promotion option. The domain layer still applies the promotion and defaults invalid choices to queen.

## Ability Menu Behavior

The ability menu uses the selected piece and ability registry to show available ability keys. A menu click stores the selected ability and source square in `InputState`. A later target click triggers `use_ability()`.

The menu does not implement ability effects. It only helps the player choose an ability and target.

## Rendering Flow

Each frame, `src.main.main()` calls:

- `draw_game_board()`
- `draw_info_panels()`
- ability error text rendering when needed
- `draw_promotion_menu()` when promotion is pending
- `draw_ability_menu()` when an ability menu is open
- `draw_event_overlays()` for active events
- `draw_endgame_text()` for checkmate or stalemate

Rendering helpers read state and draw it. They do not change gameplay rules.

## Interactions With Other Subsystems

- Game domain provides valid moves, checkmate/stalemate state, captured pieces, material score, AP, and Tempo Burst state.
- Ability registry provides available abilities for a piece and executes selected abilities.
- Events provide draw hooks for event overlays.
- Fusion affects rendered pieces by changing the piece on the board.

## OOP Design Notes

The UI uses focused helper modules rather than a large UI class. `InputState` encapsulates transient interaction state. Rendering functions stay grouped by responsibility: board, panels, ability menu, promotion menu, and assets.

## Extension Points

- change board colors in `render_board.py`
- add new panel text in `render_panels.py`
- adjust ability menu display in `ability_menu.py`
- adjust promotion menu behavior in `promotion_menu.py`
- add input behavior in `input_handler.py`
- add sprite loading behavior in `assets.py`

## Change Impact

UI-only changes usually stay inside `src/ui/` and matching `tests/ui/`. Changes that alter what moves or abilities are legal must be implemented in domain or ability code, not UI rendering code.

## Risks And Limitations

The main loop still wires many pieces together. Keep future UI changes focused in helper modules so `src/main.py` remains orchestration code rather than a place for new rules.
```

- [ ] **Step 3: Verify UI boundary language**

Run:

```powershell
Select-String -Path docs/ui-and-input.md -Pattern "InputState","process_move_attempt","process_ability_attempt","promotion","ability menu","Rendering Flow"
Select-String -Path docs/ui-and-input.md -Pattern "does not own legal move rules","must be implemented in domain or ability code"
```

Expected: UI flow and rule-boundary warnings are present.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/ui-and-input.md
git commit -m "docs: document ui and input boundaries"
```

---

### Task 10: Presentation Summary

**Files:**
- Create: `docs/presentation-summary.md`

- [ ] **Step 1: Read all new docs**

Run:

```powershell
Get-Content -LiteralPath docs/system-overview.md
Get-Content -LiteralPath docs/oop-design.md
Get-Content -LiteralPath docs/extensibility-and-change-impact.md
Get-Content -LiteralPath docs/file-map.md
Get-Content -LiteralPath docs/game-domain.md
Get-Content -LiteralPath docs/events-system.md
Get-Content -LiteralPath docs/fusion-system.md
Get-Content -LiteralPath docs/abilities-system.md
Get-Content -LiteralPath docs/ui-and-input.md
```

Expected: all documentation created by prior tasks is available.

- [ ] **Step 2: Create `docs/presentation-summary.md`**

Write:

```markdown
# Presentation Summary

## Purpose

This document gives the team short, presentation-ready talking points for explaining Chess Fusion's architecture and OOP design.

## Short Project Summary

Chess Fusion is a Python/Pygame chess variant. It keeps standard chess as the base, then adds capture-triggered fusion, special board events, Action Points, and active piece abilities.

## Architecture Summary

The system is split into focused packages:

- `src/game/`: core board state, turn flow, move execution, legal move validation, and post-move coordination
- `src/pieces/`: piece behavior and piece creation
- `src/events/`: timed special events
- `src/fusion/`: capture-triggered fusion
- `src/abilities/`: AP-backed active abilities
- `src/ui/`: rendering and input state

`GameState` coordinates the game, but subsystem behavior is kept in focused classes and helper modules.

## OOP Highlights

Use these points in the presentation:

- Pieces use inheritance from `Piece`; each piece owns its movement behavior.
- Events use inheritance from `ChessEvent`; each event owns its warning, execution, cleanup, and drawing behavior.
- Abilities use inheritance from `Ability`; each ability owns target validation and effect logic.
- `GameState` uses composition by owning `Board`, trackers, managers, `TempoBurstState`, and ordered post-move systems.
- Registries create pieces, events, and abilities from stable keys without complex factories.
- UI helpers render state and collect input but do not enforce chess rules.

## Avoiding A God Object

The project avoids putting everything into one giant `Game` class:

- movement stays in piece classes
- event timing stays in `EventManager`
- event behavior stays in event classes
- fusion stays in `FusionManager` and fusion rules
- AP state stays in `ActionPointTracker`
- capture summaries stay in `CaptureTracker`
- shields stay in `ShieldTracker`
- UI rendering and input stay in `src/ui/`

`GameState` is still central, but it acts as a coordinator instead of owning every detail.

## Extensibility Message

The strongest extension examples are:

- add a new event by creating an event class and registering it
- add a new ability by creating an ability class and registering it
- add a new fusion pair by updating `FUSION_RESULTS`
- add a UI-only change inside `src/ui/`
- add a new post-move mechanic through a focused post-move system

The honest limitation is that some changes still touch core files such as `GameState`, `src/constants.py`, or post-move system registration. The project follows a practical basic Open/Closed approach, not perfect zero-modification extension.

## Subsystem Highlights

Game domain:

- `GameState.make_move()` applies chess moves.
- `GameState.get_valid_moves()` simulates moves and rolls them back to avoid illegal self-check.
- Real moves trigger ordered post-move side effects.

Events:

- `EventManager` owns timing.
- Concrete events own behavior.
- UI overlays use event draw hooks.

Fusion:

- Fusion runs only after eligible real captures.
- `Archbishop` combines bishop and knight movement.
- `Chancellor` combines rook and knight movement.
- Tempo Burst grants one extra move for a specific fusion result.

Abilities:

- AP controls active ability usage.
- Ability classes own validation and effects.
- Ability turns currently use a separate completion path from standard moves.

UI:

- Input helpers turn mouse actions into move or ability attempts.
- Rendering helpers draw state.
- Rule decisions remain in domain and ability code.

## Suggested Slide Structure

1. Project idea: standard chess plus fusion, events, AP, and abilities.
2. Package architecture: show `game`, `pieces`, `events`, `fusion`, `abilities`, and `ui`.
3. Main runtime flow: input, valid move, `make_move()`, post-move systems, rendering.
4. OOP design: inheritance, composition, registries, and responsibility separation.
5. Fusion mechanic: capture pair, fused piece, Tempo Burst.
6. Events and abilities: manager/registry approach.
7. Extensibility: concrete examples of adding events, abilities, fusion pairs, and UI changes.
8. Honest limitations: `GameState` remains central and some cross-cutting features still require core edits.
9. Testing: subsystem tests for game, pieces, events, fusion, abilities, and UI.
10. Final message: simple, explainable OOP architecture that supports extension without overengineering.

## One-Minute Architecture Explanation

Chess Fusion separates the game into clear packages. `GameState` coordinates the chess engine and turn flow, while pieces, events, fusion, abilities, and UI each have focused responsibilities. Pieces own movement through inheritance. Events and abilities share base contracts and are created through simple registries. Real move side effects run through an ordered post-move pipeline, which makes new mechanics easier to add without growing one hardcoded function. The design is intentionally basic for an OOP course: it improves extensibility and avoids a God Object without using heavy architecture patterns.
```

- [ ] **Step 3: Verify presentation coverage**

Run:

```powershell
Select-String -Path docs/presentation-summary.md -Pattern "Suggested Slide Structure","One-Minute Architecture Explanation","OOP Highlights","Extensibility Message"
Select-String -Path docs/presentation-summary.md -Pattern "God Object","Open/Closed","GameState","registries"
```

Expected: presentation-ready sections and key OOP claims are present.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/presentation-summary.md
git commit -m "docs: add presentation summary"
```

---

### Task 11: Full Documentation Verification

**Files:**
- Verify: all documentation created in Tasks 1-10

- [ ] **Step 1: Confirm all deliverables exist**

Run:

```powershell
$required = @(
  "docs/system-overview.md",
  "docs/oop-design.md",
  "docs/extensibility-and-change-impact.md",
  "docs/file-map.md",
  "docs/game-domain.md",
  "docs/events-system.md",
  "docs/fusion-system.md",
  "docs/abilities-system.md",
  "docs/ui-and-input.md",
  "docs/presentation-summary.md"
)
$required | ForEach-Object { if (-not (Test-Path $_)) { throw "Missing $_" } else { "OK $_" } }
```

Expected: ten `OK` lines and no thrown error.

- [ ] **Step 2: Check required cross-cutting themes**

Run:

```powershell
Select-String -Path docs/*.md -Pattern "GameState","Piece","ChessEvent","Ability","FusionManager","EventManager","ActionPointTracker"
Select-String -Path docs/*.md -Pattern "extension","Open/Closed","God Object","registr"
Select-String -Path docs/*.md -Pattern "src/game/","src/pieces/","src/events/","src/fusion/","src/abilities/","src/ui/"
```

Expected: matches appear across the new docs.

- [ ] **Step 3: Run the regression suite to prove no behavior changed**

Run:

```bash
uv run python -m unittest discover -s tests/fusion -p "test_*.py" -v
uv run python -m unittest discover -s tests/abilities -p "test_*.py" -v
uv run python -m unittest discover -s tests/pieces -p "test_*.py" -v
uv run python -m unittest discover -s tests/game -p "test_*.py" -v
uv run python -m unittest discover -s tests/events -p "test_*event*.py" -v
uv run python -m unittest discover -s tests/ui -p "test_*.py" -v
```

Expected: all discovered tests pass.

- [ ] **Step 4: Run the smoke test**

Run:

```bash
uv run python -c "import os; os.environ['SDL_VIDEODRIVER']='dummy'; import pygame as p; p.init(); p.event.post(p.event.Event(p.QUIT)); import run; run.main(); print('smoke-ok')"
```

Expected: command exits successfully and prints `smoke-ok`.

- [ ] **Step 5: Final commit if verification caused documentation fixes**

Run only if verification required edits after Task 10:

```bash
git add README.md docs/system-overview.md docs/oop-design.md docs/extensibility-and-change-impact.md docs/file-map.md docs/game-domain.md docs/events-system.md docs/fusion-system.md docs/abilities-system.md docs/ui-and-input.md docs/presentation-summary.md
git commit -m "docs: verify technical documentation set"
```

---

## Self-Review

Spec coverage:

- Entry point: Task 1 creates `docs/system-overview.md`.
- OOP-focused explanation: Task 2 creates `docs/oop-design.md`.
- Extensibility and core-change impact: Task 3 creates `docs/extensibility-and-change-impact.md` and covers all seven required scenarios.
- File navigation guide: Task 4 creates `docs/file-map.md`.
- Core game-domain subsystem: Task 5 creates `docs/game-domain.md`.
- Events subsystem: Task 6 creates `docs/events-system.md`.
- Fusion subsystem: Task 7 creates `docs/fusion-system.md`.
- Abilities subsystem: Task 8 creates `docs/abilities-system.md`.
- UI/input subsystem: Task 9 creates `docs/ui-and-input.md`.
- Presentation support: Task 10 creates `docs/presentation-summary.md`.
- README remains short while linking to the technical documentation set.

Placeholder scan:

- No task contains placeholder markers or undefined file names.
- Each creation task includes concrete Markdown content and verification commands.
- Each extension scenario includes exact files and core impact.

Type and name consistency:

- Uses the implemented names `GameState`, `Board`, `Move`, `Piece`, `ChessEvent`, `EventManager`, `FusionManager`, `TempoBurstState`, `ActionPointTracker`, `CaptureTracker`, `ShieldTracker`, `Ability`, and `run_post_move_systems()`.
- Uses implemented file paths from `src/` and `tests/`.
- Uses current ability names `KnightSwap`, `BishopSnipe`, `RookShield`, and `PawnSprint`.
- Uses current fused piece names `Archbishop` and `Chancellor`.
