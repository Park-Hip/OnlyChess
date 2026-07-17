"""Tests for standard piece metadata APIs."""

import unittest

from src.constants import BLACK, BISHOP_CODE, KNIGHT_CODE, PAWN_CODE, QUEEN_CODE, ROOK_CODE, WHITE
from src.pieces import Bishop, Knight, Pawn, Queen, Rook


class PieceMetadataTests(unittest.TestCase):
    """Verify standard pieces describe themselves consistently."""

    def test_standard_piece_codes_and_display_ids(self):
        pieces = [
            Pawn(WHITE, (6, 0)),
            Knight(WHITE, (7, 1)),
            Bishop(BLACK, (0, 2)),
            Rook(BLACK, (0, 0)),
            Queen(WHITE, (7, 3)),
        ]
        expected_codes = [PAWN_CODE, KNIGHT_CODE, BISHOP_CODE, ROOK_CODE, QUEEN_CODE]
        expected_display_ids = ["wp", "wN", "bB", "bR", "wQ"]

        self.assertEqual([piece.get_piece_code() for piece in pieces], expected_codes)
        self.assertEqual([piece.get_display_id() for piece in pieces], expected_display_ids)

    def test_standard_piece_material_values(self):
        self.assertEqual(Pawn(WHITE, (6, 0)).get_material_value(), 1)
        self.assertEqual(Knight(WHITE, (7, 1)).get_material_value(), 3)
        self.assertEqual(Bishop(WHITE, (7, 2)).get_material_value(), 3)
        self.assertEqual(Rook(WHITE, (7, 0)).get_material_value(), 5)
        self.assertEqual(Queen(WHITE, (7, 3)).get_material_value(), 9)

    def test_standard_piece_sprite_keys_follow_display_ids(self):
        self.assertEqual(Pawn(WHITE, (6, 0)).get_sprite_key(), "wp")
        self.assertEqual(Knight(WHITE, (7, 1)).get_sprite_key(), "wN")
        self.assertEqual(Bishop(BLACK, (0, 2)).get_sprite_key(), "bB")


if __name__ == "__main__":
    unittest.main()
