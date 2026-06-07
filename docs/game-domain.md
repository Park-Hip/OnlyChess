# Game Domain

## Purpose

The game domain is the core chess engine for Chess Fusion. It owns board state, standard move execution, legal move validation, rollback for simulations, and the boundary between normal chess-domain rules and advanced systems such as fusion, Action Points, shields, abilities, and events.

This layer should answer chess questions first: where pieces are, whose turn it is, whether a move is legal, whether a king is in check, and how a normal move changes the board. Advanced systems are coordinated after real moves, but their concrete rules stay in their own packages.

## Responsibilities

The domain layer is responsible for:

- board setup and board mutation
- turn state through `white_to_move`
- legal move generation
- check, checkmate, and stalemate detection
- move execution
- simulation rollback
- castling rights
- en passant target tracking and capture resolution
- pawn promotion
- material scoring access
- post-move coordination for real moves

The domain layer is not responsible for:

- concrete event behavior
- concrete active ability behavior
- rendering
- mouse or keyboard input
- UI layout
- sprite loading

## Main Classes And Files

- `src/game/board.py`: defines `Board` and `GameState`; this is the main home for board state, move execution, rollback, legal move generation, turn state, king positions, and subsystem coordination.
- `src/game/move.py`: defines `Move`, the value object for one chess move plus special-move flags and rollback snapshot fields.
- `src/game/castling.py`: defines `CastleRights` and helpers for castling-right updates and king-specific move generation.
- `src/game/rules.py`: defines `run_post_move_systems()`, the simple ordered loop used after real moves.
- `src/game/post_move_systems/`: contains focused real-move side-effect systems for capture tracking, fusion, Action Point gain, shield expiry, and event updates.
- `src/game/action_points.py`: owns Action Point totals and move-count based AP gain.
- `src/game/capture_tracker.py`: records captured pieces for UI summaries and ability captures.
- `src/game/shield_tracker.py`: tracks temporary shields and expires them after the correct turn.
- `src/game/scoring.py`: calculates material advantage from the board grid.
- `src/game/state_helpers.py`: contains safe board-coordinate helper functions.

## Board

`Board` is a small mutable wrapper around the 8 by 8 grid. It sets up the classic starting position and gives the rest of the code named methods instead of direct coordinate manipulation everywhere.

Important helper methods:

- `get_piece_at(row, col)`: returns the piece at a square, or `None` when the coordinate is outside the board.
- `set_piece_at(row, col, piece)`: writes a piece or `None` to a valid square.
- `remove_piece_at(row, col)`: removes and returns the piece from a square.
- `replace_piece_at(row, col, piece)`: writes a piece and updates that piece's internal position.
- `is_inside_board(row, col)`: returns whether a coordinate is inside the board.

These helpers keep board access readable and make future board mutation rules easier to locate.

## GameState

`GameState` coordinates the playable state of one game. It owns the `Board` and the chess-domain fields that must stay consistent with the board.

Important owned state and helpers include:

- `board`: the mutable `Board`.
- `white_to_move`: the active side.
- `move_log`: half-turn history for moves and ability turns.
- `white_king_pos` and `black_king_pos`: cached king locations for check detection.
- `checkmate` and `stalemate`: end-state flags updated by valid-move generation.
- `enpassant_possible`: the en passant target square for the next move, or an empty tuple.
- `current_castle_rights` and `castle_rights_log`: current and historical castling state.
- `capture_tracker`: captured-piece summaries.
- `action_points`: Action Point state.
- `event_manager`: event timing and lifecycle coordination.
- `fusion_manager`: capture-based fusion coordination.
- `shield_tracker`: temporary shield state.
- `post_move_systems`: ordered systems that run after real moves.
- `tempo_burst_state`: pending Tempo Burst extra-move state.
- `ability_used_this_turn`: helper flag for ability turn flow.

`GameState` is central, but it delegates focused details to helper classes so the design remains understandable and expandable.

## Move Execution Flow

`GameState.make_move(move, promotion_choice='Q', is_real_move=False)` applies one move in a fixed order:

1. `_record_move_state(move)` stores previous state needed for rollback.
2. `_is_tempo_burst_move(move)` marks whether this move consumes a pending Tempo Burst move.
3. `_apply_base_piece_movement(move)` moves the piece from start square to end square.
4. `_resolve_en_passant_capture(move)` removes the pawn captured by en passant.
5. `_resolve_pawn_promotion(move, promotion_choice)` replaces a promoted pawn with the selected piece type.
6. `_update_en_passant_square(move)` sets or clears the next en passant target.
7. `_resolve_castle_rook_movement(move)` moves the rook for castling.
8. `_update_castle_state(move)` updates and logs castling rights.
9. `_finalize_move(move, is_real_move)` logs the move, flips the turn, updates king position, and runs real-move side effects when requested.

The default `is_real_move=False` matters because the same method is used for internal simulation during legal move filtering.

## Legal Move Generation

`get_valid_moves()` produces legal moves in two phases.

First, it calls `get_all_possible_moves()` to collect pseudo-legal moves for the side to move. `get_all_possible_moves()` normally scans the board, selects pieces whose color matches the active turn, and asks each piece for possible moves through `get_piece_moves()`. When `GameState.tempo_burst_state.pending` is true, generation is restricted to only the Tempo Burst piece stored in `tempo_burst_state.piece`.

Second, `get_valid_moves()` simulates each candidate move with `make_move()` using the default simulated mode. It temporarily flips `white_to_move` so `in_check()` evaluates the side that just moved. If that side's king is in check, the move is removed. The simulated move is then rolled back.

After filtering, `get_valid_moves()` updates `checkmate` or `stalemate` when no legal moves remain.

## Simulation And Rollback

Move simulation reuses `make_move()` with the default `is_real_move=False`. This lets legal move validation use the same movement logic as real play while skipping real side effects.

Rollback is handled by `_rollback_last_move()`. It restores:

- moved piece position and `has_moved`
- captured piece position and `has_moved`
- en passant captured pawn placement
- turn-local en passant state
- castling rights from `castle_rights_log`
- castling rook position and `has_moved`
- active side
- cached king position
- checkmate and stalemate flags

Because simulated moves are not real moves, post-move systems are skipped. Capture tracking, fusion, Action Point gain, shield expiry, and event updates must not happen during legal move filtering.

## Castling, En Passant, And Promotion

Castling is split between move generation and move execution. `CastleRights` stores whether each side can still castle king side or queen side. `update_castle_rights_for_move()` removes rights after king moves, rook moves, or rook captures. During execution, `_resolve_castle_rook_movement()` moves the rook to its castled square and records enough state for rollback.

En passant uses `GameState.enpassant_possible` as the target square for the next move. A double pawn move sets this target. Any other move clears it. An en passant `Move` stores the captured pawn from the adjacent square, and `_resolve_en_passant_capture()` removes that pawn from the board.

Promotion is detected in `Move` when a pawn reaches the last rank. `_resolve_pawn_promotion()` creates the selected promoted piece. Invalid promotion choices fall back to a queen.

## Post-Move Boundary

Real moves call `run_post_move_systems(game_state, move)` from `_finalize_move()`. The function is intentionally simple:

```python
for system in game_state.post_move_systems:
    system.apply(game_state, move)
```

The default order from `create_default_post_move_systems()` is:

1. capture tracking
2. fusion
3. Action Point gain
4. shield expiry
5. event update

This is the boundary between core chess-domain movement and advanced systems. `GameState` coordinates the loop, but concrete fusion behavior, event behavior, AP bookkeeping, and shield logic stay in their own classes.

After those real post-move systems run, a real Tempo Burst move clears pending Tempo Burst state.

## Interactions With Other Subsystems

Pieces provide movement rules through `get_possible_moves()`. `GameState` uses those rules, then removes moves that leave the current player's king in check.

Fusion is triggered after real captures through the post-move systems. `FusionManager` decides whether a capture produces a fused piece and applies the result.

Action Points are awarded after real moves and after successful ability turns. `ActionPointTracker` owns AP values and spend checks.

Events are timed by `EventManager`, but event-specific logic belongs to event classes. The game domain only calls the event update system after full-turn progress.

Abilities do not go through the exact normal real-move pipeline. A successful ability uses `finish_ability_turn(color)`, which records the ability turn, awards AP for that color, flips turn state, expires shields, and updates events when a full turn has completed.

The UI reads public state and calls domain operations, but it should not decide chess legality.

## OOP Design Notes

The design uses basic OOP:

- `Board` owns board storage and board mutation helpers.
- `Move` packages move data and rollback data.
- `GameState` coordinates the chess engine and composed helper objects.
- piece subclasses own their own movement rules.
- post-move system classes own focused real-move side effects.
- tracker and manager classes keep AP, captures, shields, fusion, and events out of one large method.

This keeps the code explainable for an OOP course while still supporting extension.

## Extension Points

Common extension points are:

- add a new piece or fused piece in `src/pieces/`, then register it through the piece registry.
- add a new fusion pair in `src/fusion/rules.py`.
- add a new real-move side effect by creating a post-move system and adding it to `create_default_post_move_systems()`.
- add a new event by creating a concrete event class and registering it.
- add a new ability by creating an ability class and registering it.
- add a new board helper in `Board` or `state_helpers.py` when several systems need the same safe board operation.

The goal is to add features by adding focused classes or registry entries instead of repeatedly modifying core move execution.

## Change Impact

Changes to `Board` affect every subsystem that reads or writes pieces.

Changes to `GameState.make_move()` affect real moves, simulated moves, rollback, legal move generation, and post-move systems.

Changes to `Move` affect move comparison, promotion detection, en passant, castling, fusion result tracking, and rollback.

Changes to castling rights or en passant state need matching rollback tests because legal move generation relies on exact simulation cleanup.

Changes to post-move system order can change visible gameplay results, especially around capture tracking, fusion, Action Point gain, shield expiry, and events.

## Risks And Limitations

`GameState` is still a central class. It is not a full God Object because many details are delegated, but it remains the main coordinator for board state, turn state, legal moves, rollback, and subsystem composition.

Move execution and rollback are high-risk areas. A new field added during `make_move()` may also need a rollback snapshot, or simulated legal move checks can leave hidden state behind.

The same `make_move()` method serves real moves and simulations. This reduces duplicate movement logic, but it makes the `is_real_move` boundary important.

Ability turns use `finish_ability_turn()` instead of the exact real-move pipeline. That keeps abilities separate from normal chess moves, but ability behavior must be checked when changing turn flow, AP gain, shield expiry, or event timing.
