"""Tests for the simple event registry."""

import unittest

from src.events import create_event, get_registered_event_keys
from src.events.gia_xang_tang import GiaXangTang
from src.events.registry import get_event_class
from src.game.board import GameState


class EventRegistryTests(unittest.TestCase):
    """Verify event lookup and construction are registry-driven."""

    def test_registered_event_keys_include_gia_xang_tang(self):
        self.assertIn("gia_xang_tang", get_registered_event_keys())

    def test_get_event_class_returns_registered_class(self):
        self.assertIs(get_event_class("gia_xang_tang"), GiaXangTang)

    def test_create_event_builds_event_from_key(self):
        event = create_event("gia_xang_tang", GameState())

        self.assertIsInstance(event, GiaXangTang)
        self.assertEqual(event.event_key, "gia_xang_tang")


if __name__ == "__main__":
    unittest.main()
