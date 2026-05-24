# Chess Fusion Phase 7 Documentation and Verification Readiness Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalize the current post-Phase-5 codebase into a stable, lecturer-ready baseline by tightening documentation, cleaning public import surfaces, normalizing run/test instructions, and running a final verification pass. Phase 6 is intentionally skipped, so this phase must not introduce Fusion seams, AP state, or any speculative advanced-mode scaffolding.

**Architecture:** Keep the current package layout shallow and intact. The only structural edits in this phase should be tiny cleanup changes that improve clarity without changing architecture: docstrings, docs, package exports, and small public helper naming or entrypoint fixes.

**Tech Stack:** Python, Pygame, `unittest`, current `src/` package

---

## Planned File and Folder Structure After Phase 7

```text
docs/
├── architecture-current-baseline.md     # New lecturer-facing architecture note
└── superpowers/
    └── plans/
        ├── 2026-05-23-chess-fusion-refactor-plan.md
        ├── 2026-05-23-phase-1-core-stabilization-plan.md
        ├── 2026-05-23-phase-2-clean-piece-model-plan.md
        ├── 2026-05-23-phase-3-reduce-gamestate-coupling-plan.md
        ├── 2026-05-23-phase-4-event-system-refactor-plan.md
        ├── 2026-05-24-phase-5-ui-layer-cleanup-plan.md
        └── 2026-05-24-phase-7-documentation-and-verification-plan.md

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
    ├── assets.py
    ├── input_handler.py
    ├── promotion_menu.py
    ├── render_board.py
    └── render_panels.py
```

## File Operation Summary

- **Create**
  - `docs/architecture-current-baseline.md`
- **Modify**
  - `README.md`
  - `src/events/__init__.py`
  - `src/game/__init__.py`
  - `src/pieces/__init__.py`
  - `src/ui/__init__.py`
  - any touched `src/` modules that still need concise docstrings
  - `main.py` or `run.py` only if a tiny entrypoint clarification/fix is needed
- **Remove**
  - No file deletions are required in Phase 7

---

## Task 1: Finalize Docstrings on the Current Architecture Seams

**Files:**
- Modify: extracted modules under `src/game/`, `src/events/`, `src/pieces/`, `src/ui/`

- [ ] **Step 1: Audit module docstrings across extracted packages**
  - **Target File(s):** all files under `src/game/`, `src/events/`, `src/pieces/`, `src/ui/`
  - **Proposed Action:** Review every extracted module from Phases 1-5 and add or tighten the top-level docstring so each file clearly states its single responsibility in one sentence.
  - **OOP / Clean Code Justification:** Module boundaries are now one of the strongest parts of the refactor, so each one should be explicitly documented for a student/lecturer audience.

- [ ] **Step 2: Fill only missing or non-obvious class/function docstrings**
  - **Target File(s):** touched files from Phases 1-5
  - **Proposed Action:** Add short docstrings to public helpers, data objects, and orchestration methods where the purpose is not already obvious from the name. Do not add noisy docstrings to trivial getters/setters.
  - **OOP / Clean Code Justification:** The goal is readability and explainability, not documentation bloat.

- [ ] **Step 3: Avoid speculative or future-facing documentation**
  - **Target File(s):** all touched `src/` files
  - **Proposed Action:** Keep docstrings strictly about the currently implemented baseline. Do not mention Fusion/AP placeholders, future abilities, or unimplemented advanced-mode subsystems.
  - **OOP / Clean Code Justification:** This keeps the code truthful and avoids misleading future scaffolding, which aligns with the “no overengineering” rule.

## Task 2: Add a Lecturer-Friendly Architecture Note for the Current Baseline

**Files:**
- Create: `docs/architecture-current-baseline.md`

- [ ] **Step 1: Write a short architecture note for the current project state**
  - **Target File(s):** `docs/architecture-current-baseline.md`
  - **Proposed Action:** Create a concise markdown note explaining the current post-refactor structure and how the main packages collaborate.
  - **OOP / Clean Code Justification:** This gives the student a clean, high-level explanation of the architecture they can present without diving into every file.

- [ ] **Step 2: Describe the main responsibilities of the current packages**
  - **Target File(s):** `docs/architecture-current-baseline.md`
  - **Proposed Action:** Document these roles clearly:
    - `GameState` in `game/` as the turn-flow coordinator
    - `pieces/` as piece behavior + metadata
    - `events/` as event lifecycle + orchestration
    - `ui/` as rendering and input helpers
  - **OOP / Clean Code Justification:** This reinforces SRP and package boundaries in a way that matches the current code, not the future wishlist.

- [ ] **Step 3: Mark this baseline explicitly as pre-Fusion/AP**
  - **Target File(s):** `docs/architecture-current-baseline.md`
  - **Proposed Action:** State clearly that this document describes the stable classic-plus-events baseline after Phase 5, before any Fusion/AP implementation work begins.
  - **OOP / Clean Code Justification:** This prevents confusion now that Phase 6 is intentionally skipped.

## Task 3: Clean Public Import Surfaces Without Changing Architecture

**Files:**
- Modify: `src/events/__init__.py`, `src/game/__init__.py`, `src/pieces/__init__.py`, `src/ui/__init__.py`

- [ ] **Step 1: Review every package `__init__.py` for stale exports**
  - **Target File(s):** all package `__init__.py` files under `src/`
  - **Proposed Action:** Check whether each package re-exports too much, too little, or misleading symbols left over from earlier refactors.
  - **OOP / Clean Code Justification:** A stable import surface helps the student explain the package boundaries and reduces accidental coupling.

- [ ] **Step 2: Re-export only the small public surfaces actually needed**
  - **Target File(s):** same `__init__.py` files
  - **Proposed Action:** Keep package surfaces minimal and intentional. If a package is currently best used via direct module imports, prefer a very small or even empty `__init__.py` rather than a dumping ground.
  - **OOP / Clean Code Justification:** This keeps the package layout shallow and clean without inventing a heavy public API layer.

- [ ] **Step 3: Preserve working behavior over theoretical neatness**
  - **Target File(s):** same `__init__.py` files
  - **Proposed Action:** If trimming an export would force broad import churn or break current tests/entrypoints, preserve the working interface and document that choice instead.
  - **OOP / Clean Code Justification:** Phase 7 is a stabilization phase, so behavior stability matters more than aesthetic purity.

## Task 4: Normalize Canonical Entrypoints and Run/Test Instructions

**Files:**
- Modify: `README.md`
- Modify only if needed: `main.py`, `run.py`

- [ ] **Step 1: Decide and document one canonical way to launch the game**
  - **Target File(s):** `README.md`
  - **Proposed Action:** Pick the clearest supported command for launching the game and document it as the primary entrypoint. If both `main.py` and `run.py` are supported, explain which one is the recommended user-facing command.
  - **OOP / Clean Code Justification:** A lecturer should not have to guess which file is the real app entrypoint.

- [ ] **Step 2: Decide and document one canonical regression test command**
  - **Target File(s):** `README.md`
  - **Proposed Action:** Add the exact test command used to verify the current baseline, keeping it minimal and copy-paste ready.
  - **OOP / Clean Code Justification:** This makes the project easier to evaluate and reinforces confidence in the refactored baseline.

- [ ] **Step 3: Make entrypoint wrappers truthful and minimal**
  - **Target File(s):** `main.py`, `run.py`
  - **Proposed Action:** If the root-level wrapper files are ambiguous or redundant, keep them tiny and accurate rather than deleting them. Fix only small correctness or clarity issues.
  - **OOP / Clean Code Justification:** Clear entrypoint roles reduce confusion without requiring structural churn.

- [ ] **Step 4: Keep the README focused on the current implementation**
  - **Target File(s):** `README.md`
  - **Proposed Action:** Update run/test usage, short project summary, and architecture note references so they reflect the current baseline only, not future Fusion/AP plans.
  - **OOP / Clean Code Justification:** Documentation should reflect what a lecturer can actually run and inspect today.

## Task 5: Apply Only Tiny Naming or Helper Cleanups That Improve Clarity

**Files:**
- Modify only if justified: small set of touched `src/` files

- [ ] **Step 1: Identify misleading helper names left after the refactors**
  - **Target File(s):** current `src/` modules
  - **Proposed Action:** Look for helpers whose names still reflect old structure or obscure their purpose after Phases 1-5.
  - **OOP / Clean Code Justification:** Small naming fixes can improve readability substantially without changing architecture.

- [ ] **Step 2: Rename only the smallest necessary public-facing helpers**
  - **Target File(s):** only where needed
  - **Proposed Action:** If a helper rename materially improves clarity, make the smallest safe rename and update tests/imports accordingly. Do not perform broad symbol churn.
  - **OOP / Clean Code Justification:** This keeps the phase focused on clarity, not cosmetic rewrites.

- [ ] **Step 3: Reject any cleanup that drifts toward Phase 6 work**
  - **Target File(s):** all touched `src/` files
  - **Proposed Action:** Do not introduce Fusion hooks, AP placeholders, advanced state fields, or new future-facing abstractions under the name of cleanup.
  - **OOP / Clean Code Justification:** This preserves the scope boundary and keeps Phase 7 decision-complete.

## Task 6: Lock the Current Baseline and Verify It End-to-End

**Files:**
- Modify docs if needed after verification
- Run all current test suites

- [ ] **Step 1: Run the complete automated regression suite**
  - **Target File(s):** all current `tests/ui/*.py`, `tests/events/*.py`, `tests/game/*.py`, `tests/pieces/*.py`
  - **Proposed Action:** Re-run the entire automated suite and treat it as the official post-Phase-5 baseline verification pass.
  - **OOP / Clean Code Justification:** This locks in the current architecture before any future gameplay feature work starts.

- [ ] **Step 2: Re-run Pygame smoke tests through the supported entrypoints**
  - **Target File(s):** runtime verification only
  - **Proposed Action:** Re-run the dummy-video-driver smoke test through the canonical documented entrypoint, and also through any secondary wrapper that is intentionally supported.
  - **OOP / Clean Code Justification:** This confirms the documented launch path is correct, not just the package internals.

- [ ] **Step 3: Manually verify the key UX flows still hold**
  - **Target File(s):** manual runtime check
  - **Proposed Action:** Confirm these behaviors still work:
    - normal move input
    - drag/click interaction
    - promotion flow
    - undo flow with event restoration
    - active event warning rendering
    - captured-piece panels and score summaries
  - **OOP / Clean Code Justification:** These are the user-visible flows most likely to regress after the UI and event refactors.

- [ ] **Step 4: Mark the current baseline explicitly in docs**
  - **Target File(s):** `docs/architecture-current-baseline.md` and/or `README.md`
  - **Proposed Action:** State clearly that this verified checkpoint is the stable classic-plus-events baseline and that future feature work starts after this checkpoint.
  - **OOP / Clean Code Justification:** This gives the student a clean handoff point before the project changes direction into more complex mechanics.

---

## Why This Phase 7 Structure Is Recommended

- [ ] **Treat Phase 7 as stabilization, not preparation for hidden future systems**
  - **Target File(s):** docs and small cleanup edits only
  - **Proposed Action:** Keep the implementation focused on truthfulness, readability, and verification instead of inventing future-facing scaffolding.
  - **OOP / Clean Code Justification:** This matches the explicit choice to skip Phase 6 and respects the project’s “NO OVERENGINEERING” rule.

- [ ] **Prefer tiny cleanups over structural rewrites**
  - **Target File(s):** touched `src/` files
  - **Proposed Action:** Only make the smallest architecture-safe edits needed to improve clarity or correctness.
  - **OOP / Clean Code Justification:** By Phase 7, the architecture should be stabilized, not reopened.

- [ ] **Optimize for lecturer readability**
  - **Target File(s):** `README.md`, `docs/architecture-current-baseline.md`, package docstrings
  - **Proposed Action:** Make it easy for another student, TA, or lecturer to understand how the refactored project is organized and how to run it.
  - **OOP / Clean Code Justification:** A well-structured OOP project should be explainable as well as functional.
