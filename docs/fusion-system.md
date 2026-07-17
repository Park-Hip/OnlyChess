# Fusion System

## Purpose

The fusion system is the signature capture-triggered mechanic in Chess Fusion. After an eligible real capture, the capturing piece transforms into a stronger fused piece.

The system uses `DynamicFusedPiece` to support endless fusions. A piece can absorb multiple enemy pieces and gain all their movement patterns simultaneously.

## Responsibility

The fusion subsystem is responsible for:

- checking that fusion is based on a real capture, not a simulated move
- recording the components absorbed by the capturing piece
- generating a `DynamicFusedPiece` that combines the moves of all its components
- handling special rules like not fusing with Kings
- keeping move simulation safe by avoiding fusion side effects during legal-move checks

## Main Classes And Files

- `src/fusion/manager.py`: contains `FusionManager`, the coordinator for fusion after a move.
- `src/pieces/dynamic_fused.py`: contains the `DynamicFusedPiece` class that inherits and unions moves from components.
- `src/game/post_move_systems/fusion.py`: contains `FusionPostMoveSystem`, which calls `FusionManager` during real post-move processing.

## When Fusion Can Happen

Fusion is attempted only when all of these are true:

- the move is a real move
- the move captured a piece
- the captured piece is not a King

## Fusion Rules

In the new Dynamic Fusion system, there is no hardcoded table of pairs (like `Knight` + `Bishop` = `Archbishop`). Instead, the capturing piece simply absorbs the piece code of the captured piece into its `fusion_components` list. 

When a `DynamicFusedPiece` calculates its possible moves, it iterates over all its components, temporarily instantiates a dummy piece for each, and unions their valid moves.

When a fused piece captures another piece, the captured piece's components are appended to the fused piece's components. 

## FusionManager Behavior

`FusionManager.handle_move(move)` is called by `FusionPostMoveSystem` after a real move is finalized. It first delegates basic eligibility to `_can_attempt_fusion(move)`.

If the move is eligible, the manager:

- extracts the `fusion_components` of the capturing piece (or defaults to its base code).
- extracts the `fusion_components` of the captured piece.
- merges them into a unique set of components.
- creates a new `DynamicFusedPiece` with these components.
- replaces the capturing piece on the destination square with the newly fused piece.

## Dynamic Fused Pieces

The `DynamicFusedPiece` class stores:

- `has_fused = True`
- `fusion_components` (list of base piece codes)
- `primary_component_code` (inherited from the original capturing piece)
- `material_value` (inherited from the primary component)

Its sprite rendering uses the primary component's base sprite but dynamically overlays the added movement codes (e.g. `+N+B`) over the sprite using the `generate_dynamic_sprite` helper in `src/ui/assets.py`.

## Interactions With Other Subsystems

Fusion is part of the ordered post-move pipeline for real moves. The default order is:

1. capture tracking
2. fusion
3. Action Point gain
4. shield expiry
5. event update

This order means capture summaries are updated before fusion changes the board piece. Fusion then replaces the piece before later systems finish the turn side effects.

Fusion also interacts with:

- `GameState.make_move()`: sets `move.is_real_move` before post-move systems run.
- legal move generation: simulated moves call `make_move()` without `is_real_move=True`, so fusion is skipped.
- material and movement systems: dynamic fused pieces return material value based on their primary base component.

## OOP Design Notes

The design uses simple OOP boundaries:

- `FusionManager` owns fusion orchestration.
- `DynamicFusedPiece` owns shared fused-piece movement logic.
- `FusionPostMoveSystem` connects fusion to the post-move pipeline.

This keeps fusion logic out of `GameState.make_move()` and avoids turning the main game state into a God Object. The design is intentionally basic: it uses normal classes, dynamic movement aggregation, and the existing piece registry rather than heavy metaprogramming.

## Risks And Limitations

Fusion is intentionally limited to real standard captures. Ability captures (like Bishop Snipe) update captured-piece summaries but do not trigger fusion. This keeps ability behavior simple, but it is a known difference from standard move captures.
