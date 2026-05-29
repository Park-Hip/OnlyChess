"""Pawn Sprint ability."""

from ..constants import BLACK, BOARD_ROWS, PAWN_CODE, QUEEN_CODE, WHITE
from ..pieces import create_piece
from .base import Ability
from .registry import register_ability


@register_ability
class PawnSprint(Ability):
    """Move a pawn up to three clear forward squares."""

    ability_key = "pawn_sprint"
    display_name = "Pawn Sprint"
    ap_cost = 1
    owner_piece_codes = (PAWN_CODE,)

    def is_valid_target(self, game_state, piece, target_square):
        if piece.get_piece_code() != PAWN_CODE:
            return False
        direction = -1 if piece.color == WHITE else 1
        row_delta = target_square[0] - piece.pos[0]
        if target_square[1] != piece.pos[1]:
            return False
        if row_delta == 0 or row_delta // direction not in (1, 2, 3):
            return False
        for step in range(1, abs(row_delta) + 1):
            row = piece.pos[0] + direction * step
            if game_state.board.get_piece_at(row, piece.pos[1]) is not None:
                return False
        return True

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
