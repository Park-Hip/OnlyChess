"""Tests for the shared event base contract."""

import unittest

from src.events import ChessEvent
from src.game.board import GameState


class DummyEvent(ChessEvent):
    """Minimal concrete event used for base-contract tests."""

    event_key = "dummy_event"


class EventBaseContractTests(unittest.TestCase):
    """Verify the base event shape stays predictable."""

    def test_default_event_state_is_initialized_consistently(self):
        event = DummyEvent(GameState())

        self.assertEqual(event.name, "Base Event")
        self.assertEqual(event.duration, 0)
        self.assertFalse(event.warning_active)

    def test_trigger_warning_and_execute_toggle_warning_state(self):
        event = DummyEvent(GameState())

        event.trigger_warning()
        self.assertTrue(event.warning_active)

        event.execute()
        self.assertFalse(event.warning_active)

    def test_tick_is_a_safe_no_op_by_default(self):
        event = DummyEvent(GameState())

        event.tick()

        self.assertFalse(event.warning_active)


if __name__ == "__main__":
    unittest.main()
