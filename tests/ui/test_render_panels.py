"""Tests for panel-rendering helper functions."""

import unittest

from src.ui.render_panels import calculate_turns_to_event, get_material_text


class RenderPanelHelperTests(unittest.TestCase):
    """Verify score and countdown formatting for the player panels."""

    def test_calculate_turns_to_event_uses_turn_counter_modulo(self):
        self.assertEqual(calculate_turns_to_event(0), 10)
        self.assertEqual(calculate_turns_to_event(9), 1)
        self.assertEqual(calculate_turns_to_event(10), 10)

    def test_get_material_text_formats_for_each_panel(self):
        self.assertEqual(get_material_text(-3, is_top_panel=True), "+3")
        self.assertEqual(get_material_text(2, is_top_panel=False), "+2")
        self.assertEqual(get_material_text(0, is_top_panel=True), "")
        self.assertEqual(get_material_text(-1, is_top_panel=False), "")


if __name__ == "__main__":
    unittest.main()
