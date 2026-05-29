"""Rook Shield ability."""

from ..constants import ROOK_CODE
from .base import Ability
from .registry import register_ability


@register_ability
class RookShield(Ability):
    """Protect a rook and adjacent friendly pieces for one opponent turn."""

    ability_key = "rook_shield"
    display_name = "Rook Shield"
    ap_cost = 3
    owner_piece_codes = (ROOK_CODE,)

    def is_valid_target(self, game_state, piece, target_square):
        return target_square == piece.pos

    def apply(self, game_state, piece, target_square):
        for shielded_piece in self._collect_shield_targets(game_state, piece):
            game_state.add_shielded_piece(shielded_piece, piece.color)

    def _collect_shield_targets(self, game_state, piece):
        """Return the rook and adjacent friendly pieces."""
        targets = [piece]
        row, col = piece.pos
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            candidate = game_state.board.get_piece_at(row + dr, col + dc)
            if candidate is not None and candidate.color == piece.color:
                targets.append(candidate)
        return targets
