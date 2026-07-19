"""Milestone 6, slice 3: restart and back-to-menu are application-shell chrome, reachable
both from the outcome screen and during normal play. Restart must build a brand-new
EngineSession (a fresh, empty action log) rather than reversing or replaying the old one."""

import os
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame as p

from src.runtime import ApplicationContext, EngineSession
from src.ui.screens.engine_game_screen import EngineGameScreen
from src.ui.screens.menu_screen import MenuScreen
from src.settings import Settings


class ShellNavigationTests(unittest.TestCase):
    MODE = "base:vanilla"

    @classmethod
    def setUpClass(cls):
        cls._saves = tempfile.TemporaryDirectory()
        cls.saves = Path(cls._saves.name)
        p.init()
        cls.context = ApplicationContext.load()

    @classmethod
    def tearDownClass(cls):
        cls._saves.cleanup()

    def _fonts(self):
        return {"title": p.font.Font(None, 24), "normal": p.font.Font(None, 16), "small": p.font.Font(None, 13)}

    def _screen(self):
        session = EngineSession(self.context.load_result, self.MODE)
        shared = type("Shared", (), {"fonts": self._fonts(), "app_context": self.context, "settings": Settings(), "settings_root": self.saves})()
        return EngineGameScreen(shared, session=session)

    def test_restart_builds_a_fresh_session_with_an_empty_action_log(self):
        screen = self._screen()
        move = screen.session.legal_moves[0]
        screen.session.move(move.start, move.end)
        self.assertEqual(1, len(screen.session.state.action_log))
        old_session = screen.session

        screen._restart()

        self.assertIsInstance(screen.next_screen, EngineGameScreen)
        new_session = screen.next_screen.session
        self.assertIsNot(new_session, old_session)
        self.assertEqual(old_session.mode_id, new_session.mode_id)
        self.assertEqual([], new_session.state.action_log)
        # The old session's log is untouched — restart never reverses or replays it.
        self.assertEqual(1, len(old_session.state.action_log))

    def test_restart_key_triggers_restart_during_play(self):
        screen = self._screen()
        event = type("Event", (), {"type": p.KEYDOWN, "key": p.K_r, "mod": 0, "unicode": "r"})()

        screen.handle_event(event)

        self.assertIsInstance(screen.next_screen, EngineGameScreen)
        self.assertEqual(screen.session.mode_id, screen.next_screen.session.mode_id)

    def test_back_to_menu_key_sets_next_screen_to_menu_screen(self):
        screen = self._screen()
        event = type("Event", (), {"type": p.KEYDOWN, "key": p.K_BACKSPACE, "mod": 0, "unicode": ""})()

        screen.handle_event(event)

        self.assertIsInstance(screen.next_screen, MenuScreen)

    def test_go_to_menu_sets_next_screen_to_menu_screen(self):
        screen = self._screen()

        screen._go_to_menu()

        self.assertIsInstance(screen.next_screen, MenuScreen)


if __name__ == "__main__":
    unittest.main()
