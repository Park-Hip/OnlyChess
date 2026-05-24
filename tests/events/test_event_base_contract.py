"""Tests for the shared event base contract."""

import unittest

from src.events import ChessEvent, EventStateSnapshot
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

    def test_snapshot_helpers_return_default_payload(self):
        event = DummyEvent(GameState())

        self.assertEqual(event.build_snapshot_data(), {})
        event.restore_from_snapshot_data({"warning_active": True})
        self.assertTrue(event.warning_active)

    def test_snapshot_model_copies_event_manager_state(self):
        game_state = GameState()
        snapshot = EventStateSnapshot.from_game_state(
            game_state,
            resolved_event_key="dummy_event",
            queued_event_key="dummy_event",
            active_event_keys=["dummy_event"],
            event_snapshot_data={"warning_active": True},
        )

        self.assertEqual(snapshot.move_log_len, 0)
        self.assertEqual(snapshot.resolved_event_key, "dummy_event")
        self.assertEqual(snapshot.queued_event_key, "dummy_event")
        self.assertEqual(snapshot.active_event_keys, ["dummy_event"])
        self.assertTrue(snapshot.event_snapshot_data["warning_active"])


if __name__ == "__main__":
    unittest.main()
