"""Wave 2's end-to-end contract: selected data reaches a linked renderable layout."""

from pathlib import Path
import tempfile
import unittest

from src.modding.errors import ModLoadError
from src.modding.loader import activate, load
from src.ui.mod_preview import load_preview_images, sprite_path

from .builders import data_mod


REPO_ROOT = Path(__file__).resolve().parents[2]


class WalkingSkeletonTests(unittest.TestCase):
    """Keep the first vertical slice independent from the legacy GameState."""

    def test_selected_skeleton_activates_and_links_one_placed_piece(self):
        result = load(REPO_ROOT / "mods", enabled_mod_ids=("skeleton:demo",), validate=True, link=True)

        self.assertEqual(result.errors, [])
        self.assertEqual(result.mods, ("skeleton:demo",))
        self.assertIn("skeleton:preview", activate(result).content["game_mode"])
        placement = result.linked.modes["skeleton:preview"].board.placements
        self.assertEqual(placement[0].piece_id, "skeleton:beacon")
        self.assertEqual(placement[0].side_id, "skeleton:blue")

    def test_selected_mod_does_not_load_an_unselected_broken_mod(self):
        with tempfile.TemporaryDirectory() as directory:
            mods = Path(directory)
            data_mod(
                mods,
                "good",
                "good:demo",
                pieces__beacon="type: piece\nid: good:beacon\nname: Beacon\nsprite: good:beacon\nmoves: []\n",
                board__preview=(
                    "type: board\nid: good:board\nsize: [1, 1]\nsides:\n"
                    "  - { id: good:blue, name: Blue, forward: down, promotes_at: 0, moves_first: true }\n"
                    "rows:\n  - { row: 0, side: good:blue, pieces: [good:beacon] }\n"
                ),
                modes__preview="type: game_mode\nid: good:preview\nname: Good\nboard: good:board\npools: []\n",
            )
            data_mod(mods, "broken", "broken:demo", pieces__bad="type: piece\nid: broken:bad\n")

            result = load(mods, enabled_mod_ids=("good:demo",), validate=True, link=True)
            self.assertEqual(result.errors, [])
            self.assertEqual(result.mods, ("good:demo",))

    def test_missing_placed_piece_is_an_attributed_link_error(self):
        with tempfile.TemporaryDirectory() as directory:
            mods = Path(directory)
            data_mod(
                mods,
                "bad",
                "bad:demo",
                board__preview=(
                    "type: board\nid: bad:board\nsize: [1, 1]\nsides:\n"
                    "  - { id: bad:blue, name: Blue, forward: down, promotes_at: 0, moves_first: true }\n"
                    "rows:\n  - { row: 0, side: bad:blue, pieces: [bad:missing] }\n"
                ),
                modes__preview="type: game_mode\nid: bad:preview\nname: Bad\nboard: bad:board\npools: []\n",
            )
            result = load(mods, enabled_mod_ids=("bad:demo",), validate=True, link=True)

            self.assertEqual(result.errors[0].field, "rows[0].pieces[0]")
            self.assertIn("bad:missing", result.errors[0].problem)

    def test_mod_asset_path_is_namespaced_but_windows_safe(self):
        path = sprite_path("skeleton:beacon", "skeleton:blue", REPO_ROOT / "mods" / "skeleton")
        self.assertEqual(path, REPO_ROOT / "mods" / "skeleton" / "assets" / "sprites" / "beacon" / "skeleton" / "blue.png")
        self.assertNotIn(":", path.name)

    def test_preview_loads_mod_owned_sprite_without_a_legacy_fallback(self):
        result = load(REPO_ROOT / "mods", enabled_mod_ids=("skeleton:demo",), validate=True, link=True)
        loaded_paths = []

        images = load_preview_images(
            result,
            "skeleton:preview",
            image_loader=lambda path: loaded_paths.append(path) or path,
            scaler=lambda image, size: (image, size),
            square_size=32,
        )

        self.assertEqual(len(loaded_paths), 1)
        self.assertTrue(loaded_paths[0].endswith("assets\\sprites\\beacon\\skeleton\\blue.png"))
        self.assertEqual(images[("skeleton:beacon", "skeleton:blue")][1], (32, 32))

    def test_missing_sprite_is_a_fatal_content_error(self):
        result = load(REPO_ROOT / "mods", enabled_mod_ids=("skeleton:demo",), validate=True, link=True)
        with tempfile.TemporaryDirectory() as directory:
            result.mod_roots["skeleton:demo"] = Path(directory)
            with self.assertRaises(ModLoadError) as raised:
                load_preview_images(result, "skeleton:preview")
        self.assertIn("sprite file is missing", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
