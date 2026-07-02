"""Tests for the piece registry."""

import unittest

from src.constants import (
    ARCHBISHOP_CODE,
    BISHOP_CODE,
    BLACK,
    CHANCELLOR_CODE,
    INQUISITOR_CODE,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
    WARDEN_CODE,
    WHITE,
)
from src.pieces import Archbishop, Bishop, Chancellor, King, Knight, Pawn, Queen, Rook, create_piece, get_registered_piece_codes


class PieceRegistryTests(unittest.TestCase):
    """Verify registry-based piece creation."""

    def test_registry_creates_all_standard_pieces(self):
        self.assertIsInstance(create_piece(PAWN_CODE, WHITE, (6, 0)), Pawn)
        self.assertIsInstance(create_piece(KNIGHT_CODE, WHITE, (7, 1)), Knight)
        self.assertIsInstance(create_piece(BISHOP_CODE, BLACK, (0, 2)), Bishop)
        self.assertIsInstance(create_piece(ROOK_CODE, BLACK, (0, 0)), Rook)
        self.assertIsInstance(create_piece(QUEEN_CODE, WHITE, (7, 3)), Queen)
        self.assertIsInstance(create_piece(KING_CODE, BLACK, (0, 4)), King)
        self.assertIsInstance(create_piece(ARCHBISHOP_CODE, WHITE, (4, 4)), Archbishop)
        self.assertIsInstance(create_piece(CHANCELLOR_CODE, BLACK, (3, 3)), Chancellor)

    def test_registry_reports_registered_piece_codes(self):
        self.assertEqual(
            set(get_registered_piece_codes()),
            {
                PAWN_CODE,
                KNIGHT_CODE,
                BISHOP_CODE,
                ROOK_CODE,
                QUEEN_CODE,
                KING_CODE,
                ARCHBISHOP_CODE,
                CHANCELLOR_CODE,
                WARDEN_CODE,
                INQUISITOR_CODE,
            },
        )

    def test_registry_rejects_unknown_codes(self):
        with self.assertRaises(ValueError):
            create_piece("X", WHITE, (0, 0))


if __name__ == "__main__":
    unittest.main()
