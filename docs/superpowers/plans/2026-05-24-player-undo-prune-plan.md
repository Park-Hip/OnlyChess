# Player Undo Removal Prune Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the player-facing undo feature while preserving correct chess rule simulation, event timing, capture summaries, and a clean OOP-friendly code structure.

**Architecture:** Keep rollback support only as an internal engine tool for legal-move simulation inside `GameState.get_valid_moves()`. Remove UI-triggered undo, event snapshot restoration, and other code that exists only to support player undo. After cleanup, the codebase should read more clearly: player input no longer knows about undo, the event system no longer stores restoration snapshots, and move rollback becomes an internal implementation detail rather than a public gameplay feature.

**Tech Stack:** Python, Pygame, `unittest`, current `src/` package structure

---

## Planned File and Folder Structure After Player Undo Removal

```text
docs/
├── architecture-current-baseline.md
└── superpowers/
    └── plans/
        ├── 2026-05-23-chess-fusion-refactor-plan.md
        ├── 2026-05-23-phase-1-core-stabilization-plan.md
        ├── 2026-05-23-phase-2-clean-piece-model-plan.md
        ├── 2026-05-23-phase-3-reduce-gamestate-coupling-plan.md
        ├── 2026-05-23-phase-4-event-system-refactor-plan.md
        ├── 2026-05-24-phase-5-ui-layer-cleanup-plan.md
        ├── 2026-05-24-phase-7-documentation-and-verification-plan.md
        └── 2026-05-24-player-undo-prune-plan.md

src/
├── main.py                                  # No player undo hotkey branch
├── events/
│   ├── __init__.py                          # No event snapshot export
│   ├── base.py                              # Base event contract only
│   ├── gia_xang_tang.py
│   ├── manager.py                           # Warning/execution timing only
│   └── registry.py
├── game/
│   ├── board.py                             # Internal rollback kept for move simulation
│   ├── capture_tracker.py                   # No real-move undo entry removal method
│   ├── castling.py
│   ├── move.py                              # Minimal rollback fields only
│   ├── rules.py
│   ├── scoring.py
│   └── state_helpers.py
└── ui/
    ├── assets.py
    ├── input_handler.py
    ├── promotion_menu.py
    ├── render_board.py
    └── render_panels.py

tests/
├── events/
│   ├── test_event_base_contract.py          # Snapshot assertions removed or rewritten
│   ├── test_event_manager_flow.py
│   ├── test_event_registry.py
│   └── test_gia_xang_tang_event.py
├── game/
│   ├── test_capture_tracker.py              # No player-undo capture-summary test
│   ├── test_castling_helpers.py             # Internal rollback assertions only
│   ├── test_game_rules_pipeline.py
│   └── test_move_and_undo.py                # Rename or rewrite around internal rollback
└── ui/
    └── ...
```

## File Operation Summary

- **Delete**
  - `tests/events/test_event_snapshot_restore.py`
- **Modify**
  - `README.md`
  - `docs/architecture-current-baseline.md`
  - `src/main.py`
  - `src/events/__init__.py`
  - `src/events/base.py`
  - `src/events/manager.py`
  - `src/game/board.py`
  - `src/game/capture_tracker.py`
  - `src/game/move.py`
  - `tests/events/test_event_base_contract.py`
  - `tests/events/test_event_manager_flow.py`
  - `tests/game/test_capture_tracker.py`
  - `tests/game/test_castling_helpers.py`
  - `tests/game/test_game_rules_pipeline.py`
  - `tests/game/test_move_and_undo.py`
- **Keep As-Is or Nearly As-Is**
  - `src/events/gia_xang_tang.py`
  - `src/events/registry.py`
  - `src/game/castling.py`
  - `src/game/rules.py`
  - `src/ui/*` except `src/main.py`

---

## Cleanliness Assessment Before and After

### Current Situation

- The codebase is already fairly clean at the package level.
- The main remaining conceptual leak is that one word, `undo`, currently means two different things:
  - player-facing gameplay undo from the UI
  - internal engine rollback used during move validation
- That overlap makes `GameState.undo_move()` and the event manager look more public and feature-heavy than they really need to be.

### Expected Cleanliness After This Prune

- `src/main.py` becomes simpler because player input no longer coordinates event restoration plus rollback.
- `src/events/manager.py` becomes cleaner because it only handles timing, warnings, execution, and next-event queueing.
- `src/events/base.py` becomes a truer base contract because it no longer carries snapshot hooks that only exist for undo restoration.
- `src/game/move.py` becomes easier to explain because it stores rollback state for simulation, not because the player can rewind the game.
- `src/game/board.py` still needs rollback logic, but it can be renamed and documented as an internal simulation helper instead of a user feature.

### Important Constraint

Player undo can be removed safely. Full rollback cannot be removed yet, because `GameState.get_valid_moves()` currently depends on move-then-rollback simulation.

---

## Task 1: Remove the Player Undo Entry Point

**Files:**
- Modify: `src/main.py`
- Test: `tests/game/test_game_rules_pipeline.py`
- Test: `tests/ui/test_render_board.py`

- [ ] **Step 1: Remove the keyboard branch that triggers player undo**
  - **Target File(s):** `src/main.py:95-101`
  - **Prune:** delete the `p.K_z` branch that calls `game_state.event_manager.handle_undo()`, `game_state.undo_move()`, and `game_state.event_manager.sync_state()`.
  - **Why it is safe:** This branch is the only player-facing entry point for undo. No other UI helper calls these methods directly.

- [ ] **Step 2: Keep move flow, promotion flow, and redraw flow unchanged**
  - **Target File(s):** `src/main.py`
  - **Keep:** `process_move_attempt(...)`, `handle_promotion_click(...)`, `move_made` refresh logic, and event overlay drawing.
  - **Why it must stay:** These behaviors are unrelated to player undo and still define the normal game loop.

- [ ] **Step 3: Verify no UI code still assumes player undo exists**
  - **Target File(s):** `src/ui/*.py`, `tests/ui/*.py`
  - **Check:** no labels, docstrings, or tests should mention `Z`, undo hotkeys, or player rewind behavior.
  - **Expected cleanliness gain:** UI input handling becomes strictly about selecting and making moves.

## Task 2: Prune Event Snapshot Restoration Code

**Files:**
- Modify: `src/events/base.py`
- Modify: `src/events/manager.py`
- Modify: `src/events/__init__.py`
- Delete: `tests/events/test_event_snapshot_restore.py`
- Modify: `tests/events/test_event_base_contract.py`
- Modify: `tests/events/test_event_manager_flow.py`

- [ ] **Step 1: Remove the event snapshot model**
  - **Target File(s):** `src/events/base.py:8-29`
  - **Prune:** delete `EventStateSnapshot` entirely.
  - **Why it is safe:** It exists only to restore event-layer state after player undo.

- [ ] **Step 2: Remove snapshot-specific event hooks from the base event contract**
  - **Target File(s):** `src/events/base.py:57-63`
  - **Prune:** delete `build_snapshot_data()` and `restore_from_snapshot_data()`.
  - **Why it is safe:** No remaining event flow needs per-event restoration payloads after player undo is removed.

- [ ] **Step 3: Remove snapshot storage and restoration flow from the event manager**
  - **Target File(s):** `src/events/manager.py:16-17`
  - **Prune:** remove `self.snapshots` and `self.restore_snapshot`.
  - **Target File(s):** `src/events/manager.py:26-37`
  - **Prune:** delete `_create_snapshot()`.
  - **Target File(s):** `src/events/manager.py:50`
  - **Prune:** stop appending event snapshots before execution.
  - **Target File(s):** `src/events/manager.py:59-99`
  - **Prune:** delete `handle_undo()` and `sync_state()`.
  - **Why it is safe:** All of this code exists to reconstruct warnings or board state after a player-initiated rewind.

- [ ] **Step 4: Clean the public event package surface**
  - **Target File(s):** `src/events/__init__.py:3-15`
  - **Prune:** remove `EventStateSnapshot` from imports and `__all__`.
  - **Why it is safe:** The snapshot class should disappear from the public API along with the feature it supports.

- [ ] **Step 5: Remove snapshot-only tests and rewrite the remaining event tests around live flow**
  - **Target File(s):** `tests/events/test_event_snapshot_restore.py`
  - **Prune:** delete the file.
  - **Target File(s):** `tests/events/test_event_base_contract.py:34-55`
  - **Prune or rewrite:** remove assertions about snapshot payload helpers and snapshot models.
  - **Target File(s):** `tests/events/test_event_manager_flow.py:43`
  - **Prune or rewrite:** remove the assertion that `manager.snapshots` grows.
  - **Expected cleanliness gain:** Event tests describe only active gameplay behavior, not restoration mechanics.

## Task 3: Simplify Move and GameState Rollback to Internal-Only Responsibility

**Files:**
- Modify: `src/game/board.py`
- Modify: `src/game/move.py`
- Modify: `tests/game/test_move_and_undo.py`
- Modify: `tests/game/test_castling_helpers.py`

- [ ] **Step 1: Keep rollback support because legal move generation still depends on it**
  - **Target File(s):** `src/game/board.py:233-247`
  - **Keep:** `make_move(...)` plus reversal during `get_valid_moves()`.
  - **Reason:** This is engine simulation, not player undo.

- [ ] **Step 2: Rename or redocument rollback methods so they read as internal simulation helpers**
  - **Target File(s):** `src/game/board.py:174-231`
  - **Preferred cleanup:** either rename `undo_move()` to something like `_rollback_last_move()` and update its internal callers, or keep the method name but rewrite the docstring to state clearly that it is an internal rollback helper used by move validation.
  - **Why this helps:** The codebase becomes more honest about responsibility without introducing advanced patterns.

- [ ] **Step 3: Keep only rollback fields on `Move` that still serve simulation**
  - **Target File(s):** `src/game/move.py:42-53`
  - **Likely keep:** `enpassant_possible_prev`, `moved_piece_prev_pos`, `moved_piece_prev_has_moved`, `captured_piece_prev_pos`, `captured_piece_prev_has_moved`, `rook_moved`, `rook_start_pos`, `rook_end_pos`, `rook_prev_has_moved`.
  - **Review carefully:** `promoted_to_piece` may still be removable if nothing outside tests or future UI needs it after promotion completes.
  - **Why this is a review step instead of blind deletion:** Most of these fields are still needed for internal rollback of special moves.

- [ ] **Step 4: Rewrite rollback-focused tests to describe engine simulation rather than user undo**
  - **Target File(s):** `tests/game/test_move_and_undo.py`
  - **Preferred cleanup:** rename the file to something like `tests/game/test_move_simulation_rollback.py` or keep the file but rewrite the docstrings and test names away from user undo language.
  - **Target File(s):** `tests/game/test_castling_helpers.py:66-74`
  - **Rewrite:** frame this as restoration after simulated rollback, not as a player feature.
  - **Expected cleanliness gain:** Tests explain the real purpose of reversal logic.

## Task 4: Remove Real-Move Capture Summary Undo Support

**Files:**
- Modify: `src/game/capture_tracker.py`
- Modify: `src/game/board.py`
- Modify: `tests/game/test_capture_tracker.py`

- [ ] **Step 1: Remove capture tracker rollback for real moves**
  - **Target File(s):** `src/game/capture_tracker.py:23-33`
  - **Prune:** delete `undo_move(self, move)`.
  - **Why it is safe:** Capture summaries are only recorded for `is_real_move=True`, and without player undo those summaries should not be rewound.

- [ ] **Step 2: Remove the real-move capture rollback call**
  - **Target File(s):** `src/game/board.py:177-180`
  - **Prune:** delete the `if move.is_real_move: self.capture_tracker.undo_move(move)` branch.
  - **Why it is safe:** Internal simulated moves do not call `record_move`, so rollback does not need to repair capture summaries for simulations.

- [ ] **Step 3: Keep capture tracking for actual captures**
  - **Target File(s):** `src/game/rules.py:4-8`
  - **Keep:** `game_state.capture_tracker.record_move(move)`.
  - **Why it must stay:** The side panels still need captured-piece summaries during normal play.

- [ ] **Step 4: Remove only the tests that prove capture summary rewind**
  - **Target File(s):** `tests/game/test_capture_tracker.py:25-35`
  - **Prune:** delete the test that expects capture summaries to disappear after undo.
  - **Keep:** the tests for normal capture, en passant capture, and promotion capture summaries.

## Task 5: Update Documentation So the Baseline Matches the New Feature Set

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture-current-baseline.md`

- [ ] **Step 1: Remove player undo from the advertised feature list**
  - **Target File(s):** `README.md:8-10`
  - **Prune:** remove `- undo support`.
  - **Why it is safe:** The README should only list user-visible supported features.

- [ ] **Step 2: Replace undo language with internal rollback language where needed**
  - **Target File(s):** `docs/architecture-current-baseline.md:10`
  - **Rewrite:** change phrasing like “move execution, undo” into “move execution and internal legal-move simulation rollback” or equivalent.
  - **Target File(s):** `docs/architecture-current-baseline.md:21`
  - **Rewrite:** remove “undo-related event restoration” from the event manager description.

- [ ] **Step 3: Clean regression command references if test files are renamed or deleted**
  - **Target File(s):** `README.md:36`
  - **Update:** remove `tests.events.test_event_snapshot_restore` and rename `tests.game.test_move_and_undo` if the file changes.
  - **Expected cleanliness gain:** Docs stop teaching a feature that no longer exists.

## Task 6: Final Verification and Cleanliness Review

**Files:**
- Verify: `src/main.py`
- Verify: `src/events/base.py`
- Verify: `src/events/manager.py`
- Verify: `src/game/board.py`
- Verify: `src/game/move.py`
- Verify: `src/game/capture_tracker.py`
- Verify: `README.md`
- Verify: `docs/architecture-current-baseline.md`

- [ ] **Step 1: Re-run the focused regression suite after pruning**
  - **Run:** `uv run python -m unittest tests.events.test_event_base_contract tests.events.test_event_manager_flow tests.events.test_event_registry tests.events.test_gia_xang_tang_event tests.game.test_capture_tracker tests.game.test_castling_helpers tests.game.test_game_rules_pipeline tests.game.test_board_helpers tests.game.test_board_piece_creation tests.game.test_material_scoring tests.game.test_pawn_boundaries tests.pieces.test_piece_metadata tests.pieces.test_piece_registry tests.pieces.test_piece_extension_hooks tests.ui.test_assets tests.ui.test_promotion_menu tests.ui.test_input_handler tests.ui.test_render_board tests.ui.test_render_panels -v`
  - **Expected:** PASS without any player-undo-specific tests remaining.

- [ ] **Step 2: Do one manual smoke run**
  - **Run:** `uv run python run.py`
  - **Check manually:** pieces still move, promotion still works, captured-piece panels still update, event warnings still appear, and there is no player undo behavior on `Z`.

- [ ] **Step 3: Confirm the final cleanliness outcome**
  - **Checklist:**
    - `src/main.py` has no player undo branch.
    - `src/events/manager.py` has no snapshot storage or restore logic.
    - `src/events/base.py` contains only the event contract actually used at runtime.
    - `src/game/board.py` still supports rollback, but its docs and naming present it as internal simulation support.
    - docs and tests no longer describe rewind as a player feature.

---

## Recommended Prune Order

1. Remove the UI entry point in `src/main.py`.
2. Remove event snapshot restoration code.
3. Simplify capture tracker rollback for real moves.
4. Reframe `GameState` rollback as internal simulation support.
5. Update tests and docs last so they reflect the final structure.

## Prune Risk Summary

- **Low risk**
  - `src/main.py` player undo hotkey branch
  - `tests/events/test_event_snapshot_restore.py`
  - event snapshot exports in `src/events/__init__.py`
  - `CaptureTracker.undo_move()`

- **Medium risk**
  - removing snapshot hooks from `ChessEvent`
  - simplifying `EventManager` without affecting turn-9 warning and turn-10 execution flow
  - deciding whether `Move.promoted_to_piece` is still needed

- **Do not prune yet**
  - `GameState` rollback itself
  - rollback-critical move fields used by en passant, castling, king position restoration, and `has_moved` restoration
  - `move_log`, because it still supports event timing and last-move board highlights

## Final Cleanliness Verdict

After this prune, the codebase should be **cleaner, more honest, and easier to explain**:

- The UI no longer exposes a rewind feature.
- The event system becomes narrower and more focused.
- The move model still supports rollback, but only for rule validation.
- The remaining reversal code is justified by chess legality, not by a user-facing control.

This is a good cleanup if the project scope no longer wants player undo but still wants simple, correct chess rules without overengineering a separate simulation board.
