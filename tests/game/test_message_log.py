"""Tests for the bounded gameplay message log."""

import unittest

from src.game.message_log import GameMessageLog


class GameMessageLogTests(unittest.TestCase):
    """Verify player-facing message log behavior."""

    def test_add_ignores_empty_messages(self):
        log = GameMessageLog()

        log.add("")

        self.assertEqual(log.get_recent_messages(), [])

    def test_recent_messages_are_newest_first(self):
        log = GameMessageLog()

        log.add("First")
        log.add("Second")

        self.assertEqual(log.get_recent_messages(), ["Second", "First"])

    def test_log_keeps_only_max_messages(self):
        log = GameMessageLog(max_messages=2)

        log.add("One")
        log.add("Two")
        log.add("Three")

        self.assertEqual(log.get_recent_messages(), ["Three", "Two"])


if __name__ == "__main__":
    unittest.main()
