"""Tests for help overlay text helpers."""

import unittest

from src.ui.help_overlay import get_help_lines


class HelpOverlayTests(unittest.TestCase):
    """Verify help text includes the important advanced-mode rules."""

    def test_help_lines_include_controls_fusion_abilities_and_events(self):
        help_text = "\n".join(get_help_lines())

        self.assertIn("Right-click", help_text)
        self.assertIn("Knight captures Bishop", help_text)
        self.assertIn("Pawn Sprint", help_text)
        self.assertIn("displayed turn 10", help_text)


if __name__ == "__main__":
    unittest.main()
