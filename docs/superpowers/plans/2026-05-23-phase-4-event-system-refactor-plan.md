# Chess Fusion Phase 4 Event System Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the current special-event system so it is safe to extend with more global events from `mode.md` without repeatedly reopening one large `events.py` file.

**Architecture:** Keep the design simple and course-friendly. `GameState` should continue to own one event manager reference, but the event manager should handle timing and orchestration while each event class handles only its own warning, execution, cleanup, drawing, and snapshot requirements.

**Tech Stack:** Python, Pygame, `unittest`, current `src/` package

---

## Planned File and Folder Structure After Phase 4

```text
src/
├── constants.py
├── main.py
├── game/
│   ├── __init__.py
│   ├── board.py
│   ├── capture_tracker.py
│   ├── castling.py
│   ├── move.py
│   ├── rules.py
│   ├── scoring.py
│   └── state_helpers.py
├── events/
│   ├── __init__.py
│   ├── base.py                  # Base event contract + event snapshot models
│   ├── manager.py               # Event timing, queueing, undo/sync orchestration
│   ├── registry.py              # Simple event-class registry / event-pool helpers
│   └── gia_xang_tang.py         # First extracted concrete event
└── pieces/
    ├── __init__.py
    ├── base.py
    ├── registry.py
    └── standard.py

tests/
├── game/
│   ├── test_board_helpers.py
│   ├── test_board_piece_creation.py
│   ├── test_capture_tracker.py
│   ├── test_castling_helpers.py
│   ├── test_game_rules_pipeline.py
│   ├── test_material_scoring.py
│   ├── test_move_and_undo.py
│   └── test_pawn_boundaries.py
└── events/
    ├── test_event_base_contract.py
    ├── test_event_manager_flow.py
    ├── test_event_snapshot_restore.py
    ├── test_event_registry.py
    └── test_gia_xang_tang_event.py
```

## File Operation Summary

- **Create**
  - `src/events/__init__.py`
  - `src/events/base.py`
  - `src/events/manager.py`
  - `src/events/registry.py`
  - `src/events/gia_xang_tang.py`
  - `tests/events/test_event_base_contract.py`
  - `tests/events/test_event_manager_flow.py`
  - `tests/events/test_event_snapshot_restore.py`
  - `tests/events/test_event_registry.py`
  - `tests/events/test_gia_xang_tang_event.py`
- **Move**
  - Event-related classes currently in `src/events.py` into the new `src/events/` package
- **Modify**
  - `src/game/board.py`
  - `src/game/rules.py`
  - `src/main.py`
  - existing tests/imports as needed
- **Remove**
  - `src/events.py` after all imports are safely migrated

---

## Task 1: Split the Monolithic `events.py` into a Small Event Package

**Files:**
- Create: `src/events/__init__.py`, `src/events/base.py`, `src/events/manager.py`, `src/events/gia_xang_tang.py`
- Remove later: `src/events.py`

- [ ] **Step 1: Extract the base event abstractions**
  - **Target File(s):** `src/events/base.py`
  - **Proposed Action:** Move `ChessEvent` and event snapshot-related data objects into `base.py`, give them explicit docstrings, and define a small lifecycle contract for warning, execute, cleanup, draw, and snapshot support.
  - **OOP / Clean Code Justification:** This clarifies inheritance boundaries and makes the shared event lifecycle explicit. It also stops concrete events from depending on implicit assumptions scattered across one file.

- [ ] **Step 2: Extract `GiaXangTang` into its own concrete event module**
  - **Target File(s):** `src/events/gia_xang_tang.py`
  - **Proposed Action:** Move the current rook-to-knight transformation event into its own file and keep only event-specific behavior there: warning state, transformation logic, and event drawing.
  - **OOP / Clean Code Justification:** Concrete event behavior should live with the concrete event class, not inside the manager. This is a direct SRP improvement and makes future events easier to add one-by-one.

- [ ] **Step 3: Extract the event manager into its own module**
  - **Target File(s):** `src/events/manager.py`
  - **Proposed Action:** Move `EventManager` into `manager.py` so timing, queueing, active-event bookkeeping, and undo/sync flow are isolated from event definitions.
  - **OOP / Clean Code Justification:** This keeps orchestration separate from behavior without introducing advanced patterns. The result is still simple enough for a student project but much cleaner to extend.

- [ ] **Step 4: Add a stable package surface for events**
  - **Target File(s):** `src/events/__init__.py`
  - **Proposed Action:** Re-export only the public event-layer types that the rest of the code actually needs, such as `EventManager`, `ChessEvent`, and the first concrete event class if needed.
  - **OOP / Clean Code Justification:** A small import surface reduces coupling to file layout. It also makes later module moves less disruptive.

## Task 2: Clarify the Base Event Lifecycle and Event Contract

**Files:**
- Modify: `src/events/base.py`
- Test: `tests/events/test_event_base_contract.py`

- [ ] **Step 1: Make warning state part of the base contract**
  - **Target File(s):** `src/events/base.py`
  - **Proposed Action:** Add consistent event state fields such as `name`, `duration`, `warning_active`, and any lightweight metadata the manager/UI can read without knowing each concrete event’s internals.
  - **OOP / Clean Code Justification:** Shared event state belongs in the shared base class. This prevents each event from re-inventing the same shape in inconsistent ways.

- [ ] **Step 2: Add base methods for snapshot participation**
  - **Target File(s):** `src/events/base.py`
  - **Proposed Action:** Introduce small hooks such as `build_snapshot_data()` and `restore_from_snapshot_data()` or equivalent so events can declare any extra state they need to undo safely.
  - **OOP / Clean Code Justification:** This keeps undo-related behavior encapsulated inside each event instead of leaking event-specific knowledge into the manager.

- [ ] **Step 3: Keep drawing optional but standardized**
  - **Target File(s):** `src/events/base.py`
  - **Proposed Action:** Keep `draw(...)` as part of the lifecycle but define it as an optional no-op by default so warning overlays and later event-specific visuals have a predictable entry point.
  - **OOP / Clean Code Justification:** This is a practical use of inheritance: shared interface, specialized override only where needed.

- [ ] **Step 4: Add contract tests for the base event shape**
  - **Target File(s):** `tests/events/test_event_base_contract.py`
  - **Proposed Action:** Add small tests confirming default warning state, default lifecycle methods, and snapshot hooks behave predictably for a minimal subclass.
  - **OOP / Clean Code Justification:** This locks down the event contract before multiple event types start depending on it.

## Task 3: Replace Hardcoded Event Reconstruction with a Simple Registry

**Files:**
- Create: `src/events/registry.py`
- Modify: `src/events/manager.py`
- Test: `tests/events/test_event_registry.py`

- [ ] **Step 1: Add a simple event registry**
  - **Target File(s):** `src/events/registry.py`
  - **Proposed Action:** Create a small registry mapping event keys or names to event classes, and provide helpers for listing the event pool and rebuilding an event from stored metadata.
  - **OOP / Clean Code Justification:** This applies the Open/Closed Principle in a very basic, understandable way. Adding a new event should mostly mean “create class + register class.”

- [ ] **Step 2: Store queued-event identity explicitly**
  - **Target File(s):** `src/events/manager.py`
  - **Proposed Action:** Refactor the manager so queued/active events can be reconstructed from stored event identifiers instead of hardcoding `GiaXangTang` inside `sync_state()`.
  - **OOP / Clean Code Justification:** This removes one of the clearest extensibility violations in the current code. The manager should coordinate generic event identities, not know one special class by name.

- [ ] **Step 3: Make event selection use the registry/event pool helper**
  - **Target File(s):** `src/events/manager.py`, `src/events/registry.py`
  - **Proposed Action:** Route `_queue_next_event()` through the registry or pool helper so future events can be added by registration instead of editing random-choice logic directly.
  - **OOP / Clean Code Justification:** This preserves simple behavior while creating a clean seam for the growing event list in `mode.md`.

- [ ] **Step 4: Add registry tests**
  - **Target File(s):** `tests/events/test_event_registry.py`
  - **Proposed Action:** Add tests for event registration, event lookup by key, and queued-event reconstruction from stored identifiers.
  - **OOP / Clean Code Justification:** The registry becomes a core extensibility seam, so it should be locked down early.

## Task 4: Expand Event Snapshots Beyond Raw Board Copies

**Files:**
- Modify: `src/events/base.py`, `src/events/manager.py`, `src/game/board.py`
- Test: `tests/events/test_event_snapshot_restore.py`

- [ ] **Step 1: Redesign the event snapshot model**
  - **Target File(s):** `src/events/base.py`
  - **Proposed Action:** Replace the current “move log length + board grid copy only” snapshot with a clearer snapshot object that can also store queued-event identity, active warning state, and any event-specific payload needed for restoration.
  - **OOP / Clean Code Justification:** Undo needs to restore the event system state, not only the visible pieces. A dedicated snapshot model keeps that responsibility explicit and manageable.

- [ ] **Step 2: Snapshot event-manager state at execution time**
  - **Target File(s):** `src/events/manager.py`
  - **Proposed Action:** When an event resolves, capture the minimum manager state required to restore it correctly later: board snapshot, queued-event metadata, active events/warnings, and any event-specific snapshot payload.
  - **OOP / Clean Code Justification:** This keeps restoration logic inside the event layer rather than leaking it into `GameState`.

- [ ] **Step 3: Restore event state generically during undo/sync**
  - **Target File(s):** `src/events/manager.py`
  - **Proposed Action:** Refactor `handle_undo()` and `sync_state()` so they restore queued/active event state through generic snapshot data and registry lookups instead of reconstructing one hardcoded event manually.
  - **OOP / Clean Code Justification:** This is the key change that makes undo future-proof for more than one event type.

- [ ] **Step 4: Add snapshot restoration tests**
  - **Target File(s):** `tests/events/test_event_snapshot_restore.py`
  - **Proposed Action:** Add tests proving that event execution, undo restoration, and warning-state sync all survive without hardcoded event-specific branching.
  - **OOP / Clean Code Justification:** Event snapshots are correctness-sensitive and will be reused by later events with more complex state.

## Task 5: Route Event Mutations Through Game/Board Helpers

**Files:**
- Modify: `src/game/board.py`, `src/events/gia_xang_tang.py`
- Test: `tests/events/test_gia_xang_tang_event.py`

- [ ] **Step 1: Add minimal board/game helpers for event-driven mutations**
  - **Target File(s):** `src/game/board.py`
  - **Proposed Action:** Add a few explicit helpers such as `replace_piece_at()`, `remove_piece_at()`, or a similarly small API so events stop writing directly to `board.grid` for gameplay-changing mutations.
  - **OOP / Clean Code Justification:** Board mutation rules belong in the game domain layer. This protects castling, piece state, undo, and future trackers from silent desynchronization.

- [ ] **Step 2: Refactor `GiaXangTang` to use the new helpers**
  - **Target File(s):** `src/events/gia_xang_tang.py`
  - **Proposed Action:** Replace direct board-grid mutation with board/game helper calls while preserving the exact current gameplay effect.
  - **OOP / Clean Code Justification:** This proves the helper boundary works in practice before more destructive events are added later.

- [ ] **Step 3: Keep transformed-piece state consistent**
  - **Target File(s):** `src/events/gia_xang_tang.py`, `src/game/board.py`
  - **Proposed Action:** Ensure transformations preserve important state such as color, position, and `has_moved`, and document any still-open limitations that Phase 6 or later systems will address.
  - **OOP / Clean Code Justification:** Encapsulation is only useful if state changes stay coherent when ownership crosses modules.

- [ ] **Step 4: Add focused tests for the extracted event**
  - **Target File(s):** `tests/events/test_gia_xang_tang_event.py`
  - **Proposed Action:** Add tests for warning activation, execution behavior, state preservation for transformed pieces, and integration with the manager.
  - **OOP / Clean Code Justification:** This gives the first concrete extracted event a reliable safety net before more events are introduced.

## Task 6: Keep the Current Rule Flow Compatible with the Refactored Event Layer

**Files:**
- Modify: `src/game/rules.py`, `src/game/board.py`, `src/main.py`
- Test: `tests/events/test_event_manager_flow.py`, existing game tests

- [ ] **Step 1: Keep the post-move pipeline using the public event-manager API**
  - **Target File(s):** `src/game/rules.py`
  - **Proposed Action:** Verify the Phase 3 post-move pipeline still calls only the public `EventManager` methods after the package split, without reaching into event internals.
  - **OOP / Clean Code Justification:** This preserves encapsulation between the game flow and the event subsystem.

- [ ] **Step 2: Update `GameState` and UI imports to the new event package**
  - **Target File(s):** `src/game/board.py`, `src/main.py`
  - **Proposed Action:** Update imports and any small call-site assumptions so the rest of the game continues to interact with the event system through the same high-level behavior after the module reorganization.
  - **OOP / Clean Code Justification:** Refactor should improve structure without forcing broad changes across unrelated modules.

- [ ] **Step 3: Add manager-flow integration tests**
  - **Target File(s):** `tests/events/test_event_manager_flow.py`
  - **Proposed Action:** Add tests covering warning turn, execution turn, active-event cleanup, and queueing of the next event through the refactored manager.
  - **OOP / Clean Code Justification:** This protects the orchestration behavior that later global events will depend on.

## Task 7: Verification and Cleanup

**Files:**
- Modify: all new/changed event files
- Test: all `tests/events/*.py` plus existing game/piece suites

- [ ] **Step 1: Run the event-specific regression suite**
  - **Target File(s):** `tests/events/test_event_base_contract.py`, `tests/events/test_event_manager_flow.py`, `tests/events/test_event_snapshot_restore.py`, `tests/events/test_event_registry.py`, `tests/events/test_gia_xang_tang_event.py`
  - **Proposed Action:** Run the new event-layer tests first to verify the package split and manager/event boundaries are stable on their own.
  - **OOP / Clean Code Justification:** Event refactors are easiest to validate in isolation before mixing them with the rest of the domain.

- [ ] **Step 2: Run the existing game-domain regression suite**
  - **Target File(s):** existing `tests/game/*.py`, `tests/pieces/*.py`
  - **Proposed Action:** Re-run the earlier game and piece tests to ensure the event refactor did not break move flow, undo, scoring, or UI-facing summaries.
  - **OOP / Clean Code Justification:** A good architecture refactor must preserve the behavior already stabilized in earlier phases.

- [ ] **Step 3: Remove the old monolithic `src/events.py` only after green verification**
  - **Target File(s):** `src/events.py`
  - **Proposed Action:** Delete the legacy monolithic file once all imports and tests are confirmed green, so the project has one clear event architecture instead of two overlapping ones.
  - **OOP / Clean Code Justification:** Cleanup matters because duplicate architecture invites confusion and backsliding.

- [ ] **Step 4: Add concise docstrings to each new event-layer module**
  - **Target File(s):** `src/events/__init__.py`, `src/events/base.py`, `src/events/manager.py`, `src/events/registry.py`, `src/events/gia_xang_tang.py`
  - **Proposed Action:** Add short docstrings explaining each file’s role and how the event subsystem interacts with `GameState`.
  - **OOP / Clean Code Justification:** This follows `AGENTS.md` and makes the refactor much easier to present in a university setting.

---

## Why This Phase 4 Structure Is Recommended

- [ ] **Keep the package shallow**
  - **Target File(s):** `src/events/`
  - **Proposed Action:** Use one small event package with a base module, manager, registry, and concrete events, instead of introducing nested subpackages or complicated plugin systems.
  - **OOP / Clean Code Justification:** This satisfies extensibility goals without violating the project’s “NO OVERENGINEERING” rule.

- [ ] **Treat each event like a small game-rule object**
  - **Target File(s):** `src/events/base.py`, `src/events/gia_xang_tang.py`
  - **Proposed Action:** Let each event own its own lifecycle and rule behavior, while the manager handles only timing and queueing.
  - **OOP / Clean Code Justification:** This is a natural, course-level application of encapsulation and polymorphism.

- [ ] **Create the extension seam before adding more chaotic events**
  - **Target File(s):** `src/events/registry.py`, `src/events/manager.py`
  - **Proposed Action:** Finish the registry, snapshot, and manager/event boundaries now so later events like Meteor Strike, Minefield, and Ice Storm can be added with mostly additive changes.
  - **OOP / Clean Code Justification:** This reduces rework and aligns directly with the future requirements documented in `mode.md`.
