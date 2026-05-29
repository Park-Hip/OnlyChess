"""Tests for panel-rendering helper functions."""

import unittest

from src.constants import BLACK, WHITE
from src.game.board import GameState
from src.ui.render_panels import get_ap_text, get_material_text


class RenderPanelHelperTests(unittest.TestCase):
    """Verify score and countdown formatting for the player panels."""

    def test_game_state_turns_to_next_event_uses_turn_counter_modulo(self):
        game_state = GameState()

        game_state.event_manager.turn_counter = 0
        self.assertEqual(game_state.get_turns_to_next_event(), 10)

        game_state.event_manager.turn_counter = 9
        self.assertEqual(game_state.get_turns_to_next_event(), 1)

        game_state.event_manager.turn_counter = 10
        self.assertEqual(game_state.get_turns_to_next_event(), 10)

    def test_get_material_text_formats_for_each_panel(self):
        self.assertEqual(get_material_text(-3, is_top_panel=True), "+3")
        self.assertEqual(get_material_text(2, is_top_panel=False), "+2")
        self.assertEqual(get_material_text(0, is_top_panel=True), "")
        self.assertEqual(get_material_text(-1, is_top_panel=False), "")

    def test_get_ap_text_formats_player_ap(self):
        game_state = GameState()
        game_state.action_points.gain_for_move(WHITE)
        game_state.action_points.gain_for_move(WHITE)

        self.assertEqual(get_ap_text(game_state, WHITE), "AP: 1")
        self.assertEqual(get_ap_text(game_state, BLACK), "AP: 0")

if __name__ == "__main__":
    unittest.main()
