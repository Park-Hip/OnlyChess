from ..constants import PAWN_CODE, BOARD_SIZE, KING_CODE
from .base import Ability
from .registry import register_ability

@register_ability
class PawnKamikaze(Ability):
    ability_name = "pawn_kamikaze"
    display_name = "Pawn Kamikaze"
    ap_cost = 3
    owner_piece_codes = (PAWN_CODE,)
    requires_target = False

    def is_valid_target(self, game_state, piece, target_square):
        """Return whether a target square is valid for the ability."""
        return target_square == piece.pos

    def apply(self, game_state, piece, target_square):
        """Apply ability behavior."""
        row, col = piece.pos
        game_state.board.remove_piece_at(row, col)
        game_state.capture_tracker.record_capture(piece.color, piece)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == dc == 0: continue
                r, c = row + dr, col + dc
                target = game_state.board.get_piece_at(r, c)
                if target is not None and target.get_piece_code() != KING_CODE and not getattr(target, "is_shielded", False):
                    game_state.board.remove_piece_at(r, c)
                    game_state.capture_tracker.record_capture(target.color, target)
