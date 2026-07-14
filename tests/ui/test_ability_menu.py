"""Tests for ability menu helpers and input state."""

import unittest

from src.constants import BOARD_COLS, BOARD_ROWS, WHITE
from src.game.board import GameState
from src.pieces import King, Knight
from src.ui.ability_menu import get_ability_menu_rect, get_available_ability_keys, resolve_ability_menu_click
from src.ui.input_handler import InputState, ability_attempt_ready, clear_ability_state, handle_board_mouse_down, select_ability


class AbilityMenuTests(unittest.TestCase):
    """Verify ability menu helper behavior."""

    def test_available_ability_keys_respect_piece_and_ap(self):
        game_state = GameState()
        knight = Knight(WHITE, (4, 4))

        self.assertEqual(get_available_ability_keys(game_state, knight), [])

        game_state.action_points.ap_by_color[WHITE] = 2
        self.assertEqual(get_available_ability_keys(game_state, knight), ["knight_swap"])

    def test_resolve_ability_menu_click_returns_selected_key(self):
        rect = get_ability_menu_rect((4, 4))

        selected = resolve_ability_menu_click((rect.x + 5, rect.y + 5), ["knight_swap"], rect)

        self.assertEqual(selected, "knight_swap")
        self.assertIsNone(resolve_ability_menu_click((rect.x - 5, rect.y), ["knight_swap"], rect))

    def test_right_click_opens_ability_menu_for_friendly_piece(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(4, 4, Knight(WHITE, (4, 4)))
        input_state = InputState()

        handle_board_mouse_down(input_state, game_state, (4 * 64 + 1, 4 * 64 + 60 + 1), button=3)

        self.assertEqual(input_state.ability_menu_square, (4, 4))

    def test_select_and_clear_ability_target_state(self):
        input_state = InputState()

        select_ability(input_state, "knight_swap", (4, 4))
        input_state.player_clicks = [(5, 5)]

        self.assertTrue(ability_attempt_ready(input_state))

        clear_ability_state(input_state)

        self.assertIsNone(input_state.selected_ability_key)
        self.assertEqual(input_state.ability_source_square, ())


if __name__ == "__main__":
    unittest.main()
