# Chess Fusion Phase 3 Reduce GameState Coupling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `GameState` so it remains the main coordinator but no longer directly owns every rule detail, summary calculation, and post-move responsibility needed by the game.

**Architecture:** Keep the design simple and OOP-focused: `GameState` coordinates the turn lifecycle, while focused helper modules handle castling state, capture summaries, material scoring, and post-move rule flow. Castling remains a required feature, but Phase 3 should localize castling-specific control so only the king/castling path cares about it instead of leaking that concern through every piece method.

**Tech Stack:** Python, Pygame, `unittest`, current `src/` package

---

## Planned File and Folder Structure After Phase 3

```text
src/
├── constants.py
├── events.py
├── main.py
├── game/
│   ├── __init__.py
│   ├── board.py
│   ├── capture_tracker.py         # New explicit captured-piece summary helper
│   ├── castling.py                # New castling-rights state and helper functions
│   ├── move.py
│   ├── rules.py                   # New post-move systems pipeline
│   ├── scoring.py                 # New material scoring helper
│   └── state_helpers.py
└── pieces/
    ├── __init__.py
    ├── base.py
    ├── registry.py
    └── standard.py

tests/
├── game/
│   ├── test_capture_tracker.py
│   ├── test_castling_helpers.py
│   ├── test_game_rules_pipeline.py
│   ├── test_material_scoring.py
│   └── test_board_piece_creation.py
└── pieces/
    ├── test_piece_extension_hooks.py
    ├── test_piece_metadata.py
    └── test_piece_registry.py
```

## File Operation Summary

- **Create**
  - `src/game/castling.py`
  - `src/game/capture_tracker.py`
  - `src/game/scoring.py`
  - `src/game/rules.py`
  - `tests/game/test_castling_helpers.py`
  - `tests/game/test_capture_tracker.py`
  - `tests/game/test_material_scoring.py`
  - `tests/game/test_game_rules_pipeline.py`
- **Modify**
  - `src/game/board.py`
  - `src/main.py`
  - `src/events.py`
  - `src/game/__init__.py`
  - Existing Phase 1 / Phase 2 tests as needed for import updates
- **Remove**
  - No file deletions are required in Phase 3. This phase should reduce coupling by extraction, not by large structural churn.

---

### Task 1: Extract Castling State and Rule Helpers

**Files:**
- Create: `src/game/castling.py`
- Modify: `src/game/board.py`
- Test: `tests/game/test_castling_helpers.py`

- [ ] **Step 1: Move `CastleRights` into a dedicated castling module**
  - **Target File(s):** `src/game/castling.py`
  - **Proposed Action:** Move the `CastleRights` data object out of `board.py` into `castling.py`, keeping it as a very small state container.
  - **OOP / Clean Code Justification:** Castling state is a focused rule concept and should not live inline inside a large game-state file.

- [ ] **Step 2: Add helper functions for castling-right updates**
  - **Target File(s):** `src/game/castling.py`
  - **Proposed Action:** Add small helpers such as `copy_castle_rights()`, `update_castle_rights_for_move()`, and `restore_castle_rights_from_log()` so `GameState` no longer owns the detailed branch logic directly.
  - **OOP / Clean Code Justification:** This extracts a mini-rule system into one clear place without introducing a complex service architecture.

- [ ] **Step 3: Localize castling inclusion control to king/castling logic**
  - **Target File(s):** `src/game/castling.py`, `src/game/board.py`, `src/pieces/base.py`, `src/pieces/standard.py`
  - **Proposed Action:** Keep the ability to exclude castling moves during attack-map calculations, but refactor so that this control is handled only by the king/castling path instead of being a meaningful concern for every piece subclass. If possible, simplify the generic piece API and let only king-move generation or castling helpers care about whether castling should be included.
  - **OOP / Clean Code Justification:** Castling is still required for correctness, but it is a king-specific rule and should not pollute the entire piece interface. This keeps the feature while reducing coupling and signature noise.

- [ ] **Step 4: Refactor `GameState` to delegate castling updates**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Replace the inline castling-right update logic in `GameState` with calls into `castling.py`, while keeping the public `GameState` API unchanged.
  - **OOP / Clean Code Justification:** `GameState` should coordinate rule helpers, not contain every branch itself.

- [ ] **Step 5: Add focused castling tests**
  - **Target File(s):** `tests/game/test_castling_helpers.py`
  - **Proposed Action:** Add tests for king movement, rook movement, rook capture, undo restoration of castling rights, and attack-map behavior that must exclude castling pseudo-moves.
  - **OOP / Clean Code Justification:** Castling is state-heavy and correctness-sensitive, so its extracted helper logic and localized inclusion control need direct regression coverage before Phase 4 event work can build on it.

### Task 2: Extract Capture Tracking from Board-State Inference

**Files:**
- Create: `src/game/capture_tracker.py`
- Modify: `src/game/board.py`
- Test: `tests/game/test_capture_tracker.py`

- [ ] **Step 1: Add a dedicated capture summary helper**
  - **Target File(s):** `src/game/capture_tracker.py`
  - **Proposed Action:** Create a helper object or helper functions that track and summarize captured pieces explicitly from move history instead of inferring them only from the live board grid.
  - **OOP / Clean Code Justification:** Capture state is a different responsibility from board movement and should be encapsulated separately, especially with future Fusion and revive mechanics.

- [ ] **Step 2: Initialize and update capture tracking from `GameState`**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Have `GameState` own one capture tracker instance and update it during move application and undo, using move snapshot data rather than rescanning the board each time.
  - **OOP / Clean Code Justification:** This reduces repeated board-walking logic and gives the game a reliable capture history for future advanced mechanics.

- [ ] **Step 3: Replace `get_captured_pieces()` implementation with tracker-backed logic**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Keep the same public method name if useful, but make it delegate to the capture tracker instead of calculating from board contents.
  - **OOP / Clean Code Justification:** This preserves caller simplicity while reducing the responsibility of `GameState`.

- [ ] **Step 4: Add capture tracker regression tests**
  - **Target File(s):** `tests/game/test_capture_tracker.py`
  - **Proposed Action:** Add tests for normal capture, en passant capture, promotion capture path compatibility, and undo restoration of captured summaries.
  - **OOP / Clean Code Justification:** Future Fusion and event destruction rules will depend on trustworthy capture accounting.

### Task 3: Extract Material Scoring into a Focused Helper

**Files:**
- Create: `src/game/scoring.py`
- Modify: `src/game/board.py`
- Test: `tests/game/test_material_scoring.py`

- [ ] **Step 1: Add a simple scoring helper**
  - **Target File(s):** `src/game/scoring.py`
  - **Proposed Action:** Create a helper such as `calculate_material_advantage(board_grid)` that relies on each piece’s `get_material_value()` instead of a local dictionary inside `GameState`.
  - **OOP / Clean Code Justification:** Material calculation should use the piece model, not central hardcoded piece value logic.

- [ ] **Step 2: Delegate score calculation from `GameState`**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Keep `get_material_advantage()` as the public entry point if desired, but make it call the new scoring helper.
  - **OOP / Clean Code Justification:** This keeps the external interface stable while moving the responsibility to a focused module.

- [ ] **Step 3: Add scoring regression tests**
  - **Target File(s):** `tests/game/test_material_scoring.py`
  - **Proposed Action:** Add tests for balanced starting position, simple advantage after a capture, and compatibility with piece metadata from Phase 2.
  - **OOP / Clean Code Justification:** This verifies that the new helper still reflects the board state correctly without coupling scoring to `GameState` internals.

### Task 4: Add a Post-Move Systems Pipeline

**Files:**
- Create: `src/game/rules.py`
- Modify: `src/game/board.py`
- Modify: `src/events.py`
- Test: `tests/game/test_game_rules_pipeline.py`

- [ ] **Step 1: Define a minimal post-move pipeline module**
  - **Target File(s):** `src/game/rules.py`
  - **Proposed Action:** Create a tiny rules module that defines the order of systems run after a real move, such as capture tracking, event updates, and future extension points.
  - **OOP / Clean Code Justification:** This gives later phases a clear seam for plugging in Fusion and event logic without stuffing more code into `make_move()`.

- [ ] **Step 2: Refactor `GameState._finalize_move()` to call the rules pipeline**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Keep `GameState` as the coordinator, but replace direct inline post-move calls with a call into the new pipeline module.
  - **OOP / Clean Code Justification:** This removes hidden coupling in the turn lifecycle while keeping the flow easy to follow.

- [ ] **Step 3: Keep the current event update behavior compatible**
  - **Target File(s):** `src/events.py`, `src/game/rules.py`
  - **Proposed Action:** Route the existing event-manager update through the post-move pipeline without redesigning the event system yet.
  - **OOP / Clean Code Justification:** Phase 3 should create the extension seam now, while Phase 4 later improves the event architecture itself.

- [ ] **Step 4: Add tests for post-move pipeline order**
  - **Target File(s):** `tests/game/test_game_rules_pipeline.py`
  - **Proposed Action:** Add tests confirming real moves trigger the pipeline and simulated move generation does not accidentally run real side systems like event updates or tracker commits.
  - **OOP / Clean Code Justification:** This protects `get_valid_moves()` from side effects and makes the rule flow explicit.

### Task 5: Update Existing Call Sites to Use the New Game Helpers

**Files:**
- Modify: `src/game/board.py`
- Modify: `src/main.py`
- Modify: `src/game/__init__.py`
- Existing tests: update imports if needed

- [ ] **Step 1: Expose only the needed game-layer imports**
  - **Target File(s):** `src/game/__init__.py`
  - **Proposed Action:** Re-export the stable game-layer classes or helpers that external modules actually need, without turning `__init__.py` into a dumping ground.
  - **OOP / Clean Code Justification:** A small stable import surface reduces coupling to file layout while keeping the package easy to understand.

- [ ] **Step 2: Keep `main.py` dependent on public `GameState` methods only**
  - **Target File(s):** `src/main.py`
  - **Proposed Action:** Make sure the UI continues to ask `GameState` for captured summaries and score summaries through public methods, not by reaching into new helper objects directly.
  - **OOP / Clean Code Justification:** This preserves encapsulation between the domain layer and the UI layer.

- [ ] **Step 3: Remove dead or duplicate helper code from `board.py`**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** After extraction, delete redundant inline logic that has been replaced by castling, scoring, capture-tracker, or rules-pipeline helpers.
  - **OOP / Clean Code Justification:** Extraction only helps if the old duplicated responsibility is actually removed from the coordinator.

### Task 6: Verify the Reduced-Coupling Baseline

**Files:**
- Test: `tests/game/test_castling_helpers.py`
- Test: `tests/game/test_capture_tracker.py`
- Test: `tests/game/test_material_scoring.py`
- Test: `tests/game/test_game_rules_pipeline.py`
- Existing tests: `tests/game/test_board_helpers.py`, `tests/game/test_move_and_undo.py`, `tests/game/test_pawn_boundaries.py`, `tests/game/test_board_piece_creation.py`, `tests/pieces/*.py`
- Modify: `src/game/castling.py`
- Modify: `src/game/capture_tracker.py`
- Modify: `src/game/scoring.py`
- Modify: `src/game/rules.py`

- [ ] **Step 1: Run the full game-domain regression suite**
  - **Target File(s):** all Phase 1, Phase 2, and Phase 3 tests
  - **Proposed Action:** Run the focused new tests plus the earlier game and piece tests to confirm the extractions did not change behavior.
  - **OOP / Clean Code Justification:** Coupling reductions are only successful if the gameplay baseline remains stable.

- [ ] **Step 2: Add concise docstrings to new helper modules**
  - **Target File(s):** `src/game/castling.py`, `src/game/capture_tracker.py`, `src/game/scoring.py`, `src/game/rules.py`
  - **Proposed Action:** Add short docstrings that describe each helper module’s single responsibility and how `GameState` uses it.
  - **OOP / Clean Code Justification:** This makes the extracted architecture easier to present and reason about in an OOP course project.

- [ ] **Step 3: Confirm `GameState` is smaller but still the coordinator**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Before closing the phase, review the file to ensure `GameState` still coordinates move flow but no longer owns detailed castling, capture-summary, scoring, and post-move rule logic inline.
  - **OOP / Clean Code Justification:** The goal is not to eliminate `GameState`, but to stop it from growing into a God Object.

---

## Why This Phase 3 Structure Is Recommended

- [ ] **Use helper modules, not heavyweight manager classes**
  - **Target File(s):** `src/game/castling.py`, `src/game/capture_tracker.py`, `src/game/scoring.py`, `src/game/rules.py`
  - **Proposed Action:** Favor a few focused helper modules or very small helper objects instead of building a large service layer.
  - **OOP / Clean Code Justification:** This respects the project’s “NO OVERENGINEERING” rule while still reducing coupling in a meaningful way.

- [ ] **Preserve `GameState` as the single coordination point**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Keep the main turn lifecycle readable from `GameState`, but make the details of each subsystem live elsewhere.
  - **OOP / Clean Code Justification:** This keeps the architecture easy for a student to explain while still applying SRP and basic Open/Closed improvements.

- [ ] **Create extension seams before Fusion and Event expansion**
  - **Target File(s):** `src/game/rules.py`, `src/game/capture_tracker.py`
  - **Proposed Action:** Finish the post-move pipeline and explicit trackers now so later Fusion and Special Event phases can reuse them instead of reworking `GameState` again.
  - **OOP / Clean Code Justification:** This lowers rework and aligns the structure with the future requirements in `mode.md`.

- [ ] **Keep castling as a required rule, but scope it tightly**
  - **Target File(s):** `src/game/castling.py`, `src/pieces/standard.py`
  - **Proposed Action:** Preserve the ability to include or exclude castling where the rules engine needs it, but avoid making castling a first-class concern of non-king pieces.
  - **OOP / Clean Code Justification:** This keeps a must-have chess rule intact while making the design cleaner and more focused.
