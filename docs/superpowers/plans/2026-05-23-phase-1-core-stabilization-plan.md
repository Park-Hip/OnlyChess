# Chess Fusion Phase 1 Core Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize the core chess domain rules, fix current move/undo risks, and lightly reorganize the codebase so future Fusion and Special Event features can plug in without reopening the same core files repeatedly.

**Architecture:** Phase 1 keeps the project at a university-friendly level: `GameState` remains the main coordinator, but the move domain is grouped into a small `game/` package and the piece model is grouped into a small `pieces/` package. The focus is not adding new features yet, but making core movement, board access, and undo reliable enough for later refactors.

**Tech Stack:** Python, Pygame, pytest, current `src/` package

---

## Planned File and Folder Structure After Phase 1

```text
src/
├── constants.py                  # Shared constants and enums used by game, UI, and events
├── events.py                     # Kept in place for now; only import updates in Phase 1
├── main.py                       # Kept in place; only import updates in Phase 1
├── game/
│   ├── __init__.py
│   ├── board.py                  # Moved from src/board.py
│   ├── move.py                   # Moved from src/move.py
│   └── state_helpers.py          # New helper functions/classes for board-safe access and move-state support
└── pieces/
    ├── __init__.py
    └── piece.py                  # Moved from src/piece.py

tests/
└── game/
    ├── test_board_helpers.py
    ├── test_pawn_boundaries.py
    └── test_move_and_undo.py
```

## File Operation Summary

- **Create**
  - `src/game/__init__.py`
  - `src/game/state_helpers.py`
  - `src/pieces/__init__.py`
  - `tests/game/test_board_helpers.py`
  - `tests/game/test_pawn_boundaries.py`
  - `tests/game/test_move_and_undo.py`
- **Move**
  - `src/board.py` -> `src/game/board.py`
  - `src/move.py` -> `src/game/move.py`
  - `src/piece.py` -> `src/pieces/piece.py`
- **Modify**
  - `src/constants.py`
  - `src/events.py`
  - `src/main.py`
  - `src/game/board.py`
  - `src/game/move.py`
  - `src/pieces/piece.py`
- **Remove**
  - No permanent file removals in Phase 1 beyond replacing old paths through file moves. This keeps the reorganization low-risk and easy to verify.

---

### Task 1: Reorganize the Core Domain into Small Packages

**Files:**
- Create: `src/game/__init__.py`
- Create: `src/pieces/__init__.py`
- Move: `src/board.py` -> `src/game/board.py`
- Move: `src/move.py` -> `src/game/move.py`
- Move: `src/piece.py` -> `src/pieces/piece.py`
- Modify: `src/main.py`
- Modify: `src/events.py`

- [ ] **Step 1: Create the package folders and `__init__.py` files**
  - **Proposed Action:** Create `src/game/` and `src/pieces/` with minimal `__init__.py` files so the project has a clear home for board-state logic and piece logic.
  - **OOP / Clean Code Justification:** This is a shallow, easy-to-understand package split that reduces file crowding without creating an enterprise-style architecture.

- [ ] **Step 2: Move board, move, and piece modules to their new package locations**
  - **Proposed Action:** Move `board.py`, `move.py`, and `piece.py` into the new `game/` and `pieces/` folders, keeping each file’s main responsibility unchanged for now.
  - **OOP / Clean Code Justification:** Files that change together should live together. This grouping makes future refactors more predictable while keeping the mental model simple.

- [ ] **Step 3: Update imports in `src/main.py` and `src/events.py`**
  - **Proposed Action:** Change imports to reference `src.game.board`, `src.game.move`, and `src.pieces.piece`, while keeping runtime behavior unchanged.
  - **OOP / Clean Code Justification:** Import cleanup is necessary to complete the reorganization cleanly. It prevents temporary half-old, half-new module structure from confusing later work.

- [ ] **Step 4: Add smoke tests that confirm imports and initialization still work**
  - **Proposed Action:** Add a small test that imports `GameState`, constructs a board, and confirms the initial valid move generation still succeeds after the file moves.
  - **OOP / Clean Code Justification:** Structural refactors should be validated immediately so later logic fixes are not hiding import breakage.

### Task 2: Remove Magic Numbers and Define Shared Domain Constants

**Files:**
- Modify: `src/constants.py`
- Modify: `src/game/board.py`
- Modify: `src/game/move.py`
- Modify: `src/pieces/piece.py`
- Modify: `src/events.py`
- Test: `tests/game/test_board_helpers.py`

- [ ] **Step 1: Add named constants for board size and piece codes**
  - **Proposed Action:** Expand `src/constants.py` with explicit constants or enums for board dimension, row/column limits, and standard piece codes used across the project.
  - **OOP / Clean Code Justification:** This directly follows the AGENTS rule against magic numbers and strings. It also makes future Fusion pieces and advanced rules easier to express clearly.

- [ ] **Step 2: Replace hardcoded `8` and piece-letter checks in core logic**
  - **Proposed Action:** Update board loops, move generation, castling checks, and event scans to use constants instead of embedded literals like `8`, `'R'`, `'K'`, and `'p'`.
  - **OOP / Clean Code Justification:** This makes the code more readable and reduces the chance of missing one special case during later feature work.

- [ ] **Step 3: Add tests that verify constants-driven logic still behaves correctly**
  - **Proposed Action:** Add tests for board size assumptions and a small sample of move generation paths that now rely on named constants instead of raw values.
  - **OOP / Clean Code Justification:** A constants refactor is only valuable if behavior stays stable. These tests create confidence for the next rule-level changes.

### Task 3: Add Safe Board Access Helpers and Fix Pawn Boundary Risks

**Files:**
- Create: `src/game/state_helpers.py`
- Modify: `src/game/board.py`
- Modify: `src/pieces/piece.py`
- Modify: `src/game/move.py`
- Test: `tests/game/test_board_helpers.py`
- Test: `tests/game/test_pawn_boundaries.py`

- [ ] **Step 1: Add board-safe helper functions or helper classes**
  - **Proposed Action:** Create `src/game/state_helpers.py` with helpers such as `is_inside_board()`, `safe_get_piece()`, and any small utilities needed to avoid risky raw grid indexing.
  - **OOP / Clean Code Justification:** This centralizes low-level board safety rules in one place instead of repeating them inside many move functions.

- [ ] **Step 2: Update `GameState` and `Piece` logic to use the helpers**
  - **Proposed Action:** Refactor movement code, especially pawn forward movement and edge-sensitive checks, to call the safe helpers before reading or writing board squares.
  - **OOP / Clean Code Justification:** This is a practical encapsulation improvement because pieces should rely on a safe board API, not on fragile direct indexing.

- [ ] **Step 3: Add regression tests for edge-of-board pawn cases**
  - **Proposed Action:** Write tests that place pawns on extreme rows and confirm the system does not generate invalid moves or crash when move lists are printed or inspected.
  - **OOP / Clean Code Justification:** This targets a real bug class found in the audit and ensures the core engine is safe before advanced-mode rules start altering piece positions in non-standard ways.

### Task 4: Upgrade `Move` into a Reliable Move-State Snapshot Object

**Files:**
- Modify: `src/game/move.py`
- Modify: `src/game/board.py`
- Test: `tests/game/test_move_and_undo.py`

- [ ] **Step 1: Define what state a `Move` must remember for exact undo**
  - **Proposed Action:** Extend the `Move` object to store pre-move values such as moved-piece position, `has_moved`, captured-piece reference, en passant state, and promotion replacement details.
  - **OOP / Clean Code Justification:** A move should carry its own history so undo logic does not need to guess. This is the simplest correct form of encapsulation for reversible actions.

- [ ] **Step 2: Refactor `make_move()` to fill the new `Move` state fields**
  - **Proposed Action:** Update `GameState.make_move()` so it records all undo-critical information into the move before changing board state.
  - **OOP / Clean Code Justification:** Capturing history at the time of the action is more reliable than reconstructing it later from a changed board.

- [ ] **Step 3: Add tests for normal move, capture, en passant, and promotion bookkeeping**
  - **Proposed Action:** Add tests that inspect `Move` after execution and confirm it carries enough information to support exact restoration.
  - **OOP / Clean Code Justification:** This validates the move object as a proper domain object instead of a thin coordinate container.

### Task 5: Split `make_move()` into Small Internal Rule Steps

**Files:**
- Modify: `src/game/board.py`
- Test: `tests/game/test_move_and_undo.py`

- [ ] **Step 1: Introduce focused private helpers inside `GameState`**
  - **Proposed Action:** Break `make_move()` into smaller internal methods for applying base movement, resolving en passant, resolving promotion, resolving castling rook movement, updating king positions, and updating post-move state.
  - **OOP / Clean Code Justification:** This keeps `GameState` as the coordinator but removes the current God-method shape. Smaller helpers are easier to extend later with Fusion and event hooks.

- [ ] **Step 2: Keep public behavior unchanged while improving internal structure**
  - **Proposed Action:** Ensure the public `make_move()` signature remains stable so `main.py` and other callers do not need a large API rewrite in Phase 1.
  - **OOP / Clean Code Justification:** This respects the “basic Open/Closed” goal by improving internals without needlessly changing external usage at the same time.

- [ ] **Step 3: Add regression tests around valid move generation after refactor**
  - **Proposed Action:** Add tests that verify the initial game state still returns the expected count of valid moves and that castling/promotion behavior still routes through `make_move()` correctly.
  - **OOP / Clean Code Justification:** This confirms the refactor improved structure without silently breaking core chess behavior.

### Task 6: Refactor `undo_move()` to Restore Exact State

**Files:**
- Modify: `src/game/board.py`
- Modify: `src/game/move.py`
- Test: `tests/game/test_move_and_undo.py`

- [ ] **Step 1: Rewrite undo restoration around `Move` snapshot data**
  - **Proposed Action:** Update `undo_move()` to restore moved piece state, captured piece state, king position, en passant state, castling state, and special-move side effects from stored move metadata.
  - **OOP / Clean Code Justification:** This makes undo deterministic and future-proof. Advanced features like Fusion and events will fail quickly if undo remains partial or state-blind.

- [ ] **Step 2: Keep event integration untouched except for import/path updates**
  - **Proposed Action:** Do not redesign the event system yet in Phase 1; only make sure the refactored undo still cooperates with the current event hooks so Phase 4 can improve that system separately.
  - **OOP / Clean Code Justification:** This keeps the phase scoped and avoids overengineering. Each phase should solve one architectural layer cleanly.

- [ ] **Step 3: Add round-trip tests for move then undo**
  - **Proposed Action:** Write tests that perform a move, call undo, and confirm the board, king positions, `white_to_move`, en passant state, and castling rights return exactly to their previous values.
  - **OOP / Clean Code Justification:** Round-trip testing is the clearest way to prove the core reversible game state is healthy before moving on.

### Task 7: Verify the Reorganized Core and Freeze the New Baseline

**Files:**
- Modify: `src/main.py`
- Modify: `src/events.py`
- Test: `tests/game/test_board_helpers.py`
- Test: `tests/game/test_pawn_boundaries.py`
- Test: `tests/game/test_move_and_undo.py`

- [ ] **Step 1: Run the focused test suite for Phase 1**
  - **Proposed Action:** Run the three new Phase 1 test files and verify the reorganized project passes all core stabilization checks.
  - **OOP / Clean Code Justification:** This creates a stable baseline before any Phase 2 extensibility refactor begins.

- [ ] **Step 2: Launch the game manually for a smoke check**
  - **Proposed Action:** Run the game once and verify start-up, selection, movement, undo, and promotion still work after the file moves and logic cleanup.
  - **OOP / Clean Code Justification:** The project is still a Pygame application, so manual validation complements unit tests for integration-heavy flows.

- [ ] **Step 3: Document the new import structure with short docstrings**
  - **Proposed Action:** Add or update docstrings in the moved modules so the new `game/` and `pieces/` package responsibilities are explicit before Phase 2 starts.
  - **OOP / Clean Code Justification:** Clear responsibilities make the code easier to explain and maintain, which is especially important in a student OOP project.

---

## Why This Structure Is Recommended for Phase 1

- [ ] **Keep `events.py` and `main.py` in place for now**
  - **Target File(s):** `src/events.py`, `src/main.py`
  - **Proposed Action:** Avoid moving UI and event files in Phase 1; only update imports so the phase stays focused on domain stabilization rather than wide structural churn.
  - **OOP / Clean Code Justification:** This keeps the refactor incremental and avoids changing too many layers at once.

- [ ] **Group core rules into `src/game/` early**
  - **Target File(s):** `src/game/`
  - **Proposed Action:** Move board and move logic into one package now because those files will change together repeatedly through later phases.
  - **OOP / Clean Code Justification:** This follows the rule that files that change together should live together, while still remaining simple enough for a course project.

- [ ] **Keep `src/pieces/` shallow**
  - **Target File(s):** `src/pieces/piece.py`
  - **Proposed Action:** Use only one piece module in Phase 1 and postpone splitting standard/custom pieces until a later phase actually needs it.
  - **OOP / Clean Code Justification:** This respects the “no overengineering” rule by not creating extra abstraction before it is needed.
