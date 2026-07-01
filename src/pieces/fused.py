"""Fused chess piece classes."""

from ..constants import ARCHBISHOP_CODE, BISHOP_CODE, CHANCELLOR_CODE, KNIGHT_CODE, ROOK_CODE
from .base import Piece
from .standard import Bishop, Knight, Rook


class FusedPiece:
    """Mixin for pieces made from a fusion capture."""

    component_codes = ()

    def __init__(self, color, name, pos):
        Piece.__init__(self, color, name, pos)
        self.has_fused = True
        self.fusion_components = list(self.component_codes)
        self.primary_component_code = self.component_codes[0]

    def can_fuse(self):
        """Fused pieces cannot trigger another fusion."""
        return False

    def get_fusion_tags(self):
        """Return the component codes that grant abilities."""
        return list(self.fusion_components)

    def get_sprite_key(self):
        """Use the fused piece sprite key."""
        return self.get_display_id()

    def _get_knight_moves(self, gs):
        """Generate knight-style moves for fused pieces."""
        return Knight._calculate_moves(self, gs)

    def _get_bishop_moves(self, gs):
        """Generate bishop-style moves for fused pieces."""
        return Bishop._calculate_moves(self, gs)

    def _get_rook_moves(self, gs):
        """Generate rook-style moves for fused pieces."""
        return Rook._calculate_moves(self, gs)


class Archbishop(FusedPiece, Bishop):
    """Fused Knight + Bishop piece."""

    piece_code = ARCHBISHOP_CODE
    material_value = 6
    component_codes = (KNIGHT_CODE, BISHOP_CODE)

    def __init__(self, color, pos):
        super().__init__(color, ARCHBISHOP_CODE, pos)

    def _calculate_moves(self, gs):
        return self._get_bishop_moves(gs) + self._get_knight_moves(gs)


class Chancellor(FusedPiece, Rook):
    """Fused Rook + Knight piece."""

    piece_code = CHANCELLOR_CODE
    material_value = 8
    component_codes = (ROOK_CODE, KNIGHT_CODE)

    def __init__(self, color, pos):
        super().__init__(color, CHANCELLOR_CODE, pos)

    def _calculate_moves(self, gs):
        return self._get_rook_moves(gs) + self._get_knight_moves(gs)


class Warden(FusedPiece, Rook):
    """Fused Rook + Bishop piece (Heavy Rook).
    Moves orthogonally without limit, plus diagonally up to 3 squares.
    """

    piece_code = "W"
    material_value = 7
    component_codes = (ROOK_CODE, BISHOP_CODE)

    def __init__(self, color, pos):
        super().__init__(color, self.piece_code, pos)

    def _calculate_moves(self, gs):
        # Full Rook moves
        moves = self._get_rook_moves(gs)
        
        # Limited Bishop moves (max 3 squares, which means limit=4 for range(1, 4))
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        moves.extend(self._get_sliding_moves(gs, directions, limit=4))
        return moves


class Inquisitor(FusedPiece, Bishop):
    """Fused Bishop + Rook piece (Heavy Bishop).
    Moves diagonally without limit, plus orthogonally up to 3 squares.
    """

    piece_code = "I"
    material_value = 7
    component_codes = (BISHOP_CODE, ROOK_CODE)

    def __init__(self, color, pos):
        super().__init__(color, self.piece_code, pos)

    def _calculate_moves(self, gs):
        # Full Bishop moves
        moves = self._get_bishop_moves(gs)
        
        # Limited Rook moves (max 3 squares, which means limit=4 for range(1, 4))
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        moves.extend(self._get_sliding_moves(gs, directions, limit=4))
        return moves
