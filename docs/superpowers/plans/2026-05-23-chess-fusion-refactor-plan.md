# Chess Fusion Refactoring Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the current Chess Fusion codebase into a cleaner, safer, and more extensible university-level OOP architecture before implementing Fusion rules, abilities, or new Special Events.

**Architecture:** Keep `GameState` as the central coordinator, but reduce its responsibility by extracting focused helpers for piece creation, move history, capture tracking, rendering, and event orchestration. The main extension seams will be a piece registry, a post-move rule pipeline, and an event system based on simple inheritance and polymorphism instead of hardcoded branching.

**Tech Stack:** Python, Pygame, current `src/` package structure

---

## Module-Level Direction

- [ ] **`src/main.py` should become a thin game loop**
  - **Target File(s):** `src/main.py`
  - **Proposed Action:** Reduce `main.py` to orchestration only: initialize Pygame, forward input, trigger game-state actions, and call rendering helpers. Move board drawing, info-panel drawing, promotion UI, and input state transitions into focused UI modules.
  - **OOP / Clean Code Justification:** This removes the current multi-responsibility file and prevents the main loop from turning into a God Object. It also makes future right-click abilities and event overlays much easier to add.

- [ ] **`src/board.py` should become a rules coordinator, not a storage dump**
  - **Target File(s):** `src/board.py`
  - **Proposed Action:** Keep `Board` responsible for board data and piece placement, and keep `GameState` responsible for move orchestration and game status, but move side concerns such as piece factories, capture summaries, scoring, and post-move systems out to helpers.
  - **OOP / Clean Code Justification:** This keeps the core gameplay model easy to understand while reducing coupling. It matches `AGENTS.md` by avoiding a bloated central class.

- [ ] **`src/piece.py` should become the source of piece behavior and metadata**
  - **Target File(s):** `src/piece.py`
  - **Proposed Action:** Let each piece class own its move logic, identity, sprite key, and material value, and prepare small extension points for future fusion and abilities without implementing those systems yet.
  - **OOP / Clean Code Justification:** This uses encapsulation and polymorphism in the most natural place: the piece object itself. It prevents future `if piece.name == ...` chains from spreading into unrelated modules.

- [ ] **`src/events.py` should separate event definitions from event scheduling**
  - **Target File(s):** `src/events.py`
  - **Proposed Action:** Keep a simple base event class, but split event behavior from manager logic so events focus on warning/execute/cleanup and the manager focuses on turn timing, queueing, and undo snapshots.
  - **OOP / Clean Code Justification:** This is a clean SRP improvement without introducing advanced patterns. It creates a safe path for adding more event types later.

- [ ] **`src/move.py` should become a reliable move snapshot object**
  - **Target File(s):** `src/move.py`
  - **Proposed Action:** Expand `Move` so it can carry the minimum pre-move and post-move state needed for correct undo, promotion, fusion follow-up, and event-safe history restoration.
  - **OOP / Clean Code Justification:** A move object should encapsulate move-specific state instead of making `GameState` reconstruct history manually. This directly improves correctness and future extensibility.

## Phase 1: Stabilize Core Domain Rules

- [ ] **Task 1: Replace magic numbers and piece strings with named constants**
  - **Target File(s):** `src/constants.py`, `src/board.py`, `src/piece.py`, `src/events.py`, `src/main.py`, `src/move.py`
  - **Proposed Action:** Add constants or enums for board dimensions, files/ranks, and piece identifiers, then replace hardcoded `8`, `'R'`, `'N'`, `'B'`, `'Q'`, `'K'`, and `'p'` in game logic with named values.
  - **OOP / Clean Code Justification:** This directly follows the “no magic numbers/strings” rule in `AGENTS.md`. It also makes later refactors safer because logic depends on explicit concepts instead of scattered literals.

- [ ] **Task 2: Add safe board helper methods for bounds and square access**
  - **Target File(s):** `src/board.py`, `src/piece.py`, `src/move.py`
  - **Proposed Action:** Add helpers such as `is_inside_board()`, `get_piece_at()`, and `set_piece_at()` so movement code stops indexing the grid directly in risky places.
  - **OOP / Clean Code Justification:** Encapsulating board access in one place reduces repeated low-level logic and prevents edge-case bugs. This is especially useful once events and fusion start moving pieces in non-standard ways.

- [ ] **Task 3: Fix pawn edge-case movement generation**
  - **Target File(s):** `src/piece.py`
  - **Proposed Action:** Refactor pawn movement so forward movement checks boundaries before reading `grid`, and ensure illegal off-board move generation cannot create invalid `Move` objects.
  - **OOP / Clean Code Justification:** This solves a real correctness issue with minimal complexity. It keeps move generation robust before more advanced rules are added.

- [ ] **Task 4: Expand `Move` to store undo-critical state**
  - **Target File(s):** `src/move.py`, `src/board.py`
  - **Proposed Action:** Add fields for prior piece position/state, captured-piece state, promotion replacement details, and any flags needed so undo can restore a move exactly instead of approximately.
  - **OOP / Clean Code Justification:** The move object is the right place to carry move history because that state belongs to the move itself. This reduces fragile reconstruction logic in `GameState`.

- [ ] **Task 5: Refactor `make_move()` into internal rule steps**
  - **Target File(s):** `src/board.py`
  - **Proposed Action:** Split `make_move()` into small private helpers such as applying the basic movement, resolving special move behavior, updating state trackers, and running post-move systems.
  - **OOP / Clean Code Justification:** This shrinks the current God-method without changing the basic architecture. Smaller steps are easier to reason about, test, and extend.

- [ ] **Task 6: Refactor `undo_move()` to restore exact state**
  - **Target File(s):** `src/board.py`, `src/move.py`
  - **Proposed Action:** Rework undo so it restores piece state, en passant state, castling state, king position, and special-move side effects from stored move data rather than recomputing only part of the state.
  - **OOP / Clean Code Justification:** Undo should be deterministic and complete because future fusion/event systems will depend on it. This is a correctness-first refactor that reduces hidden state bugs.

## Phase 2: Create a Clean Piece Model for Future Fusion

- [ ] **Task 7: Introduce a simple piece registry**
  - **Target File(s):** `src/board.py`, new `src/piece_registry.py`, `src/piece.py`
  - **Proposed Action:** Replace the `Board.create_piece()` `if` chain with a registry that maps piece codes to classes and use it for board setup and promotion.
  - **OOP / Clean Code Justification:** This creates a simple Open/Closed seam where new piece types can be added without modifying the board core repeatedly. It is practical and easy to explain in an OOP course setting.

- [ ] **Task 8: Move piece metadata into piece classes**
  - **Target File(s):** `src/piece.py`
  - **Proposed Action:** Let each piece class provide its own code, display id, sprite key, and material value, instead of relying on `piece.id[1]` and external dictionaries.
  - **OOP / Clean Code Justification:** A piece should know what it is and how it should be treated. This is a direct application of encapsulation and avoids scattered type checks.

- [ ] **Task 9: Add light extension hooks for fused/custom pieces**
  - **Target File(s):** `src/piece.py`
  - **Proposed Action:** Add small methods such as `get_material_value()`, `get_sprite_key()`, `can_fuse()`, and `is_minor_piece()` so future systems can ask pieces for behavior instead of branching on string ids.
  - **OOP / Clean Code Justification:** This uses polymorphism where it naturally fits and prevents future special-case chains. It stays lightweight because the methods are small and concrete.

- [ ] **Task 10: Reorganize piece modules for readability**
  - **Target File(s):** `src/piece.py`, optional new `src/pieces/standard.py`, `src/pieces/custom.py`, `src/pieces/__init__.py`
  - **Proposed Action:** Split standard piece classes from future custom piece classes if `src/piece.py` becomes too crowded during refactor, while keeping the package shallow and easy to navigate.
  - **OOP / Clean Code Justification:** This keeps files focused without introducing unnecessary architectural depth. It makes future additions like Archbishop and Chancellor easier to place and maintain.

## Phase 3: Reduce `GameState` Coupling

- [ ] **Task 11: Extract castling logic into focused helpers**
  - **Target File(s):** `src/board.py`
  - **Proposed Action:** Separate castling validation, rook movement during castle, and castling-right updates into clearly named helper methods inside `GameState` or a small castling helper.
  - **OOP / Clean Code Justification:** Castling is already a mini-rule system and should not be mixed inline with every other move concern. This also creates a clear place to fix stale-rights bugs caused by piece transformation.

- [ ] **Task 12: Extract capture tracking from board-state inference**
  - **Target File(s):** `src/board.py`, new `src/capture_tracker.py`
  - **Proposed Action:** Replace `get_captured_pieces()` counting logic with a dedicated tracker updated during move execution, undo, and future event-based piece removal.
  - **OOP / Clean Code Justification:** Current capture inference breaks once pieces can transform, fuse, or revive. Explicit tracking is simpler and more correct for the advanced mode described in `mode.md`.

- [ ] **Task 13: Extract material scoring into a focused helper**
  - **Target File(s):** `src/board.py`, `src/piece.py`, optional new `src/scoring.py`
  - **Proposed Action:** Move material evaluation out of `GameState` and make scoring depend on each piece’s own material value rather than a local hardcoded dictionary.
  - **OOP / Clean Code Justification:** This removes one more type-based decision from the central state class. It also makes custom pieces work without reopening core scoring code.

- [ ] **Task 14: Add a post-move systems pipeline**
  - **Target File(s):** `src/board.py`, optional new `src/rules.py`
  - **Proposed Action:** Add a simple sequence after every real move for systems such as capture tracking, event updates, and later fusion resolution, instead of embedding all future logic directly into `make_move()`.
  - **OOP / Clean Code Justification:** This is the main extensibility seam the current code is missing. It keeps the move pipeline open to extension while keeping the design understandable.

## Phase 4: Refactor the Event System Before Adding More Events

- [ ] **Task 15: Clarify the base event lifecycle**
  - **Target File(s):** `src/events.py`
  - **Proposed Action:** Strengthen the `ChessEvent` base class so each event clearly owns warning activation, execution, cleanup, rendering, and any snapshot data it needs for undo.
  - **OOP / Clean Code Justification:** This is a good use of inheritance because all events share the same lifecycle shape. It reduces event-specific assumptions inside the manager.

- [ ] **Task 16: Separate event behavior from event orchestration**
  - **Target File(s):** `src/events.py`, optional new `src/event_manager.py`, `src/events/base.py`, `src/events/gia_xang_tang.py`
  - **Proposed Action:** Move event scheduling, queueing, and turn counting into a manager-focused module, and keep each event class responsible only for its own gameplay effect and UI warning state.
  - **OOP / Clean Code Justification:** This is a clean Single Responsibility improvement without introducing advanced infrastructure. It makes future event additions much safer and clearer.

- [ ] **Task 17: Remove hardcoded event reconstruction in undo sync**
  - **Target File(s):** `src/events.py`
  - **Proposed Action:** Replace hardcoded `GiaXangTang` reconstruction in `sync_state()` with a stored event type or simple event registry so queued events can be restored generically.
  - **OOP / Clean Code Justification:** This fixes a direct Open/Closed violation in the current implementation. New event types should not require reopening the manager’s undo logic every time.

- [ ] **Task 18: Expand event snapshots beyond board-grid copy**
  - **Target File(s):** `src/events.py`, `src/board.py`
  - **Proposed Action:** Redesign event snapshot data so it can restore all event-related game state, including board changes, queued event information, and any future advanced-mode event fields.
  - **OOP / Clean Code Justification:** Undo must restore the true state of the game, not only the visible board. This is essential before implementing minefields, meteor warnings, or revival events.

- [ ] **Task 19: Route event board mutations through explicit helpers**
  - **Target File(s):** `src/events.py`, `src/board.py`
  - **Proposed Action:** Add board/game helpers for replacing, removing, or spawning pieces, and update event code to call those helpers instead of writing directly to `board.grid`.
  - **OOP / Clean Code Justification:** This centralizes rule-sensitive board mutations and protects systems like castling, capture tracking, and undo from silent desynchronization. It is a simple but high-impact encapsulation improvement.

## Phase 5: Clean the UI Layer for Future Ability/Event UX

- [ ] **Task 20: Extract rendering responsibilities out of `main.py`**
  - **Target File(s):** `src/main.py`, new `src/ui/render_board.py`, new `src/ui/render_panels.py`
  - **Proposed Action:** Move board drawing, square highlighting, piece drawing, and information-panel rendering into small UI modules while keeping the main loop responsible only for orchestration.
  - **OOP / Clean Code Justification:** Rendering should not be mixed with input and game-rule flow in one file. This keeps the project easier to scale when AP bars and event overlays are added.

- [ ] **Task 21: Extract input handling and selection state**
  - **Target File(s):** `src/main.py`, new `src/ui/input_handler.py`
  - **Proposed Action:** Refactor click selection, drag selection, move-attempt creation, and cancel/reselect logic into a focused input helper or class.
  - **OOP / Clean Code Justification:** This keeps UI interaction logic out of the already busy main loop. It also creates a clear place for future right-click ability input and multi-step targeting.

- [ ] **Task 22: Isolate promotion menu logic**
  - **Target File(s):** `src/main.py`, new `src/ui/promotion_menu.py`
  - **Proposed Action:** Move promotion menu rendering and choice resolution into a small dedicated UI component that returns a selected piece code to the main loop.
  - **OOP / Clean Code Justification:** Promotion is already its own workflow and should be treated as a separate responsibility. This also prepares the code to support promotion through the piece registry.

- [ ] **Task 23: Replace hardcoded image loading with asset lookup**
  - **Target File(s):** `src/main.py`, new `src/ui/assets.py`, `src/piece.py`
  - **Proposed Action:** Refactor image loading to use sprite keys from piece objects or a simple asset registry, instead of hardcoding the 12 standard piece ids in `main.py`.
  - **OOP / Clean Code Justification:** The UI should ask a piece what to draw rather than assuming a fixed set forever. This is necessary for fused pieces and any transformed-event states.

## Phase 6: Prepare for Fusion and Advanced Mode Systems

- [ ] **Task 24: Add a fusion-resolution seam without implementing fusion yet**
  - **Target File(s):** `src/board.py`, new `src/fusion.py`
  - **Proposed Action:** Add a small `FusionResolver` or similarly named helper that `GameState` can call after captures, even if its first version always returns “no fusion”.
  - **OOP / Clean Code Justification:** This creates the exact extension point needed for the project’s core feature without prematurely building the full system. It prevents fusion rules from being shoved into `make_move()` later.

- [ ] **Task 25: Reserve advanced-mode state in `GameState`**
  - **Target File(s):** `src/board.py`
  - **Proposed Action:** Introduce clearly named placeholders for future state from `mode.md`, such as AP, fused-piece bookkeeping, and long-lived event state, without implementing their game behavior yet.
  - **OOP / Clean Code Justification:** This makes future responsibilities visible and intentional instead of bolted on later. It supports incremental growth while keeping the current refactor grounded.

- [ ] **Task 26: Define a minimal subsystem order after each move**
  - **Target File(s):** `src/board.py`, `src/events.py`, `src/fusion.py`, optional `src/rules.py`
  - **Proposed Action:** Standardize the order of post-move processing as board update, special move resolution, capture tracking, fusion check, event update, and UI refresh trigger.
  - **OOP / Clean Code Justification:** A clear execution order reduces hidden coupling between future systems. This is a practical architecture rule, not an advanced framework.

## Phase 7: Documentation and Verification Readiness

- [ ] **Task 27: Add docstrings to every new class and extension seam**
  - **Target File(s):** All touched `src/` files
  - **Proposed Action:** Add short docstrings that explain the role of each refactored helper, registry, tracker, and event lifecycle class.
  - **OOP / Clean Code Justification:** This directly follows the workflow in `AGENTS.md`. It also makes the architecture easier for a student to present and defend.

- [ ] **Task 28: Keep file structure shallow and intentional**
  - **Target File(s):** `src/` package structure as a whole
  - **Proposed Action:** Reorganize only where responsibility separation clearly improves readability, and avoid creating too many tiny modules that would confuse the project more than help it.
  - **OOP / Clean Code Justification:** This enforces the “no overengineering” constraint while still cleaning up the architecture. The goal is clarity and extension-friendliness, not enterprise complexity.

- [ ] **Task 29: Lock in the implementation order after refactor**
  - **Target File(s):** Planning/documentation layer only for now
  - **Proposed Action:** After the refactor is complete, implement new systems in this order: fusion seam activation, custom fused pieces, capture-aware scoring/UI, AP state, active abilities, then advanced event pool.
  - **OOP / Clean Code Justification:** This order follows dependency direction and reduces rework. It ensures core rule stability before the project’s more chaotic mechanics are introduced.
