"""Pawn Sprint ability."""

from ..constants import BLACK, BOARD_ROWS, PAWN_CODE, QUEEN_CODE, WHITE
from ..pieces import create_piece
from .base import Ability
from .registry import register_ability


@register_ability
class PawnSprint(Ability):
    """Move a pawn exactly three forward squares, jumping over blockers."""

    ability_key = "pawn_sprint"
    display_name = "Pawn Sprint"
    ap_cost = 1
    owner_piece_codes = (PAWN_CODE,)

    def is_valid_target(self, game_state, piece, target_square):
        if piece.get_piece_code() != PAWN_CODE:
            return False
        if getattr(piece, "stunned_turns", 0) > 0:
            return False
        direction = -1 if piece.color == WHITE else 1
        row_delta = target_square[0] - piece.pos[0]
        if target_square[1] != piece.pos[1]:
            return False
        if row_delta != direction * 3:
            return False
        return game_state.board.get_piece_at(target_square[0], target_square[1]) is None

    def apply(self, game_state, piece, target_square):
        source_row, source_col = piece.pos
        game_state.board.set_piece_at(source_row, source_col, None)
        promotion_row = 0 if piece.color == WHITE else BOARD_ROWS - 1
        if target_square[0] == promotion_row:
            promoted_piece = create_piece(QUEEN_CODE, piece.color, target_square)
            promoted_piece.has_moved = True
            game_state.board.set_piece_at(target_square[0], target_square[1], promoted_piece)
        else:
            game_state.board.replace_piece_at(target_square[0], target_square[1], piece)
            piece.has_moved = True
