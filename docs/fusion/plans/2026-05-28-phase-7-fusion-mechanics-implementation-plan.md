# Chess Fusion Phase 7 Fusion Mechanics Implementation Plan

**Goal:** Add capture-based fusion while keeping core move execution readable and simulation-safe.

## Scope

- Add fusion pair lookup rules.
- Add `FusionManager` as the post-move fusion coordinator.
- Add fused pieces as normal piece classes.
- Add Tempo Burst as the Rook + Bishop fusion result.

## Tasks

- [x] Add fusion constants and pair lookup.
- [x] Add `Archbishop` and `Chancellor` piece classes.
- [x] Register fused pieces through the piece registry.
- [x] Resolve fusion only after real captures.
- [x] Prevent simulated move generation from triggering fusion.
- [x] Add Tempo Burst state and UI text.
- [x] Add regression tests for rules, manager behavior, fused pieces, and Tempo Burst.

## Verification

- `python -m unittest discover -s tests/fusion -p "test_*.py" -v`
- `python -m unittest discover -s tests/pieces -p "test_*.py" -v`

## Post-Phase Update (2026-07-01)

Tempo Burst was later replaced by two new fused pieces:
- `Warden` (Rook captures Bishop): unlimited orthogonal + max 3 sq. diagonal
- `Inquisitor` (Bishop captures Rook): unlimited diagonal + max 3 sq. orthogonal

All Tempo Burst state and logic was removed from `GameState`, `FusionManager`, and the UI.

