"""Milestone 6, slice 5: statuses render their declared `icon` sprite (not only a glyph),
and a piece carrying more than one visible status shows every one of them.

The proof mod is the fixture: `proof:glow` ships an owned icon, `proof:warded` ships a glyph
only. A piece wearing both must draw the glow via its icon and the ward via its glyph."""

import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame as p

from src.engine.piece import StatusInstance
from src.runtime import ApplicationContext, EngineSession
from src.ui.presentation_runtime import PresentationRuntime
from src.ui.screens.engine_game_screen import EngineGameScreen
from src.settings import Settings


class _RecordingFont:
    def __init__(self, real):
        self.real = real
        self.rendered = []

    def render(self, text, antialias, color):
        self.rendered.append(text)
        return self.real.render(text, antialias, color)


class StatusIconTests(unittest.TestCase):
    MODE = "proof:arena_mode"

    @classmethod
    def setUpClass(cls):
        p.init()
        p.display.set_mode((960, 640))  # convert_alpha() needs a video surface, as in the real app
        cls.context = ApplicationContext.load()

    def _runtime(self):
        return PresentationRuntime(self.context.load_result, self.MODE)

    def test_status_with_an_icon_loads_a_scaled_sprite(self):
        icon = self._runtime().status_icon("proof:glow", 20)
        self.assertIsNotNone(icon)
        self.assertEqual((20, 20), icon.get_size())

    def test_glyph_only_status_has_no_icon(self):
        runtime = self._runtime()
        self.assertIsNone(runtime.status_icon("proof:warded", 20))  # declares a glyph, no icon
        self.assertIsNone(runtime.status_icon("base:shield", 20))   # declares no presentation at all

    def test_status_presentation_reports_visibility(self):
        runtime = self._runtime()
        self.assertTrue(runtime.status_presentation("proof:glow")["visible"])
        # base:shield declared no presentation until 2026-07-19, which meant a protected piece
        # looked exactly like an unprotected one — a rule the player could not see.
        self.assertTrue(runtime.status_presentation("base:shield")["visible"])

    def test_two_visible_statuses_both_render_icon_and_glyph(self):
        recording = _RecordingFont(p.font.Font(None, 13))
        fonts = {"title": p.font.Font(None, 24), "normal": p.font.Font(None, 16), "small": recording}
        session = EngineSession(self.context.load_result, self.MODE)
        shared = type("Shared", (), {"fonts": fonts, "settings": Settings()})()
        screen = EngineGameScreen(shared, session=session)

        piece = next(iter(session.state.board.pieces()))
        piece.statuses["proof:glow"] = StatusInstance(session.state.status_defs["proof:glow"], 2)
        piece.statuses["proof:warded"] = StatusInstance(session.state.status_defs["proof:warded"], 2)

        screen.draw(p.Surface((960, 640)))

        # The ward (glyph-only) drew its glyph; the glow drew via its icon, so it never
        # fell through to rendering its own "*" glyph.
        self.assertIn("+", recording.rendered)
        self.assertNotIn("*", recording.rendered)


if __name__ == "__main__":
    unittest.main()
