"""Milestone 6, slice 1: the game screen renders the mod's declared HUD widgets, not a
hardcoded panel. Removing a widget from the layout removes it from screen with no code change."""

import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame as p

from src.runtime import ApplicationContext, EngineSession
from src.ui.screens.engine_game_screen import EngineGameScreen
from src.settings import Settings


class _RecordingFont:
    """Wraps a real font and records the text of every render() call."""

    def __init__(self, real):
        self.real = real
        self.rendered = []

    def render(self, text, antialias, color):
        self.rendered.append(text)
        return self.real.render(text, antialias, color)


class HudRenderingTests(unittest.TestCase):
    MODE = "proof:arena_mode"
    BACKGROUND = p.Color("#111827")  # proof theme background

    @classmethod
    def setUpClass(cls):
        p.init()
        cls.context = ApplicationContext.load()

    def _fonts(self):
        return {"title": p.font.Font(None, 24), "normal": p.font.Font(None, 16), "small": p.font.Font(None, 13)}

    def _screen(self, fonts=None):
        session = EngineSession(self.context.load_result, self.MODE)
        shared = type("Shared", (), {"fonts": fonts or self._fonts(), "settings": Settings()})()
        return EngineGameScreen(shared, session=session)

    def test_declared_side_widgets_draw_the_panel(self):
        screen = self._screen()
        surface = p.Surface((960, 640))
        screen.draw(surface)
        layout = screen._layout(surface)
        # The proof HUD declares resources + log in the side slot, so the panel background is drawn.
        self.assertNotEqual(self.BACKGROUND, surface.get_at(layout.side.center))

    def test_removing_side_widgets_removes_the_panel_with_no_code_change(self):
        screen = self._screen()
        # Same code path; the only change is the declared widget list — as a mod edit would do.
        screen.presentation.hud_widgets = lambda: [
            {"type": "turn", "slot": "top"},
            {"type": "prompt", "slot": "bottom"},
        ]
        surface = p.Surface((960, 640))
        screen.draw(surface)
        layout = screen._layout(surface)
        self.assertEqual(self.BACKGROUND, surface.get_at(layout.side.center))

    def test_log_widget_honors_max_lines(self):
        recording = _RecordingFont(p.font.Font(None, 13))
        fonts = {"title": p.font.Font(None, 24), "normal": p.font.Font(None, 16), "small": recording}
        screen = self._screen(fonts)
        screen.presentation.hud_widgets = lambda: [{"type": "log", "slot": "side", "max_lines": 3}]
        for index in range(6):
            screen.session.state.event_messages.append(f"message-{index}")
        screen.draw(p.Surface((960, 640)))
        # Only the last three messages are rendered; older ones are dropped.
        self.assertIn("message-5", recording.rendered)
        self.assertIn("message-3", recording.rendered)
        self.assertNotIn("message-2", recording.rendered)


if __name__ == "__main__":
    unittest.main()
