# Chess Fusion Phase 8 Action Points System Implementation Plan

**Goal:** Add a small Action Points system that active abilities can spend without turning `GameState` into a God Object.

## Scope

- Add `ActionPointTracker`.
- Award AP from real moves only.
- Display AP in player panels.
- Keep AP state independent from event and fusion logic.

## Tasks

- [x] Add AP constants.
- [x] Add `ActionPointTracker`.
- [x] Wire AP gain into the post-move pipeline.
- [x] Expose AP text in the panel renderer.
- [x] Add tracker and integration tests.

## Verification

- `python -m unittest discover -s tests/game -p "test_*.py" -v`
- `python -m unittest discover -s tests/ui -p "test_*.py" -v`
