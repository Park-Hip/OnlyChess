"""Milestone 3 loader contract for declarative presentation content."""

import tempfile
import unittest
from pathlib import Path
from dataclasses import FrozenInstanceError

from src.modding.loader import load
from src.presentation import PresentationNotification, PresentationSnapshot

from .builders import write_mod


class PresentationContractTests(unittest.TestCase):
    def test_owned_assets_and_presentation_references_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mod = write_mod(root, "present", manifest="id: present:demo\nname: Present\nversion: 1\ncode: false\n", files={
                "theme.yaml": "type: theme\nid: present:theme\nname: Theme\npalette: {background: '#000000', panel: '#111111', board_light: '#eeeeee', board_dark: '#777777', text: '#ffffff', accent: '#ffaa00', warning: '#ff0000', selection: '#00aaff', target: '#00ff00'}\n",
                "hud.yaml": "type: hud_layout\nid: present:hud\nname: HUD\nwidgets: [{type: turn, slot: top}]\n",
                "sound.yaml": "type: sound\nid: present:sound\nname: Sound\ncues: {move_completed: assets/sounds/move.ogg}\n",
            })
            asset = mod / "assets" / "sounds"; asset.mkdir(parents=True); (asset / "move.ogg").write_bytes(b"test")
            result = load(root, validate=True, link=True)
            self.assertTrue(result.ok, [error.format() for error in result.errors])

    def test_asset_path_outside_assets_is_an_attributed_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_mod(root, "bad", manifest="id: bad:demo\nname: Bad\nversion: 1\ncode: false\n", files={"sound.yaml": "type: sound\nid: bad:sound\nname: Bad\ncues: {move_completed: ../move.wav}\n"})
            result = load(root, validate=True)
            self.assertIn("relative path beneath assets", result.errors[0].problem)

    def test_presentation_boundary_records_are_immutable_data(self):
        snapshot = PresentationSnapshot("demo:mode", 1, 1, "Blue", (), (), (), None, None)
        notice = PresentationNotification("move_completed", "demo:mode")
        with self.assertRaises(FrozenInstanceError):
            snapshot.mode_id = "other:mode"
        with self.assertRaises(FrozenInstanceError):
            notice.kind = "undo_completed"


if __name__ == "__main__": unittest.main()
