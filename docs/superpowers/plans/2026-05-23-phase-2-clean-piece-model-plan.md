# Chess Fusion Phase 2 Clean Piece Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the piece model so chess pieces own their metadata and creation flow, making it easy to add future Fusion pieces without repeatedly editing `Board` or scattering piece-type checks across the codebase.

**Architecture:** Keep the design basic and student-friendly: a `Piece` base class for shared behavior, a `standard.py` module for normal chess pieces, and a tiny registry module for piece creation. The registry is intentionally simple and explicit, so adding a new piece later means “create class + register code” instead of touching multiple core files.

**Tech Stack:** Python, Pygame, `unittest`, current `src/` package

---

## Planned File and Folder Structure After Phase 2

```text
src/
├── constants.py
├── events.py
├── main.py
├── game/
│   ├── __init__.py
│   ├── board.py
│   ├── move.py
│   └── state_helpers.py
└── pieces/
    ├── __init__.py
    ├── base.py                    # Piece base class and shared movement helpers
    ├── standard.py                # Pawn, Knight, Bishop, Rook, Queen, King
    └── registry.py                # Piece registration and creation helpers

tests/
├── game/
│   └── test_board_piece_creation.py
└── pieces/
    ├── test_piece_metadata.py
    ├── test_piece_registry.py
    └── test_piece_extension_hooks.py
```

## File Operation Summary

- **Create**
  - `src/pieces/base.py`
  - `src/pieces/registry.py`
  - `tests/game/test_board_piece_creation.py`
  - `tests/pieces/test_piece_metadata.py`
  - `tests/pieces/test_piece_registry.py`
  - `tests/pieces/test_piece_extension_hooks.py`
- **Move**
  - `src/pieces/piece.py` -> `src/pieces/standard.py`
- **Modify**
  - `src/pieces/__init__.py`
  - `src/game/board.py`
  - `src/main.py`
  - `src/constants.py`
  - `src/events.py`
- **Remove**
  - Remove `src/pieces/piece.py` after imports are updated to the new module layout.

---

### Task 1: Split the Piece Package into Clear Responsibilities

**Files:**
- Create: `src/pieces/base.py`
- Move: `src/pieces/piece.py` -> `src/pieces/standard.py`
- Modify: `src/pieces/__init__.py`
- Modify: `src/game/board.py`
- Modify: `src/events.py`

- [ ] **Step 1: Move standard piece implementations into `standard.py`**
  - **Target File(s):** `src/pieces/standard.py`
  - **Proposed Action:** Move `Pawn`, `Knight`, `Bishop`, `Rook`, `Queen`, and `King` into `standard.py`, keeping their move logic unchanged at first.
  - **OOP / Clean Code Justification:** This separates standard piece implementations from the base abstraction and keeps the package easier to extend later.

- [ ] **Step 2: Extract the `Piece` base class and shared helpers into `base.py`**
  - **Target File(s):** `src/pieces/base.py`
  - **Proposed Action:** Move the `Piece` base class and reusable helpers such as `_get_sliding_moves()` into `base.py`, then make `standard.py` import from it.
  - **OOP / Clean Code Justification:** Shared behavior belongs in the base class, while concrete piece rules belong in their own module. This is a natural use of inheritance without adding complexity.

- [ ] **Step 3: Use `src/pieces/__init__.py` as the stable import surface**
  - **Target File(s):** `src/pieces/__init__.py`, `src/game/board.py`, `src/events.py`
  - **Proposed Action:** Re-export `Piece`, `Pawn`, `Knight`, `Bishop`, `Rook`, `Queen`, and `King` from `__init__.py`, then update callers to import from `src.pieces` instead of a single file path.
  - **OOP / Clean Code Justification:** A small package-level import surface keeps the structure clean and reduces future churn when files move again.

### Task 2: Introduce a Simple Piece Registry

**Files:**
- Create: `src/pieces/registry.py`
- Modify: `src/game/board.py`
- Modify: `src/pieces/__init__.py`
- Test: `tests/pieces/test_piece_registry.py`
- Test: `tests/game/test_board_piece_creation.py`

- [ ] **Step 1: Add a simple registry mapping piece codes to classes**
  - **Target File(s):** `src/pieces/registry.py`
  - **Proposed Action:** Create a small registry such as `PIECE_CLASS_BY_CODE` plus helper functions like `create_piece(piece_code, color, pos)` and `get_registered_piece_codes()`.
  - **OOP / Clean Code Justification:** This creates the Open/Closed seam needed for Fusion pieces while staying easy to understand and debug.

- [ ] **Step 2: Replace `Board.create_piece()` branching with registry-based creation**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Refactor `Board.create_piece()` to delegate piece creation to the registry instead of using a hardcoded `if` chain.
  - **OOP / Clean Code Justification:** Piece creation should not require reopening the board core every time a new type is introduced.

- [ ] **Step 3: Reuse the registry for promotion creation**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Update pawn promotion to build the promoted piece through the same registry helpers used by initial board setup.
  - **OOP / Clean Code Justification:** One creation path is easier to maintain than separate hardcoded paths for setup and promotion.

- [ ] **Step 4: Add tests that lock in registry behavior**
  - **Target File(s):** `tests/pieces/test_piece_registry.py`, `tests/game/test_board_piece_creation.py`
  - **Proposed Action:** Add tests for creating each standard piece by code, rejecting unknown codes cleanly, and confirming `Board.setup_classic()` still produces the right starting arrangement through the registry.
  - **OOP / Clean Code Justification:** This verifies the new creation seam before future custom pieces rely on it.

### Task 3: Move Piece Metadata into the Piece Objects

**Files:**
- Modify: `src/pieces/base.py`
- Modify: `src/pieces/standard.py`
- Modify: `src/game/board.py`
- Modify: `src/main.py`
- Test: `tests/pieces/test_piece_metadata.py`

- [ ] **Step 1: Add explicit metadata methods or properties to `Piece`**
  - **Target File(s):** `src/pieces/base.py`
  - **Proposed Action:** Add small metadata access points such as `piece_code`, `get_display_id()`, `get_sprite_key()`, and `get_material_value()` on the base class, with concrete values supplied by subclasses.
  - **OOP / Clean Code Justification:** A piece should describe itself instead of forcing outside modules to slice strings like `piece.id[1]`.

- [ ] **Step 2: Update standard pieces to declare their own metadata**
  - **Target File(s):** `src/pieces/standard.py`
  - **Proposed Action:** Give each standard piece class its own piece code and material value, while preserving the existing movement logic from Phase 1.
  - **OOP / Clean Code Justification:** This is direct encapsulation: piece identity and value belong to the piece class itself.

- [ ] **Step 3: Update UI-facing code to use sprite keys instead of raw `id` assumptions**
  - **Target File(s):** `src/main.py`
  - **Proposed Action:** Change rendering and promotion-menu code so image lookup uses `piece.get_sprite_key()` or the equivalent metadata access point rather than assuming every piece is addressed through `piece.id`.
  - **OOP / Clean Code Justification:** This makes the rendering path ready for fused/custom pieces without requiring special-case UI logic later.

- [ ] **Step 4: Add metadata tests**
  - **Target File(s):** `tests/pieces/test_piece_metadata.py`
  - **Proposed Action:** Write tests verifying each standard piece reports the correct code, sprite key, and material value, and that these values are stable for the rest of the project.
  - **OOP / Clean Code Justification:** This turns the new self-description API into a trustworthy contract for later phases.

### Task 4: Add Lightweight Extension Hooks for Future Fusion Pieces

**Files:**
- Modify: `src/pieces/base.py`
- Modify: `src/pieces/standard.py`
- Test: `tests/pieces/test_piece_extension_hooks.py`

- [ ] **Step 1: Add future-facing but minimal hooks on the base class**
  - **Target File(s):** `src/pieces/base.py`
  - **Proposed Action:** Add methods like `can_fuse()`, `is_minor_piece()`, `get_fusion_tags()`, and `get_move_profile_name()` with safe defaults on the base class.
  - **OOP / Clean Code Justification:** These hooks give future fusion/event logic a clean API to ask pieces about themselves, without forcing immediate feature implementation.

- [ ] **Step 2: Override hooks only where standard pieces need meaningful answers**
  - **Target File(s):** `src/pieces/standard.py`
  - **Proposed Action:** Override only the hooks that matter now, such as marking bishops/knights as minor pieces or marking kings as non-fusible.
  - **OOP / Clean Code Justification:** This keeps the design practical and avoids overengineering by only adding overrides that serve clear upcoming needs.

- [ ] **Step 3: Add tests that define the extension-hook contract**
  - **Target File(s):** `tests/pieces/test_piece_extension_hooks.py`
  - **Proposed Action:** Write tests verifying `can_fuse()`, `is_minor_piece()`, and similar hooks return predictable values for standard pieces.
  - **OOP / Clean Code Justification:** Fusion logic in later phases will depend on these methods, so their behavior should be fixed by tests now.

### Task 5: Update Core Call Sites to Depend on the New Piece Model

**Files:**
- Modify: `src/game/board.py`
- Modify: `src/events.py`
- Modify: `src/main.py`
- Test: `tests/game/test_board_piece_creation.py`

- [ ] **Step 1: Replace direct class imports with package imports where appropriate**
  - **Target File(s):** `src/game/board.py`, `src/events.py`
  - **Proposed Action:** Update core files to import through `src.pieces` or `src.pieces.registry` rather than depending on one concrete implementation file.
  - **OOP / Clean Code Justification:** This reduces coupling to file layout and keeps future piece refactors localized inside the package.

- [ ] **Step 2: Replace remaining type-string assumptions in piece-related logic**
  - **Target File(s):** `src/game/board.py`, `src/main.py`
  - **Proposed Action:** Where reasonable in Phase 2, switch piece-related logic from raw `piece.id[1]` or `piece.name` checks to the new metadata or hook methods.
  - **OOP / Clean Code Justification:** This is the core payoff of the refactor: behavior should depend on object capabilities, not repeated string inspection.

- [ ] **Step 3: Keep event behavior compatible with the new piece model**
  - **Target File(s):** `src/events.py`
  - **Proposed Action:** Adjust event code only enough to stay compatible with the new import and creation paths, without redesigning the event system yet.
  - **OOP / Clean Code Justification:** This keeps Phase 2 focused on piece modeling while avoiding side regressions in the current event flow.

### Task 6: Verify the New Piece Model and Freeze the Phase 2 Baseline

**Files:**
- Test: `tests/game/test_board_piece_creation.py`
- Test: `tests/pieces/test_piece_metadata.py`
- Test: `tests/pieces/test_piece_registry.py`
- Test: `tests/pieces/test_piece_extension_hooks.py`
- Modify: `src/pieces/base.py`
- Modify: `src/pieces/standard.py`
- Modify: `src/pieces/registry.py`

- [ ] **Step 1: Run the Phase 2 focused test suite**
  - **Target File(s):** test files listed above
  - **Proposed Action:** Run the new piece-package tests plus the existing Phase 1 game tests to confirm the refactor preserved chess behavior while improving structure.
  - **OOP / Clean Code Justification:** Phase 2 must preserve the stable movement baseline from Phase 1, not just improve file organization.

- [ ] **Step 2: Add docstrings to the new piece modules and registry helpers**
  - **Target File(s):** `src/pieces/base.py`, `src/pieces/standard.py`, `src/pieces/registry.py`
  - **Proposed Action:** Add short docstrings explaining each file’s responsibility and the purpose of the registry and extension hooks.
  - **OOP / Clean Code Justification:** This keeps the architecture easy to explain in a university OOP setting and matches the workflow from `AGENTS.md`.

- [ ] **Step 3: Confirm the package stays shallow**
  - **Target File(s):** `src/pieces/`
  - **Proposed Action:** Before closing Phase 2, verify the package still uses only the minimum number of files needed and has not drifted into unnecessary abstraction.
  - **OOP / Clean Code Justification:** This protects the project from overengineering while still making future Fusion work much easier.

---

## Why This Phase 2 Structure Is Recommended

- [ ] **Use one registry, not a factory hierarchy**
  - **Target File(s):** `src/pieces/registry.py`
  - **Proposed Action:** Keep piece creation as a plain code-to-class mapping with a few helper functions, not a multi-layer factory system.
  - **OOP / Clean Code Justification:** This is enough extensibility for the project without violating the “NO OVERENGINEERING” rule.

- [ ] **Split `Piece` base and standard pieces, but stop there**
  - **Target File(s):** `src/pieces/base.py`, `src/pieces/standard.py`
  - **Proposed Action:** Use only one split between shared abstraction and standard implementations; postpone `custom.py` or deeper subpackages until actual fused pieces exist.
  - **OOP / Clean Code Justification:** This keeps the package readable and practical, which is exactly the balance this project needs.

- [ ] **Make future Fusion pieces first-class objects**
  - **Target File(s):** `src/pieces/base.py`, `src/pieces/registry.py`
  - **Proposed Action:** Design the metadata and registry so later fused pieces can be added as normal classes rather than as special cases hidden inside board logic.
  - **OOP / Clean Code Justification:** This is the cleanest way to align the architecture with the project’s main feature while staying within fundamental OOP principles.
