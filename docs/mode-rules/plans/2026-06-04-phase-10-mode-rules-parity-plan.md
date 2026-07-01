# Chess Fusion Phase 10 Mode Rules Parity Implementation Plan

**Goal:** Bring the already implemented Advanced Mode systems closer to the exact behavior described in `mode.md`, while keeping the code basic, readable, and easy to explain for an OOP course project.

## Current Gap Summary

- Pawn Sprint currently allows 1-3 squares and requires the path to be clear, but `mode.md` requires exactly 3 squares, allows jumping over pieces, and only requires the landing square to be empty.
- Rook Shield blocks standard captures and Meteor Strike, but shield immunity should also protect pieces from Tai Xiu removal and Mat Quyen Cong Dan black-pawn elimination.
- Comeout promotes a pawn to a queen but does not preserve all temporary status fields.
- Tempo Burst allows the extra rook move, but ability use during the extra Tempo Burst action is not explicitly supported.
- Event execution currently happens during the post-move full-turn update; `mode.md` describes event resolution at the start of the event turn. This is a larger turn-flow change, so this phase will document the limitation and avoid risky main-loop churn unless tests show a simple safe seam.

## Scope

- Update Pawn Sprint rules.
- Add shield filtering for destruction/removal events.
- Preserve status effects during Comeout promotion.
- Add Tempo Burst ability-use support for the Tempo Burst rook.
- Add regression tests for each adjusted rule.
- Update documentation to note any remaining event-timing limitation if it is not changed in this phase.

## Tasks

- [x] **Task 1: Update Pawn Sprint to exactly match `mode.md`**
  - Require exactly 3 forward squares.
  - Allow jumping over intermediate pieces.
  - Require only the landing square to be empty.
  - Reject stunned pawns.

- [x] **Task 2: Make shield immunity cover removal events**
  - Exclude shielded pieces from Tai Xiu random removal.
  - Prevent Mat Quyen Cong Dan from eliminating shielded black pawns.
  - Keep transformation effects allowed, because `mode.md` says shields do not block transformation effects.

- [x] **Task 3: Preserve status fields in Comeout**
  - Promote the selected pawn to a queen.
  - Preserve dynamic status fields such as `has_moved`, `is_active`, `stunned_turns`, and `poisoned_turns`.

- [x] **Task 4: Allow Tempo Burst ability use**
  - Let the Tempo Burst rook use one ability during the pending extra action if AP permits.
  - Clear Tempo Burst after that ability resolves.
  - Keep the implementation simple and avoid adding a complex turn scheduler.

- [x] **Task 5: Verification**
  - Add or update unit tests for all adjusted rules.
  - Run Fusion, Abilities, Game, Events, and UI regression suites.

## Out of Scope

- Rebuilding the whole turn scheduler.
- Custom fused-piece art.
- New fusion pairs or new abilities.

## Timing Result

- [x] Event warning/execution timing now uses completed full turns to trigger at the start of the displayed turn: warning at displayed turn 9 and execution at displayed turn 10.

## Verification Commands

```bash
python -m unittest discover -s tests/abilities -p "test_*.py" -v
python -m unittest discover -s tests/events -p "test_*event*.py" -v
python -m unittest discover -s tests/fusion -p "test_*.py" -v
python -m unittest discover -s tests/game -p "test_*.py" -v
python -m unittest discover -s tests/ui -p "test_*.py" -v
```

## Post-Phase Update (2026-07-01)

Task 4 (Tempo Burst ability use) is now obsolete. Tempo Burst was replaced entirely by the `Warden` and `Inquisitor` fused pieces. All Tempo Burst state and logic has been removed from the codebase.

