# Wave 4: `base:chess`

**Status:** complete, 2026-07-17. The shipped standard-chess content now runs through the target
engine without a privileged base-game route. The legacy application still owns the playable UI until
Wave 6; it remains the comparison implementation.

## The public extension proof

`mods/base-chess/code/__init__.py` receives the same `ModApi` as a third-party code mod and registers:

```python
api.move_type("castle", generate_castle, threatens=False)
api.move_type("enpassant", generate_enpassant)
```

The engine resolves an opaque `type:` relative to the piece's namespace, looks it up in the runtime
registry, and calls it with a restricted move-generation context. The context can read board state,
match a declared selector, inspect the last completed move, and construct reversible actions. It does
not give mod code a direct state-mutation API.

This keeps the ownership boundary honest: castle code knows its selected partner; core does not know
what a rook is. En-passant code knows the rule's prior-move condition; core only records a generic
completed move.

## Reversible standard-chess mechanics

| Rule | Recorded actions |
|---|---|
| Castling | two `Relocate` actions |
| En passant | `Remove` adjacent victim, then `Relocate` mover |
| Promotion | `Relocate`, then `Replace` with the selected declared definition |
| Ability | resource adjustment plus declared board/status actions, then turn advance |

Promotion options are data from the piece's `on: moved` declaration. A caller must supply one of the
declared choices; there is no hidden queen default. Every row above is undone by reversing the action
record, rather than re-running the rule.

## Content now interpreted

- `base:standard` and `base:vanilla` load with validation/linking.
- `base:shield` uses the generic status model.
- `base:ap` initializes per-side named resources and pays for abilities.
- The four declared base abilities use generic selectors/effects for destroy, swap, move, transform,
  and apply-status behavior. Ability use spends the acting side's turn.

This is intentionally the capability set exercised by `base:chess`, not a general event/fusion
interpreter. Those systems remain Wave 5.

## Oracle gate

`tests/oracle/new_adapter.py` builds its state from `base:chess`, not a test-only imitation. The
Wave 4 oracle checks published perft positions through depth 2, legal-play differential positions,
castling, en-passant, and all four promotion choices.

The `castling_through_attack` divergence remains explicit: the legacy engine offers an illegal castle
when a pawn attacks the transit square; the new threat path rejects it. No other disagreement is
accepted by the Wave 4 oracle.

## Verification

```powershell
uv run python -m unittest tests.oracle.test_wave4_oracle tests.engine.test_wave4_base_chess
python -m pytest
```

## Next boundary: Wave 5

Use the capture bus, selectors, conditions, and action-only effect machinery to load `base:fusion`
and `base:events`. The Wave 4 ability interpreter is evidence for the existing generic primitives,
not permission to special-case either content package.
