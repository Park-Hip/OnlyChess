# Chess Fusion Phase 9 Piece Abilities Implementation Plan

**Goal:** Add basic active abilities using AP while keeping each ability as a small, explainable class.

## Scope

- Add a simple ability base class and registry.
- Implement Knight Swap, Bishop Snipe, Rook Shield, and Pawn Sprint.
- Add right-click ability menu UI.
- Keep ability captures separate from fusion triggers.

## Tasks

- [x] Add ability base contract and registry.
- [x] Implement Knight Swap.
- [x] Implement Bishop Snipe.
- [x] Implement Rook Shield.
- [x] Implement Pawn Sprint.
- [x] Add ability menu helpers and input state.
- [x] Add ability tests and UI helper tests.

## Verification

- `python -m unittest discover -s tests/abilities -p "test_*.py" -v`
- `python -m unittest discover -s tests/ui -p "test_*.py" -v`
