"""Tests for promotion menu helpers."""

import unittest

from src.constants import BISHOP_CODE, KNIGHT_CODE, QUEEN_CODE, ROOK_CODE
from src.game.board import GameState
from src.main import handle_promotion_click
from src.ui.input_handler import InputState
from src.ui.promotion_menu import PROMOTION_CHOICES, get_promotion_menu_rect, resolve_promotion_click


class PromotionMenuTests(unittest.TestCase):
    """Verify promotion menu geometry and click mapping."""

    def test_promotion_choices_match_standard_promotion_options(self):
        self.assertEqual(PROMOTION_CHOICES, [QUEEN_CODE, ROOK_CODE, BISHOP_CODE, KNIGHT_CODE])

    def test_get_promotion_menu_rect_centers_menu(self):
        rect = get_promotion_menu_rect(board_width=512, board_height=512, info_panel_height=60, square_size=64)

        self.assertEqual((rect.x, rect.y, rect.width, rect.height), (128, 284, 256, 64))

    def test_resolve_promotion_click_returns_piece_code_inside_menu(self):
        rect = get_promotion_menu_rect(board_width=512, board_height=512, info_panel_height=60, square_size=64)

        self.assertEqual(resolve_promotion_click((rect.x + 10, rect.y + 10), rect, square_size=64), QUEEN_CODE)
        self.assertEqual(resolve_promotion_click((rect.x + 74, rect.y + 10), rect, square_size=64), ROOK_CODE)
        self.assertEqual(resolve_promotion_click((rect.x + 138, rect.y + 10), rect, square_size=64), BISHOP_CODE)
        self.assertEqual(resolve_promotion_click((rect.x + 202, rect.y + 10), rect, square_size=64), KNIGHT_CODE)

    def test_resolve_promotion_click_returns_none_outside_menu(self):
        rect = get_promotion_menu_rect()
        self.assertIsNone(resolve_promotion_click((rect.x - 5, rect.y), rect))

    def test_handle_promotion_click_keeps_pending_move_on_outside_click(self):
        game_state = GameState()
        input_state = InputState(promotion_move_pending=object())

        result = handle_promotion_click(input_state, game_state, (0, 0))

        self.assertFalse(result)
        self.assertIsNotNone(input_state.promotion_move_pending)


if __name__ == "__main__":
    unittest.main()
