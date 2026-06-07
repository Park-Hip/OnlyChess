"""Knight Swap ability."""

from ..constants import KNIGHT_CODE
from .base import Ability
from .registry import register_ability


@register_ability
class KnightSwap(Ability):
    """Swap a knight with a friendly piece."""

    ability_key = "knight_swap"
    display_name = "Knight Swap"
    ap_cost = 2
    owner_piece_codes = (KNIGHT_CODE,)

    def is_valid_target(self, game_state, piece, target_square):
        target = game_state.board.get_piece_at(target_square[0], target_square[1])
        return target is not None and target is not piece and target.color == piece.color

    def apply(self, game_state, piece, target_square):
        target = game_state.board.get_piece_at(target_square[0], target_square[1])
        source_square = piece.pos
        game_state.board.replace_piece_at(source_square[0], source_square[1], target)
        game_state.board.replace_piece_at(target_square[0], target_square[1], piece)
        game_state._update_king_position_after_piece_relocation(piece)
        game_state._update_king_position_after_piece_relocation(target)
