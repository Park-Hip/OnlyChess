"""Simple registry for creating chess pieces by code."""

from ..constants import (
    BISHOP_CODE,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
)
from .standard import Bishop, King, Knight, Pawn, Queen, Rook


_PIECE_REGISTRY = {
    PAWN_CODE: Pawn,
    KNIGHT_CODE: Knight,
    BISHOP_CODE: Bishop,
    ROOK_CODE: Rook,
    QUEEN_CODE: Queen,
    KING_CODE: King,
}


def create_piece(piece_code, color, pos):
    """Create a piece instance from a registered code."""
    piece_class = _PIECE_REGISTRY.get(piece_code)
    if piece_class is None:
        raise ValueError(f"Unknown piece code: {piece_code}")
    return piece_class(color, pos)


def get_registered_piece_codes():
    """Return the registered piece codes."""
    return tuple(_PIECE_REGISTRY.keys())
