# Fusion System

## Purpose

The fusion system is the signature capture-triggered mechanic in Chess Fusion. After an eligible real capture, the capturing piece transforms into a stronger fused piece.

The current implementation keeps fusion separate from normal chess movement. `GameState` still owns the board and turn flow, while `FusionManager` owns the decision about whether a capture should create a fusion result.

## Responsibility

The fusion subsystem is responsible for:

- checking that fusion is based on a real capture, not a simulated move
- checking whether the capturing piece can still fuse
- looking up valid fusion results from a simple rules table
- replacing the capturing piece with the fused piece
- preventing repeated fusion from an already fused piece
- keeping move simulation safe by avoiding fusion side effects during legal-move checks

## Main Classes And Files

- `src/fusion/manager.py`: contains `FusionManager`, the coordinator for fusion after a move.
- `src/fusion/rules.py`: contains `FUSION_RESULTS` and `get_fusion_result()`.
- `src/pieces/fused.py`: contains the `FusedPiece` mixin plus `Archbishop`, `Chancellor`, `Warden`, and `Inquisitor`.
- `src/pieces/registry.py`: registers fused pieces so `create_piece()` can build them by code.
- `src/game/post_move_systems/fusion.py`: contains `FusionPostMoveSystem`, which calls `FusionManager` during real post-move processing.

## When Fusion Can Happen

Fusion is attempted only when all of these are true:

- the move is a real move
- the move captured a piece
- the capturing piece returns `True` from `can_fuse()`
- the capturing and captured piece codes exist as a pair in `FUSION_RESULTS`

If any requirement fails, fusion does nothing and the normal capture result stays on the board.

## Fusion Rules

The current `FUSION_RESULTS` mapping is:

| Capturing Piece | Captured Piece | Result |
| --- | --- | --- |
| Knight | Bishop | `Archbishop` |
| Bishop | Knight | `Archbishop` |
| Rook | Knight | `Chancellor` |
| Knight | Rook | `Chancellor` |
| Rook | Bishop | `Warden` |
| Bishop | Rook | `Inquisitor` |

Fusion now covers both capture directions. For the Knight/Bishop and Rook/Knight combinations, either direction produces the same fused piece. The Rook/Bishop combination is direction-sensitive: a Rook capturing a Bishop becomes a `Warden` (a heavy rook), while a Bishop capturing a Rook becomes an `Inquisitor` (a heavy bishop).

When the captured piece is already fused, `FusionManager` uses its `primary_component_code` for matching. This lets a base piece interact with a fused target using the target's main component instead of the fused piece code.

## FusionManager Behavior

`FusionManager.handle_move(move)` is called by `FusionPostMoveSystem` after a real move is finalized. It first delegates basic eligibility to `_can_attempt_fusion(move)`.

If the move is eligible, the manager:

- reads the capturing piece code
- reads the captured piece code or captured fused piece primary component code
- calls `get_fusion_result(capturing_code, captured_code)`
- returns `None` when no rule exists
- marks the capturing piece as fused when a rule exists
- creates the fused piece and replaces the capturing piece on the destination square

`_replace_with_fused_piece()` creates the new piece through the shared piece registry, marks it as moved, stores its fusion components, sets its primary component code, replaces the board square, and records the new object on `move.fused_to_piece`.

## Fused Pieces

`FusedPiece` is a small mixin used by fused piece classes. It stores:

- `has_fused = True`
- `fusion_components`
- `primary_component_code`

It also overrides `can_fuse()` to return `False`, which prevents chained fusion from a fused piece, and exposes helpers (`_get_knight_moves`, `_get_bishop_moves`, `_get_rook_moves`) so fused classes reuse the standard movement logic instead of duplicating movement algorithms.

The four fused pieces are:

- `Archbishop` (Knight + Bishop): combines bishop-style diagonal moves with knight-style jumps.
- `Chancellor` (Rook + Knight): combines rook-style straight moves with knight-style jumps.
- `Warden` (Rook + Bishop): a heavy rook that moves orthogonally without limit and diagonally up to 3 squares.
- `Inquisitor` (Bishop + Rook): a heavy bishop that moves diagonally without limit and orthogonally up to 3 squares.

The limited-range moves for `Warden` and `Inquisitor` reuse `Piece._get_sliding_moves()` with its `limit` argument, so no new movement algorithm is introduced.

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
- the piece registry: fused piece results are created through `create_piece()`.
- material and movement systems: fused pieces behave as normal pieces once placed on the board.

## OOP Design Notes

The design uses simple OOP boundaries:

- `FusionManager` owns fusion orchestration.
- `rules.py` owns the fusion pair table.
- `FusedPiece` owns shared fused-piece behavior.
- `Archbishop`, `Chancellor`, `Warden`, and `Inquisitor` own their movement combinations.
- `FusionPostMoveSystem` connects fusion to the post-move pipeline.

This keeps fusion logic out of `GameState.make_move()` and avoids turning the main game state into a God Object. The design is intentionally basic: it uses normal classes, a dictionary lookup, and the existing piece registry rather than heavier patterns.

## Extension Points

To add a new fusion pair that returns an existing result, update `FUSION_RESULTS` in `src/fusion/rules.py` and add tests for the new valid and invalid pair behavior.

To add a new fused piece type:

- add a constant for the new piece code
- add a class in `src/pieces/fused.py`
- register the class in `src/pieces/registry.py`
- add a mapping in `FUSION_RESULTS`
- add the sprite art in `images/` and its key in `src/ui/assets.py`
- add tests for creation, movement, and fusion eligibility

## Change Impact

Adding a new pair for an existing result is low impact because the rules table is isolated.

Adding a brand-new fused piece has medium impact because constants, fused piece classes, the registry, fusion rules, sprites, and tests may need updates.

Changing fusion timing or eligibility has higher impact because it affects `FusionManager`, real move processing, simulation safety, and post-move system ordering.

## Risks And Limitations

Fusion is intentionally limited to real standard captures. Ability captures update captured-piece summaries but do not trigger fusion. This keeps ability behavior simple, but it is a known difference from standard move captures.

Fusion pair lookup is keyed on the ordered `(capturing, captured)` codes. Both directions are listed explicitly in `FUSION_RESULTS`, which is what lets the Rook/Bishop pair resolve to different pieces depending on which side captures.

Each fused piece has dedicated sprite art in `images/` (`A`, `C`, `W`, and `I` in both colors), loaded through the standard sprite keys in `src/ui/assets.py`.
