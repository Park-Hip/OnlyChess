# Code Review Follow-Up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the highest-risk correctness issues first, then clean up rollback naming, code clarity, and extension seams so the project stays simple, correct, and ready for future `mode.md` features.

**Architecture:** Keep the current package structure (`game`, `pieces`, `events`, `ui`) and avoid advanced patterns. This plan focuses on small, explainable improvements: fix concrete bugs, reduce leftover undo terminology, centralize a few fragile rules, and add lightweight seams so Fusion, AP, abilities, and richer events can be integrated with fewer edits to `GameState`.

**Tech Stack:** Python 3.12, Pygame, `unittest`, current `src/` package layout

---

## Planned File and Folder Structure After This Follow-Up

```text
docs/
└── superpowers/
    └── plans/
        └── 2026-05-24-code-review-followup-phased-plan.md

src/
├── constants.py                       # Domain constants only or clearly-separated constants
├── main.py                            # Main loop with safer promotion flow
├── events/
│   ├── base.py
│   ├── gia_xang_tang.py               # Event behavior compatible with castling/event rules
│   ├── manager.py                     # Clearer event-pool and turn/event timing behavior
│   └── registry.py
├── game/
│   ├── board.py                       # GameState plus internal rollback, move validation, turn helpers
│   ├── capture_tracker.py             # Captured-piece records shaped for UI and future rules
│   ├── castling.py                    # Castling-right validation still isolated here
│   ├── move.py                        # Internal rollback/move identity kept simple but explicit
│   ├── rules.py                       # Post-move pipeline
│   ├── scoring.py
│   └── state_helpers.py
├── pieces/
│   ├── base.py
│   ├── registry.py
│   └── standard.py
└── ui/
    ├── input_handler.py               # Safer board-boundary input handling
    ├── promotion_menu.py              # Promotion click policy
    ├── render_board.py                # Board rendering using safer board access where practical
    └── render_panels.py               # Shared event countdown usage

tests/
├── events/
│   ├── test_event_manager_flow.py
│   └── test_gia_xang_tang_event.py
├── game/
│   ├── test_castling_helpers.py
│   ├── test_capture_tracker.py
│   ├── test_game_rules_pipeline.py
│   └── test_move_and_undo.py          # May be renamed to rollback-focused naming
└── ui/
    ├── test_input_handler.py
    ├── test_promotion_menu.py
    └── test_render_panels.py
```

---

## Recommended Execution Order

1. **Phase 1:** Fix correctness and regression risks that can break gameplay now.
2. **Phase 2:** Remove leftover undo terminology and tighten internal rollback boundaries.
3. **Phase 3:** Apply small clean-code refactors that reduce duplication and coupling.
4. **Phase 4:** Prepare turn/event/capture seams needed by `mode.md`.
5. **Phase 5:** Apply final OOP polish so future features land in smaller, clearer units.

---

## Phase 1: Correctness and Regression Safety

**Purpose:** Fix the issues most likely to cause crashes or illegal moves before doing any design cleanup.

### Task 1: Fix Board Click Boundary Safety

**Files:**
- Modify: `src/ui/input_handler.py`
- Test: `tests/ui/test_input_handler.py`

- [ ] **Step 1: Add a failing test for clicks outside board width**

```python
def test_board_click_rejects_x_positions_outside_board_width(self):
    self.assertFalse(is_board_click((-1, INFO_PANEL_HEIGHT + 10)))
    self.assertFalse(is_board_click((BOARD_COLS * SQ_SIZE, INFO_PANEL_HEIGHT + 10)))
```

- [ ] **Step 2: Run the focused test to verify current failure**

Run: `uv run python -m unittest tests.ui.test_input_handler -v`
Expected: FAIL on the new boundary assertions.

- [ ] **Step 3: Update `is_board_click()` to validate both axes**

```python
def is_board_click(
    location,
    square_size=SQ_SIZE,
    info_panel_height=INFO_PANEL_HEIGHT,
    board_height=BOARD_HEIGHT,
    board_size=BOARD_SIZE,
):
    board_width = board_size * square_size
    return (
        0 <= location[0] < board_width
        and info_panel_height <= location[1] < info_panel_height + board_height
    )
```

- [ ] **Step 4: Keep downstream handlers unchanged unless tests prove more guarding is needed**

```python
if not is_board_click(location):
    return
```

- [ ] **Step 5: Re-run the input handler tests**

Run: `uv run python -m unittest tests.ui.test_input_handler -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/ui/input_handler.py tests/ui/test_input_handler.py
git commit -m "fix: guard board clicks by x and y bounds"
```

### Task 2: Prevent Illegal Castling After Rook Mutation or Removal

**Files:**
- Modify: `src/pieces/standard.py`
- Test: `tests/game/test_castling_helpers.py`
- Test: `tests/events/test_gia_xang_tang_event.py`

- [ ] **Step 1: Add a failing castling regression test**

```python
def test_castle_requires_actual_rook_on_corner(self):
    game_state = GameState()
    game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
    king = King(WHITE, (7, 4))
    fake_corner_piece = Knight(WHITE, (7, 7))
    game_state.board.grid[7][4] = king
    game_state.board.grid[7][7] = fake_corner_piece
    game_state.white_king_pos = (7, 4)

    moves = king.get_castle_moves(game_state)

    self.assertEqual(moves, [])
```

- [ ] **Step 2: Add an event-specific regression test**

```python
def test_gia_xang_tang_prevents_future_castling_from_transformed_corner(self):
    game_state = GameState()
    for col in (5, 6):
        game_state.board.set_piece_at(7, col, None)

    event = GiaXangTang(game_state)
    event.execute()

    king = game_state.board.get_piece_at(7, 4)
    self.assertEqual(king.get_castle_moves(game_state), [])
```

- [ ] **Step 3: Run the targeted tests to verify failure**

Run: `uv run python -m unittest tests.game.test_castling_helpers tests.events.test_gia_xang_tang_event -v`
Expected: FAIL because castling is still generated.

- [ ] **Step 4: Add explicit rook validation in `King.get_castle_moves()`**

```python
corner_piece = gs.board.get_piece_at(r, BOARD_COLS - 1)
if (
    corner_piece is not None
    and corner_piece.color == self.color
    and corner_piece.get_piece_code() == ROOK_CODE
):
    if gs.board.get_piece_at(r, c + 1) is None and gs.board.get_piece_at(r, c + 2) is None:
        if not gs.square_under_attack(r, c + 1) and not gs.square_under_attack(r, c + 2):
            moves.append(Move((r, c), (r, c + 2), gs.board.grid, is_castle_move=True))
```

- [ ] **Step 5: Mirror the same explicit rook check on queen side**

```python
corner_piece = gs.board.get_piece_at(r, 0)
if (
    corner_piece is not None
    and corner_piece.color == self.color
    and corner_piece.get_piece_code() == ROOK_CODE
):
    if (
        gs.board.get_piece_at(r, c - 1) is None
        and gs.board.get_piece_at(r, c - 2) is None
        and gs.board.get_piece_at(r, c - 3) is None
    ):
        if not gs.square_under_attack(r, c - 1) and not gs.square_under_attack(r, c - 2):
            moves.append(Move((r, c), (r, c - 2), gs.board.grid, is_castle_move=True))
```

- [ ] **Step 6: Re-run the targeted tests**

Run: `uv run python -m unittest tests.game.test_castling_helpers tests.events.test_gia_xang_tang_event -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/pieces/standard.py tests/game/test_castling_helpers.py tests/events/test_gia_xang_tang_event.py
git commit -m "fix: require real rook for castling"
```

### Task 3: Make Promotion Click Flow Safer

**Files:**
- Modify: `src/main.py`
- Test: `tests/ui/test_promotion_menu.py`

- [ ] **Step 1: Add a failing test for outside-menu clicks during promotion**

```python
def test_outside_click_does_not_resolve_promotion_choice(self):
    rect = get_promotion_menu_rect()
    self.assertIsNone(resolve_promotion_click((rect.x - 5, rect.y), rect))
```

- [ ] **Step 2: Add a small integration assertion in a new or existing UI flow test**

```python
input_state.promotion_move_pending = object()
result = handle_promotion_click(input_state, game_state, (0, 0))
self.assertFalse(result)
self.assertIsNotNone(input_state.promotion_move_pending)
```

- [ ] **Step 3: Run focused tests to confirm current behavior mismatch**

Run: `uv run python -m unittest tests.ui.test_promotion_menu -v`
Expected: PASS for geometry helper but integration test should fail until `handle_promotion_click()` changes.

- [ ] **Step 4: Preserve pending promotion when click is outside the menu**

```python
choice = resolve_promotion_click(mouse_pos)
if choice is None:
    return False

game_state.make_move(input_state.promotion_move_pending, choice, is_real_move=True)
clear_promotion_pending(input_state)
reset_selection_state(input_state)
return True
```

- [ ] **Step 5: Re-run the promotion tests**

Run: `uv run python -m unittest tests.ui.test_promotion_menu -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/main.py tests/ui/test_promotion_menu.py
git commit -m "fix: keep promotion choice pending on outside click"
```

### Task 4: Make Empty Event Pools Explicitly Supported

**Files:**
- Modify: `src/events/manager.py`
- Test: `tests/events/test_event_manager_flow.py`

- [ ] **Step 1: Add a failing test for an intentionally empty event pool**

```python
def test_empty_event_pool_remains_empty(self):
    game_state = GameState()
    manager = EventManager(game_state, event_pool=[])
    self.assertEqual(manager.event_pool, [])
    self.assertIsNone(manager.queued_event)
    self.assertIsNone(manager.queued_event_key)
```

- [ ] **Step 2: Run the event manager tests to verify current failure**

Run: `uv run python -m unittest tests.events.test_event_manager_flow -v`
Expected: FAIL because the default event is still injected.

- [ ] **Step 3: Treat `None` differently from `[]`**

```python
self.event_pool = ["gia_xang_tang"] if event_pool is None else list(event_pool)
if self.event_pool:
    self._queue_next_event()
```

- [ ] **Step 4: Guard `_queue_next_event()` callers against empty pools**

```python
if not self.event_pool:
    self.queued_event = None
    self.queued_event_key = None
    return
```

- [ ] **Step 5: Re-run the event manager tests**

Run: `uv run python -m unittest tests.events.test_event_manager_flow -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/events/manager.py tests/events/test_event_manager_flow.py
git commit -m "fix: support intentionally empty event pools"
```

---

## Phase 2: Finish the Undo-Removal Cleanup

**Purpose:** Remove conceptual leftovers from the old player undo feature while keeping internal rollback simple and explicit.

### Task 5: Rename Rollback-Focused Tests and Language

**Files:**
- Modify: `src/game/board.py`
- Modify: `src/game/move.py`
- Modify: `tests/game/test_move_and_undo.py`
- Modify: `README.md`

- [ ] **Step 1: Rewrite rollback comments/docstrings away from player undo language**

```python
def undo_move(self):
    """Roll back the most recent move for internal move simulation."""
```

```python
"""Move object for representing chess actions and rollback state."""
```

- [ ] **Step 2: Rename the test class to match current behavior**

```python
class MoveRollbackTests(unittest.TestCase):
    """Lock in move-state bookkeeping used by internal rollback."""
```

- [ ] **Step 3: Update README wording if it still sounds user-facing**

```markdown
- internal move-simulation rollback for legal move validation
```

- [ ] **Step 4: Run the rollback and README-adjacent regression tests**

Run: `uv run python -m unittest tests.game.test_move_and_undo tests.game.test_castling_helpers tests.game.test_game_rules_pipeline -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/game/board.py src/game/move.py tests/game/test_move_and_undo.py README.md
git commit -m "refactor: clarify internal rollback terminology"
```

### Task 6: Decide Whether to Rename `undo_move()` to a Private Rollback Helper

**Files:**
- Modify: `src/game/board.py`
- Modify: `tests/game/test_move_and_undo.py`
- Modify: `tests/game/test_castling_helpers.py`

- [ ] **Step 1: Search for every `undo_move()` call site**

Run: `rg -n "undo_move\\(" src tests`
Expected: only internal engine use plus rollback tests.

- [ ] **Step 2: If call sites are fully internal, rename the method**

```python
def _rollback_last_move(self):
    """Roll back the most recent simulated move."""
```

- [ ] **Step 3: Update the internal validation call**

```python
self._rollback_last_move()
```

- [ ] **Step 4: Update tests to call the new name only where rollback is being asserted directly**

```python
game_state._rollback_last_move()
```

- [ ] **Step 5: Run focused rollback tests**

Run: `uv run python -m unittest tests.game.test_move_and_undo tests.game.test_castling_helpers -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/game/board.py tests/game/test_move_and_undo.py tests/game/test_castling_helpers.py
git commit -m "refactor: make rollback helper internal to GameState"
```

---

## Phase 3: Small Clean-Code and Coupling Improvements

**Purpose:** Reduce duplication and weak boundaries without changing the simple architecture style.

### Task 7: Remove Duplicate Event Countdown Ownership

**Files:**
- Modify: `src/ui/render_panels.py`
- Modify: `tests/ui/test_render_panels.py`

- [ ] **Step 1: Decide the single countdown owner**

```python
event_turns_remaining = game_state.get_turns_to_next_event()
```

- [ ] **Step 2: Remove the unused helper if nothing else needs it**

```python
# delete calculate_turns_to_event()
```

- [ ] **Step 3: Rewrite tests around the GameState-facing API or the remaining helper**

```python
self.assertEqual(game_state.get_turns_to_next_event(), 10)
```

- [ ] **Step 4: Run the panel tests**

Run: `uv run python -m unittest tests.ui.test_render_panels -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/render_panels.py tests/ui/test_render_panels.py
git commit -m "refactor: keep event countdown logic in one place"
```

### Task 8: Reduce Direct `board.grid` Access in UI Entry Points

**Files:**
- Modify: `src/ui/input_handler.py`
- Modify: `src/ui/render_board.py`

- [ ] **Step 1: Replace direct reads with board helpers where practical**

```python
piece = game_state.board.get_piece_at(row, col)
```

- [ ] **Step 2: Keep full-grid iteration only where rendering the full board is simpler**

```python
draw_pieces(screen, game_state.board.grid, images, selected_square if dragging else ())
```

- [ ] **Step 3: Re-run the UI tests**

Run: `uv run python -m unittest tests.ui.test_input_handler tests.ui.test_render_board -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/ui/input_handler.py src/ui/render_board.py
git commit -m "refactor: use board access helpers in ui read paths"
```

### Task 9: Separate Domain and UI Constants More Clearly

**Files:**
- Modify: `src/constants.py`
- Create or Modify: `src/ui/__init__.py`
- Modify: `src/ui/render_board.py`
- Modify: `src/ui/render_panels.py`
- Modify: `src/ui/input_handler.py`

- [ ] **Step 1: Move only Pygame color constants out of the domain constants module**

```python
# src/ui/ui_constants.py
import pygame as p

COLOR_LIGHT = p.Color("white")
COLOR_DARK = p.Color("gray")
PANEL_BACKGROUND = "#2f2f2f"
```

- [ ] **Step 2: Keep board dimensions and piece codes in `src/constants.py`**

```python
BOARD_SIZE = 8
BOARD_ROWS = BOARD_SIZE
BOARD_COLS = BOARD_SIZE
```

- [ ] **Step 3: Update UI imports only**

```python
from .ui_constants import COLOR_DARK, COLOR_LIGHT, PANEL_BACKGROUND
```

- [ ] **Step 4: Run the UI regression tests**

Run: `uv run python -m unittest tests.ui.test_assets tests.ui.test_render_board tests.ui.test_render_panels tests.ui.test_input_handler -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/constants.py src/ui/ui_constants.py src/ui/render_board.py src/ui/render_panels.py src/ui/input_handler.py
git commit -m "refactor: separate ui constants from domain constants"
```

---

## Phase 4: Integration Readiness for `mode.md`

**Purpose:** Add the smallest possible seams that will support Fusion, AP, abilities, and persistent events without reopening the same core logic repeatedly.

### Task 10: Centralize Turn Progress and Full-Turn Detection

**Files:**
- Modify: `src/game/board.py`
- Modify: `src/game/rules.py`
- Modify: `src/events/manager.py`
- Test: `tests/game/test_game_rules_pipeline.py`
- Test: `tests/events/test_event_manager_flow.py`

- [ ] **Step 1: Add explicit half-turn and full-turn helpers on `GameState`**

```python
def get_half_turn_count(self):
    return len(self.move_log)

def get_full_turn_count(self):
    return self.get_half_turn_count() // 2

def just_finished_full_turn(self):
    return self.white_to_move
```

- [ ] **Step 2: Route event timing through those helpers**

```python
self.turn_counter = self.gs.get_full_turn_count()
```

- [ ] **Step 3: Keep event update invocation behind a named rule**

```python
if game_state.just_finished_full_turn():
    game_state.event_manager.update()
```

- [ ] **Step 4: Add or rewrite tests so they describe full-turn semantics directly**

```python
self.assertTrue(game_state.just_finished_full_turn())
self.assertEqual(game_state.get_full_turn_count(), 10)
```

- [ ] **Step 5: Run the focused tests**

Run: `uv run python -m unittest tests.game.test_game_rules_pipeline tests.events.test_event_manager_flow -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/game/board.py src/game/rules.py src/events/manager.py tests/game/test_game_rules_pipeline.py tests/events/test_event_manager_flow.py
git commit -m "refactor: centralize half-turn and full-turn helpers"
```

### Task 11: Shape Captured-Piece Data for Future Rules, Not Only UI

**Files:**
- Modify: `src/game/capture_tracker.py`
- Modify: `src/game/board.py`
- Test: `tests/game/test_capture_tracker.py`

- [ ] **Step 1: Introduce a tiny captured-piece record**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CapturedPieceRecord:
    color: str
    piece_code: str

    def to_display_id(self):
        return f"{self.color}{self.piece_code}"
```

- [ ] **Step 2: Store records instead of raw display strings**

```python
if move.piece_moved.color == WHITE:
    self.white_captured.append(
        CapturedPieceRecord(move.piece_captured.color, move.piece_captured.get_piece_code())
    )
```

- [ ] **Step 3: Keep the public UI-facing method simple**

```python
def get_captured_pieces(self):
    return (
        [record.to_display_id() for record in self.white_captured],
        [record.to_display_id() for record in self.black_captured],
    )
```

- [ ] **Step 4: Add one test for record shape and preserve current UI output tests**

```python
self.assertEqual(game_state.get_captured_pieces(), ([BLACK + ROOK_CODE], []))
```

- [ ] **Step 5: Run the capture tracker tests**

Run: `uv run python -m unittest tests.game.test_capture_tracker -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/game/capture_tracker.py tests/game/test_capture_tracker.py
git commit -m "refactor: store captured pieces as small records"
```

### Task 12: Prepare the Event System for Persistent Effects

**Files:**
- Modify: `src/events/base.py`
- Modify: `src/events/manager.py`
- Test: `tests/events/test_event_base_contract.py`
- Test: `tests/events/test_event_manager_flow.py`

- [ ] **Step 1: Add a tiny optional tick hook to the base event contract**

```python
def tick(self):
    """Advance any per-turn event state."""
```

- [ ] **Step 2: Add a lightweight active-event tick step in the manager**

```python
def _tick_active_events(self):
    for event in list(self.active_events):
        event.tick()
```

- [ ] **Step 3: Call ticking from the manager update flow without changing one-shot behavior**

```python
if self.turn_counter > 0:
    self._tick_active_events()
```

- [ ] **Step 4: Keep `GiaXangTang` unchanged because it is still one-shot**

```python
class GiaXangTang(ChessEvent):
    ...
```

- [ ] **Step 5: Add a base-contract test that the hook exists and is no-op safe**

```python
event = ChessEvent(game_state)
event.tick()
self.assertFalse(event.warning_active)
```

- [ ] **Step 6: Run event tests**

Run: `uv run python -m unittest tests.events.test_event_base_contract tests.events.test_event_manager_flow tests.events.test_gia_xang_tang_event -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/events/base.py src/events/manager.py tests/events/test_event_base_contract.py tests/events/test_event_manager_flow.py
git commit -m "refactor: add lightweight event tick hook"
```

---

## Phase 5: Final OOP Polish Before Major New Features

**Purpose:** Make responsibilities easier to explain before adding Fusion, AP, and abilities.

### Task 13: Simplify Piece Identity and Status Semantics

**Files:**
- Modify: `src/pieces/base.py`
- Modify: `src/pieces/standard.py`
- Test: `tests/pieces/test_piece_metadata.py`
- Test: `tests/pieces/test_piece_extension_hooks.py`

- [ ] **Step 1: Decide one canonical source of piece identity**

```python
def get_piece_code(self):
    return self.piece_code
```

- [ ] **Step 2: Remove duplicated dependence on `name` where safe**

```python
self.id = f"{color}{self.get_piece_code()}"
```

- [ ] **Step 3: Replace magic `"active"` status with a simpler flag if status effects are not yet implemented**

```python
self.is_active = True
```

- [ ] **Step 4: Update the guard in `get_possible_moves()`**

```python
if not self.is_active:
    return []
```

- [ ] **Step 5: Re-run the piece metadata tests**

Run: `uv run python -m unittest tests.pieces.test_piece_metadata tests.pieces.test_piece_extension_hooks tests.pieces.test_piece_registry -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/pieces/base.py src/pieces/standard.py tests/pieces/test_piece_metadata.py tests/pieces/test_piece_extension_hooks.py
git commit -m "refactor: simplify piece identity and active-state semantics"
```

### Task 14: Normalize Remaining Comments and Architecture Notes

**Files:**
- Modify: `src/game/board.py`
- Modify: `src/game/move.py`
- Modify: `src/pieces/standard.py`
- Modify: `docs/architecture-current-baseline.md`

- [ ] **Step 1: Replace garbled comments with short English comments or docstrings**

```python
# Generate pseudo-legal moves first.
# Temporarily apply each move, then reject moves that leave the king in check.
```

- [ ] **Step 2: Keep comments only where they explain rules, not obvious syntax**

```python
if move.is_enpassant_move:
    # The captured pawn sits beside the destination square, not on it.
```

- [ ] **Step 3: Update the architecture note so it matches the post-cleanup seams**

```markdown
- `GameState` coordinates move execution, internal rollback for validation, and turn-based rule helpers.
```

- [ ] **Step 4: Do one final regression run**

Run: `uv run python -m unittest tests.ui.test_assets tests.ui.test_promotion_menu tests.ui.test_input_handler tests.ui.test_render_board tests.ui.test_render_panels tests.events.test_event_base_contract tests.events.test_event_registry tests.events.test_gia_xang_tang_event tests.events.test_event_manager_flow tests.game.test_castling_helpers tests.game.test_capture_tracker tests.game.test_material_scoring tests.game.test_game_rules_pipeline tests.game.test_board_helpers tests.game.test_board_piece_creation tests.game.test_move_and_undo tests.game.test_pawn_boundaries tests.pieces.test_piece_metadata tests.pieces.test_piece_registry tests.pieces.test_piece_extension_hooks -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/game/board.py src/game/move.py src/pieces/standard.py docs/architecture-current-baseline.md
git commit -m "docs: normalize rule comments and architecture wording"
```

---

## Final Verification Checklist

- [ ] The game no longer crashes on clicks outside the board width.
- [ ] Castling is impossible unless the correct rook is actually present.
- [ ] Promotion clicks outside the menu do not silently discard the pending move.
- [ ] `EventManager([])` stays empty instead of injecting a default event.
- [ ] No player-facing undo feature remains in runtime behavior.
- [ ] Internal rollback is clearly named and documented as simulation-only.
- [ ] Event countdown logic has one clear owner.
- [ ] UI code uses board helpers more consistently where random indexing was fragile.
- [ ] Turn/full-turn semantics are explicit enough for AP and timed-event features.
- [ ] Captured-piece tracking is usable both for UI and future rules like Necromancy.
- [ ] The event system has a minimal seam for persistent effects without overengineering.

---

## Self-Review

### Spec Coverage

- Correctness bugs: covered in Phase 1.
- Undo-removal leftovers: covered in Phase 2.
- Cleanup and maintainability: covered in Phase 3 and Phase 5.
- `mode.md` integration readiness: covered in Phase 4.
- OOP separation, coupling, extensibility: covered across Phases 2-5.

### Placeholder Scan

- No `TODO`, `TBD`, or “implement later” placeholders were left in the execution steps.
- Each task lists exact files and exact verification commands.

### Type and Naming Consistency

- Rollback terminology is consistently described as internal simulation support.
- Event timing helpers are consistently framed around half-turn/full-turn semantics.
- Captured-piece record naming is kept lightweight and domain-friendly.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-24-code-review-followup-phased-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
