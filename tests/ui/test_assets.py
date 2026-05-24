"""Tests for UI asset helpers."""

import unittest

from src.constants import BLACK, BISHOP_CODE, KING_CODE, KNIGHT_CODE, PAWN_CODE, QUEEN_CODE, ROOK_CODE, WHITE
from src.ui.assets import build_image_path, get_standard_sprite_keys, load_images


class AssetHelperTests(unittest.TestCase):
    """Verify asset lookup stays aligned with piece metadata."""

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
        self.assertEqual(build_image_path("wQ"), "images/wQ.png")

    def test_load_images_uses_loader_and_scaler_hooks(self):
        loaded_paths = []
        scaled_sizes = []

        def fake_loader(path):
            loaded_paths.append(path)
            return path

        def fake_scaler(image, size):
            scaled_sizes.append(size)
            return (image, size)

        images = load_images(
            sprite_keys=["wQ", "bK"],
            image_loader=fake_loader,
            scaler=fake_scaler,
            square_size=40,
        )

        self.assertEqual(loaded_paths, ["images/wQ.png", "images/bK.png"])
        self.assertEqual(scaled_sizes, [(40, 40), (40, 40)])
        self.assertIn("wQ", images)
        self.assertIn("bK", images)


if __name__ == "__main__":
    unittest.main()
