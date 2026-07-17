"""Tests for UI asset loading helpers."""

import unittest

from src.constants import (
    BLACK,
    BISHOP_CODE,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
    WHITE,
)
from src.ui.assets import build_image_path, get_standard_sprite_keys


class AssetHelperTests(unittest.TestCase):
    """Verify sprite key lists and image loading behavior."""

    def test_standard_sprite_keys_cover_all_standard_pieces(self):
        keys = get_standard_sprite_keys()

        expected = {
            WHITE + PAWN_CODE,
            WHITE + ROOK_CODE,
            WHITE + KNIGHT_CODE,
            WHITE + BISHOP_CODE,
            WHITE + KING_CODE,
            WHITE + QUEEN_CODE,
            BLACK + PAWN_CODE,
            BLACK + ROOK_CODE,
            BLACK + KNIGHT_CODE,
            BLACK + BISHOP_CODE,
            BLACK + KING_CODE,
            BLACK + QUEEN_CODE,
        }
        self.assertEqual(set(keys), expected)

    def test_build_image_path_uses_sprite_key(self):
        path = build_image_path("wQ").replace("\\", "/")
        self.assertTrue(path.endswith("images/wQ.png"))

    def test_standard_sprite_keys_count(self):
        """There should be exactly 12 standard sprites (6 pieces x 2 colors)."""
        keys = get_standard_sprite_keys()
        self.assertEqual(len(keys), 12)


if __name__ == "__main__":
    unittest.main()
