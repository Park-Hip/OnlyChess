"""Tests for future-facing piece extension hooks."""

import unittest

from src.constants import BLACK, WHITE
from src.pieces import Bishop, King, Knight, Pawn, Queen, Rook


class PieceExtensionHookTests(unittest.TestCase):
    """Verify future-facing hooks stay predictable for standard pieces."""

    def test_minor_piece_flags_match_standard_chess_roles(self):
        self.assertFalse(Pawn(WHITE, (6, 0)).is_minor_piece())
        self.assertTrue(Knight(WHITE, (7, 1)).is_minor_piece())
        self.assertTrue(Bishop(WHITE, (7, 2)).is_minor_piece())
        self.assertFalse(Rook(WHITE, (7, 0)).is_minor_piece())
        self.assertFalse(Queen(WHITE, (7, 3)).is_minor_piece())
        self.assertFalse(King(WHITE, (7, 4)).is_minor_piece())

    def test_can_fuse_defaults_for_standard_pieces(self):
        self.assertTrue(Pawn(WHITE, (6, 0)).can_fuse())
        self.assertTrue(Knight(WHITE, (7, 1)).can_fuse())
        self.assertTrue(Bishop(BLACK, (0, 2)).can_fuse())
        self.assertTrue(Rook(BLACK, (0, 0)).can_fuse())
        self.assertTrue(Queen(WHITE, (7, 3)).can_fuse())
        self.assertFalse(King(WHITE, (7, 4)).can_fuse())

    def test_fusion_tags_and_move_profile_names_are_defined(self):
        knight = Knight(WHITE, (7, 1))
        self.assertEqual(knight.get_fusion_tags(), ["N"])
        self.assertEqual(knight.get_move_profile_name(), "Knight")


if __name__ == "__main__":
    unittest.main()
