# Wave 3: Engine Core

**Status:** complete, 2026-07-17. Wave 3 creates a separate, generic rules engine. It does not
route the playable application through it yet; the old game remains both runnable and the
comparison oracle until cutover.

## What lives where

| Concern | Location | Responsibility |
|---|---|---|
| Definitions and instances | `src/engine/piece.py` | Separates immutable piece/status definitions from mutable pieces and status instances. |
| Geometry and state | `src/engine/board.py`, `state.py` | Owns board occupancy, sides, active side, and the action history. |
| State changes | `src/engine/actions.py` | Applies and reverses relocation, removal, replacement, status, and turn actions. |
| Rules | `src/engine/movegen.py`, `status.py` | Interprets generic `slide` and `leap`, threats, legality, and status restrictions. |
| Lifecycle | `src/engine/pipeline.py`, `bus.py` | Applies moves, emits capture facts, advances turns, records every action, and undoes the record. |

Content supplies IDs, movement parts, properties, and layouts. The engine never selects a chess
piece or base mod by name.

## The action rule in practice

`Pipeline.apply(move)` applies move actions, emits a capture event when relevant, appends an
`AdvanceTurn`, then applies status-expiry actions. The complete list is recorded together.
`undo_last()` reverses that same list in reverse order.

Undo therefore restores both board occupancy and turn-scoped status changes without asking an
effect to run again. Future effect verbs must emit actions, never mutate an `EngineState` directly.

## Fixture and oracle boundary

`tests/fixtures/wave3_mods/standard/` is intentionally not `mods/base/`. It describes the six
ordinary chess pieces using only `slide` and `leap`, proving the generic engine before `base:chess`
gains its code-mod verbs.

`tests/oracle/new_adapter.py` converts supported FEN positions into that fixture and compares UCI
move sets with the legacy adapter. The curated comparison covers the starting position, pawn
movement/capture, and a knight position. It deliberately excludes:

- castling and en passant, which are Wave 4 code-mod move types;
- promotion, which needs the Wave 4 choice/replacement contract;
- fusion, events, abilities, and resources, which belong to Wave 5.

An unsupported rule is not silently approximated. It remains outside the oracle set until the
mod vocabulary can express it.

## Verification

```powershell
uv run python -m unittest tests.engine.test_wave3 tests.oracle.test_wave3_adapter
python -m pytest
```

The focused tests prove the 20 legal opening moves, simulation, apply/undo, reversible
replacement, status expiry, and legacy/new adapter agreement. The full suite is the final
regression check before merging.

## Next boundary: Wave 4

Build `base:chess` as an ordinary mod. Its code registers castling and en-passant through the same
public `ModApi` a third-party mod receives; then add promotion, the complete standard-content
package, and the full standard-chess oracle scope.
