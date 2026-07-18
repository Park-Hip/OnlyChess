"""Release gate: independent content plays through the ordinary runtime path."""

import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame as p

from src.runtime import ApplicationContext, EngineSession
from src.ui.screens.engine_game_screen import EngineGameScreen
from src.settings import Settings


class ReleaseProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p.init()
        cls.context = ApplicationContext.load()
        cls.fonts = {"title": p.font.Font(None, 24), "normal": p.font.Font(None, 16), "small": p.font.Font(None, 13)}

    def test_proof_mode_is_auto_discovered_and_uses_a_six_by_six_board(self):
        self.assertIn("proof:arena_mode", tuple(mode.id for mode in self.context.modes))
        session = EngineSession(self.context.load_result, "proof:arena_mode")
        self.assertEqual((6, 6), (session.state.board.rows, session.state.board.columns))
        self.assertEqual("proof:prism", session.state.board.at((5, 0)).definition.id)

    def test_proof_mode_renders_headlessly_with_its_theme(self):
        session = EngineSession(self.context.load_result, "proof:arena_mode")
        shared = type("Shared", (), {"fonts": self.fonts, "settings": Settings()})()
        screen = EngineGameScreen(shared, session=session)
        surface = p.Surface((960, 640))
        screen.draw(surface)
        self.assertEqual(p.Color("#111827"), surface.get_at((0, 0)))


if __name__ == "__main__": unittest.main()
