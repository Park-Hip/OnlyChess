"""Menu rows use each mode's declared palette independently."""

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame as p

from src.runtime import ModeCatalogEntry
from src.ui.screens.menu_screen import MenuScreen


class MenuThemingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p.init()
        p.display.set_mode((960, 640))
        cls.fonts = {"title": p.font.Font(None, 24), "normal": p.font.Font(None, 16), "small": p.font.Font(None, 13)}
        cls._saves = tempfile.TemporaryDirectory()
        cls.saves = Path(cls._saves.name)

    @classmethod
    def tearDownClass(cls):
        cls._saves.cleanup()

    def test_each_row_uses_its_mode_palette(self):
        modes = (
            ModeCatalogEntry("a:mode", "A", 6, 6, {"panel": "#112233", "selection": "#ffffff", "text": "#ffffff", "background": "#000000", "accent": "#ffffff"}),
            ModeCatalogEntry("b:mode", "B", 6, 6, {"panel": "#334455", "selection": "#ffffff", "text": "#ffffff", "background": "#000000", "accent": "#ffffff"}),
        )
        shared = SimpleNamespace(
            fonts=self.fonts,
            menu_background=p.Surface((960, 640)),
            app_context=SimpleNamespace(modes=modes),
            # The menu offers to continue a saved game, so it needs somewhere to look for one.
            # A temporary directory keeps this test blind to whatever is in the repository.
            settings_root=self.saves,
        )
        surface = p.Surface((960, 640))
        screen = MenuScreen(shared)
        screen.draw(surface)

        self.assertEqual(p.Color("#112233"), surface.get_at((screen._row_rect(0).x + 5, screen._row_rect(0).y + 5)))
        self.assertEqual(p.Color("#334455"), surface.get_at((screen._row_rect(1).x + 5, screen._row_rect(1).y + 5)))


if __name__ == "__main__":
    unittest.main()
