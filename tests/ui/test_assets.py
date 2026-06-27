"""Tests for UI asset loading helpers."""

import unittest

from src.constants import (
    ARCHBISHOP_CODE,
    BLACK,
    BISHOP_CODE,
    CHANCELLOR_CODE,
    KING_CODE,
    KNIGHT_CODE,
    PAWN_CODE,
    QUEEN_CODE,
    ROOK_CODE,
    WHITE,
)
from src.ui.assets import build_image_path, get_standard_sprite_keys, load_images


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
            WHITE + ARCHBISHOP_CODE,
            WHITE + CHANCELLOR_CODE,
            BLACK + PAWN_CODE,
            BLACK + ROOK_CODE,
            BLACK + KNIGHT_CODE,
            BLACK + BISHOP_CODE,
            BLACK + KING_CODE,
            BLACK + QUEEN_CODE,
            BLACK + ARCHBISHOP_CODE,
            BLACK + CHANCELLOR_CODE,
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

    def test_default_load_images_includes_fused_piece_sprites(self):
        loaded_paths = []

        def fake_loader(path):
            loaded_paths.append(path)
            return path

        def fake_scaler(image, size):
            return (image, size)

        images = load_images(image_loader=fake_loader, scaler=fake_scaler, square_size=40)

        self.assertIn("images/wA.png", loaded_paths)
        self.assertIn("images/bC.png", loaded_paths)
        self.assertIn("wA", images)
        self.assertIn("bC", images)
        self.assertEqual(len(images), 16)


if __name__ == "__main__":
    unittest.main()
