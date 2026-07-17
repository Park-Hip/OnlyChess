"""Bishop Snipe ability."""

from ..constants import BISHOP_CODE, KING_CODE
from .base import Ability, is_enemy_piece
from .registry import register_ability


@register_ability
class BishopSnipe(Ability):
    """Capture an enemy along an unobstructed diagonal without moving."""

    ability_key = "bishop_snipe"
    display_name = "Bishop Snipe"
    ap_cost = 3
    owner_piece_codes = (BISHOP_CODE,)

    def is_valid_target(self, game_state, piece, target_square):
        target = game_state.board.get_piece_at(target_square[0], target_square[1])
        if not is_enemy_piece(piece, target):
            return False
        if target.get_piece_code() == KING_CODE:
            return False
        if getattr(target, "is_shielded", False):
            return False
        row_delta = target_square[0] - piece.pos[0]
        col_delta = target_square[1] - piece.pos[1]
        if abs(row_delta) != abs(col_delta):
            return False
        row_step = 1 if row_delta > 0 else -1
        col_step = 1 if col_delta > 0 else -1
        row = piece.pos[0] + row_step
        col = piece.pos[1] + col_step
        while (row, col) != target_square:
            if game_state.board.get_piece_at(row, col) is not None:
                return False
            row += row_step
            col += col_step
        return True

    def apply(self, game_state, piece, target_square):
        captured_piece = game_state.board.remove_piece_at(target_square[0], target_square[1])
        game_state.capture_tracker.record_capture(piece.color, captured_piece)
