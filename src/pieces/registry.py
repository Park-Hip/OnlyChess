"""Simple registry for creating chess pieces by code."""

from ..constants import (
    ARCHBISHOP_CODE,
    BISHOP_CODE,
    CHANCELLOR_CODE,
    INQUISITOR_CODE,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
    WARDEN_CODE,
)
from .fused import Archbishop, Chancellor, Inquisitor, Warden
from .standard import Bishop, King, Knight, Pawn, Queen, Rook


_PIECE_REGISTRY = {
    PAWN_CODE: Pawn,
    KNIGHT_CODE: Knight,
    BISHOP_CODE: Bishop,
    ROOK_CODE: Rook,
    QUEEN_CODE: Queen,
    KING_CODE: King,
    ARCHBISHOP_CODE: Archbishop,
    CHANCELLOR_CODE: Chancellor,
    WARDEN_CODE: Warden,
    INQUISITOR_CODE: Inquisitor,
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
