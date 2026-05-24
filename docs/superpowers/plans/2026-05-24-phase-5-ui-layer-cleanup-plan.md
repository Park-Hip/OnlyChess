# Chess Fusion Phase 5 UI Layer Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the current Pygame UI layer so `main.py` becomes a thin coordinator and the project has clean entry points for future ability menus, AP displays, event overlays, and richer interaction without turning the main loop into a God Object.

**Architecture:** Keep the UI design simple and course-friendly. Use one shallow `src/ui/` package with small modules for rendering, assets, promotion UI, and input state handling. `GameState` must remain the only source of gameplay truth; UI helpers should only read public state and return user interaction results.

**Tech Stack:** Python, Pygame, `unittest`, current `src/` package

---

## Planned File and Folder Structure After Phase 5

```text
src/
├── constants.py
├── main.py
├── events/
│   ├── __init__.py
│   ├── base.py
│   ├── gia_xang_tang.py
│   ├── manager.py
│   └── registry.py
├── game/
│   ├── __init__.py
│   ├── board.py
│   ├── capture_tracker.py
│   ├── castling.py
│   ├── move.py
│   ├── rules.py
│   ├── scoring.py
│   └── state_helpers.py
├── pieces/
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   └── standard.py
└── ui/
    ├── __init__.py
    ├── assets.py                # Image loading and sprite lookup helpers
    ├── input_handler.py         # Selection, dragging, and move-attempt state
    ├── promotion_menu.py        # Promotion menu draw + click-resolution helpers
    ├── render_board.py          # Board, highlights, pieces, overlays
    └── render_panels.py         # Top/bottom player panels and event countdown UI

tests/
├── events/
│   ├── test_event_base_contract.py
│   ├── test_event_manager_flow.py
│   ├── test_event_registry.py
│   ├── test_event_snapshot_restore.py
│   └── test_gia_xang_tang_event.py
├── game/
│   ├── test_board_helpers.py
│   ├── test_board_piece_creation.py
│   ├── test_capture_tracker.py
│   ├── test_castling_helpers.py
│   ├── test_game_rules_pipeline.py
│   ├── test_material_scoring.py
│   ├── test_move_and_undo.py
│   └── test_pawn_boundaries.py
├── pieces/
│   ├── test_piece_extension_hooks.py
│   ├── test_piece_metadata.py
│   └── test_piece_registry.py
└── ui/
    ├── test_assets.py
    ├── test_input_handler.py
    ├── test_promotion_menu.py
    ├── test_render_board.py
    └── test_render_panels.py
```

## File Operation Summary

- **Create**
  - `src/ui/__init__.py`
  - `src/ui/assets.py`
  - `src/ui/input_handler.py`
  - `src/ui/promotion_menu.py`
  - `src/ui/render_board.py`
  - `src/ui/render_panels.py`
  - `tests/ui/test_assets.py`
  - `tests/ui/test_input_handler.py`
  - `tests/ui/test_promotion_menu.py`
  - `tests/ui/test_render_board.py`
  - `tests/ui/test_render_panels.py`
- **Modify**
  - `src/main.py`
  - `src/game/board.py` only if a tiny public helper is needed for UI-safe access
  - existing tests/imports as needed
- **Remove**
  - No file deletions are required in Phase 5; existing UI functions should be migrated out of `main.py`, not abruptly dropped

---

## Task 1: Extract Asset Loading and Sprite Lookup

**Files:**
- Create: `src/ui/assets.py`
- Modify: `src/main.py`
- Test: `tests/ui/test_assets.py`

- [ ] **Step 1: Move image-loading logic into a UI assets module**
  - **Target File(s):** `src/ui/assets.py`
  - **Proposed Action:** Extract `load_images()` from `main.py` into an assets helper that loads sprites using stable piece display ids or sprite keys, while preserving the current file layout under `images/`.
  - **OOP / Clean Code Justification:** Asset loading is a UI responsibility and should not live in the game loop. This also prepares the project for fused/custom pieces without hardcoding asset assumptions in `main.py`.

- [ ] **Step 2: Keep sprite lookup aligned with piece metadata**
  - **Target File(s):** `src/ui/assets.py`, `src/main.py`
  - **Proposed Action:** Make rendering code consistently use `piece.get_sprite_key()` instead of direct string-building logic, and ensure panel thumbnails and dragged-piece rendering use the same lookup rule.
  - **OOP / Clean Code Justification:** The UI should ask pieces how they should be rendered, not duplicate identity logic outside the piece model.

- [ ] **Step 3: Add asset-loading regression tests**
  - **Target File(s):** `tests/ui/test_assets.py`
  - **Proposed Action:** Add tests for expected sprite keys, asset dictionary completeness for standard pieces, and any lightweight helper behavior that can be tested without opening a real Pygame window.
  - **OOP / Clean Code Justification:** This locks down the rendering contract before future fused-piece sprites and transformed-event states are added.

## Task 2: Extract Board Rendering and Overlay Drawing

**Files:**
- Create: `src/ui/render_board.py`
- Modify: `src/main.py`
- Test: `tests/ui/test_render_board.py`

- [ ] **Step 1: Move board and piece rendering into a dedicated renderer**
  - **Target File(s):** `src/ui/render_board.py`
  - **Proposed Action:** Move `draw_board()`, `draw_pieces()`, dragged-piece rendering, and the board portion of `draw_game_state()` into a focused render module.
  - **OOP / Clean Code Justification:** Rendering the board is a separate responsibility from input and turn orchestration. This keeps the main loop readable and gives future UI work a clear home.

- [ ] **Step 2: Move selection and move-highlight overlays into the renderer**
  - **Target File(s):** `src/ui/render_board.py`
  - **Proposed Action:** Move highlight logic for last move, selected square, and legal target squares out of `main.py`, while keeping the renderer purely read-only with respect to `GameState`.
  - **OOP / Clean Code Justification:** The renderer should consume state and draw it, not mutate game rules. This separation keeps future visual polish independent from gameplay logic.

- [ ] **Step 3: Keep event warning drawing compatible with the extracted event layer**
  - **Target File(s):** `src/ui/render_board.py`, `src/main.py`
  - **Proposed Action:** Move the loop that renders active event overlays into the render module or a clearly named helper so `main.py` no longer manually iterates event UI details.
  - **OOP / Clean Code Justification:** Event visuals are still UI, even though the event system owns the behavior. This keeps the main loop focused on orchestration.

- [ ] **Step 4: Add render-module regression tests**
  - **Target File(s):** `tests/ui/test_render_board.py`
  - **Proposed Action:** Add lightweight tests for helper behavior that can be verified without visual inspection, such as correct use of sprite keys, selected-square filtering, or highlight input preparation.
  - **OOP / Clean Code Justification:** Even in a Pygame project, some rendering logic can still be stabilized with small functional tests.

## Task 3: Extract Player Panels and Match Summary UI

**Files:**
- Create: `src/ui/render_panels.py`
- Modify: `src/main.py`
- Test: `tests/ui/test_render_panels.py`

- [ ] **Step 1: Move top/bottom info panel rendering into its own module**
  - **Target File(s):** `src/ui/render_panels.py`
  - **Proposed Action:** Move `draw_info_panels()` out of `main.py`, including captured-piece mini-icons, material-advantage summary, player labels, and event countdown text.
  - **OOP / Clean Code Justification:** Sidebar/panel rendering is its own UI concern and should not be mixed with click handling or move execution.

- [ ] **Step 2: Keep panel rendering dependent on public `GameState` methods only**
  - **Target File(s):** `src/ui/render_panels.py`
  - **Proposed Action:** Make the panel renderer read captured pieces, material advantage, and turn/event summary through public game-state APIs instead of reaching into helper internals wherever possible.
  - **OOP / Clean Code Justification:** This preserves encapsulation between the domain layer and the UI layer.

- [ ] **Step 3: Leave clear hooks for future AP and ability UI**
  - **Target File(s):** `src/ui/render_panels.py`
  - **Proposed Action:** Structure the panel renderer so future AP counters, ability cooldown text, or advanced-mode overlays can be added in a few clearly named sections without reopening the whole file.
  - **OOP / Clean Code Justification:** This creates extension seams for later UX work while staying simple and readable.

- [ ] **Step 4: Add panel helper tests**
  - **Target File(s):** `tests/ui/test_render_panels.py`
  - **Proposed Action:** Add tests for panel-summary helper functions or layout-preparation helpers, especially score text and event-countdown calculations.
  - **OOP / Clean Code Justification:** The panel logic contains real state formatting and should not be left entirely unguarded.

## Task 4: Isolate Promotion Menu Workflow

**Files:**
- Create: `src/ui/promotion_menu.py`
- Modify: `src/main.py`
- Test: `tests/ui/test_promotion_menu.py`

- [ ] **Step 1: Move promotion-menu drawing into a dedicated module**
  - **Target File(s):** `src/ui/promotion_menu.py`
  - **Proposed Action:** Extract `draw_promotion_menu()` from `main.py` and keep all size, position, and piece-choice rendering details inside the new module.
  - **OOP / Clean Code Justification:** Promotion is already a separate mini-workflow and deserves its own focused UI component.

- [ ] **Step 2: Add a helper to resolve promotion clicks into piece choices**
  - **Target File(s):** `src/ui/promotion_menu.py`
  - **Proposed Action:** Move the menu click-resolution math out of the event loop into a helper that returns the chosen piece code or `None`.
  - **OOP / Clean Code Justification:** Input math specific to promotion should not clutter the main loop. This also makes the workflow easier to test and reuse.

- [ ] **Step 3: Keep promotion flow compatible with the piece registry**
  - **Target File(s):** `src/ui/promotion_menu.py`, `src/main.py`
  - **Proposed Action:** Keep the output of the promotion menu as a simple piece code that `GameState.make_move()` can already consume, without introducing a larger UI abstraction.
  - **OOP / Clean Code Justification:** This preserves a small interface between UI and game logic and avoids overengineering.

- [ ] **Step 4: Add promotion-menu tests**
  - **Target File(s):** `tests/ui/test_promotion_menu.py`
  - **Proposed Action:** Add tests for menu geometry helpers, click-to-piece mapping, and cancellation/outside-click behavior where practical.
  - **OOP / Clean Code Justification:** Promotion is a user-facing special flow and should stay predictable as the UI is cleaned up.

## Task 5: Extract Input State and Move-Attempt Handling

**Files:**
- Create: `src/ui/input_handler.py`
- Modify: `src/main.py`
- Test: `tests/ui/test_input_handler.py`

- [ ] **Step 1: Introduce a small input-state object or helper set**
  - **Target File(s):** `src/ui/input_handler.py`
  - **Proposed Action:** Move UI-only state such as selected square, player clicks, dragging flag, mouse position, click type, and move-attempt type out of `main.py` into a small state object or tightly grouped helper functions.
  - **OOP / Clean Code Justification:** This keeps transient UI state separate from the actual game state. It is a practical use of encapsulation without creating a heavy framework.

- [ ] **Step 2: Move board-click selection logic into input helpers**
  - **Target File(s):** `src/ui/input_handler.py`
  - **Proposed Action:** Extract the logic for first click, reselection, second click, drag-start, drag-end, and board-bound clamping into named helpers that return updated input state and any move-attempt data.
  - **OOP / Clean Code Justification:** The current event loop mixes too many interaction branches. Splitting them into small helpers makes the behavior easier to explain and debug.

- [ ] **Step 3: Keep move validation in `GameState`, not in the input layer**
  - **Target File(s):** `src/ui/input_handler.py`, `src/main.py`
  - **Proposed Action:** Let the input layer only package user intent into candidate moves or UI actions; `GameState` and valid-move lists must remain the source of legality.
  - **OOP / Clean Code Justification:** This preserves the boundary between UI intent and domain rules, which is critical for future abilities and special events.

- [ ] **Step 4: Add input-handler tests**
  - **Target File(s):** `tests/ui/test_input_handler.py`
  - **Proposed Action:** Add tests for selection transitions, drag-release conversion into move attempts, invalid click reset behavior, and promotion-pending short-circuit behavior where possible.
  - **OOP / Clean Code Justification:** Input state bugs are easy to introduce during UI refactors, so a small behavioral safety net is worth adding.

## Task 6: Reduce `main.py` to a Thin Orchestrator

**Files:**
- Modify: `src/main.py`
- Existing tests plus `tests/ui/*.py`

- [ ] **Step 1: Keep `main()` responsible only for app orchestration**
  - **Target File(s):** `src/main.py`
  - **Proposed Action:** Refactor `main()` so it initializes Pygame, creates `GameState`, loads assets, delegates input handling, delegates drawing, and coordinates move refresh and end-of-game messaging.
  - **OOP / Clean Code Justification:** The main loop should orchestrate modules, not contain all module logic inline. This is the core anti-God-Object goal of Phase 5.

- [ ] **Step 2: Replace wildcard constant usage where cleanup is straightforward**
  - **Target File(s):** `src/main.py`
  - **Proposed Action:** As part of the UI cleanup, reduce overreliance on `from .constants import *` if it can be done cleanly without widening the phase too much.
  - **OOP / Clean Code Justification:** Explicit imports improve readability and align with clean-code goals, but this should stay secondary to the structural UI refactor.

- [ ] **Step 3: Keep undo and event-warning integration behavior unchanged**
  - **Target File(s):** `src/main.py`
  - **Proposed Action:** Preserve the current undo ordering with event restoration and keep active-event warning overlays visible through the new render path.
  - **OOP / Clean Code Justification:** Phase 5 is a UI cleanup phase, not a gameplay-rule redesign. Behavior must stay stable while responsibilities move.

- [ ] **Step 4: Keep endgame message rendering in a clearly named UI helper**
  - **Target File(s):** `src/main.py`, optionally `src/ui/render_board.py`
  - **Proposed Action:** Move `draw_text()` or equivalent endgame-message rendering into a clearer UI helper if it improves organization, while avoiding unnecessary fragmentation.
  - **OOP / Clean Code Justification:** This keeps small view logic grouped without forcing every tiny helper into its own file.

## Task 7: Verification and Cleanup

**Files:**
- Modify: all new UI files and `src/main.py`
- Test: all new `tests/ui/*.py` plus existing event/game/piece suites

- [ ] **Step 1: Run UI-focused regression tests**
  - **Target File(s):** `tests/ui/test_assets.py`, `tests/ui/test_input_handler.py`, `tests/ui/test_promotion_menu.py`, `tests/ui/test_render_board.py`, `tests/ui/test_render_panels.py`
  - **Proposed Action:** Run the new UI tests first to validate the refactored rendering/input helpers in isolation.
  - **OOP / Clean Code Justification:** UI cleanup is safest when small components are verified before full integration.

- [ ] **Step 2: Re-run existing event/game/piece regression suites**
  - **Target File(s):** existing `tests/events/*.py`, `tests/game/*.py`, `tests/pieces/*.py`
  - **Proposed Action:** Re-run the earlier regression suites to confirm the UI-layer refactor did not break move execution, undo flow, event handling, or piece rendering assumptions.
  - **OOP / Clean Code Justification:** Separation of responsibilities is only valuable if behavior remains stable.

- [ ] **Step 3: Run a Pygame smoke test after UI extraction**
  - **Target File(s):** local runtime verification only
  - **Proposed Action:** Run the same dummy-video-driver smoke boot used in earlier phases to ensure the app still starts, enters the main loop, and exits cleanly after the module split.
  - **OOP / Clean Code Justification:** This confirms the UI orchestration still works end-to-end after moving rendering and input helpers.

- [ ] **Step 4: Add concise docstrings to each new UI module**
  - **Target File(s):** `src/ui/__init__.py`, `src/ui/assets.py`, `src/ui/input_handler.py`, `src/ui/promotion_menu.py`, `src/ui/render_board.py`, `src/ui/render_panels.py`
  - **Proposed Action:** Add short docstrings describing each module’s single responsibility and how `main.py` coordinates them.
  - **OOP / Clean Code Justification:** This follows `AGENTS.md` and makes the UI architecture easy to present and defend in a university project.

---

## Why This Phase 5 Structure Is Recommended

- [ ] **Keep the UI package shallow**
  - **Target File(s):** `src/ui/`
  - **Proposed Action:** Use one flat UI package with a handful of clearly named modules, rather than nested view/component systems or framework-like abstractions.
  - **OOP / Clean Code Justification:** This keeps the refactor understandable and respects the project’s “NO OVERENGINEERING” rule.

- [ ] **Treat the UI layer as a consumer of domain state**
  - **Target File(s):** `src/ui/*.py`, `src/main.py`
  - **Proposed Action:** Ensure UI helpers only read state and package user intent, while `GameState` remains responsible for rule truth and move legality.
  - **OOP / Clean Code Justification:** This is the cleanest boundary between interface and game logic for a project at this level.

- [ ] **Create UX seams before abilities and AP are added**
  - **Target File(s):** `src/ui/render_panels.py`, `src/ui/input_handler.py`, `src/ui/promotion_menu.py`
  - **Proposed Action:** Finish the panel/input/promotion seams now so AP bars, right-click ability menus, and event overlays can be added later without reopening a giant `main.py`.
  - **OOP / Clean Code Justification:** This reduces future rework and aligns directly with the next gameplay features planned in `mode.md`.
