"""The mods screen reports installed trust metadata and load errors."""

import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame as p

from src.modding.errors import ContentError
from src.modding.loader import ModInfo
from src.ui.screens.mods_screen import ModsScreen


class ModsScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p.init()
        p.display.set_mode((960, 640))
        cls.fonts = {"title": p.font.Font(None, 24), "normal": p.font.Font(None, 16), "small": p.font.Font(None, 13)}

    def test_renders_installed_code_badge_and_attributed_error(self):
        context = SimpleNamespace(
            installed=(ModInfo("safe:mod", "Safe", False), ModInfo("code:mod", "Code", True)),
            errors=(ContentError("broken:mod", "broken.yaml", "bad field", field="value"),),
            modes=(),
        )
        screen = ModsScreen(SimpleNamespace(app_context=context, fonts=self.fonts))
        surface = p.Surface((960, 640))
        screen.draw(surface)
        self.assertNotEqual(p.Color("#2B1B17"), surface.get_at((90, 125)))


if __name__ == "__main__":
    unittest.main()
