"""Tests for promotion menu helpers."""

import unittest

from src.constants import BISHOP_CODE, KNIGHT_CODE, QUEEN_CODE, ROOK_CODE
from src.game.board import GameState
from src.main import handle_promotion_click
from src.ui.input_handler import InputState
from src.ui.promotion_menu import PROMOTION_CHOICES, get_promotion_menu_rect, resolve_promotion_click


class _StubMove:
    """Minimal pending-move stand-in exposing the target square."""

    def __init__(self, end_row, end_col):
        self.end_row = end_row
        self.end_col = end_col
        self.promotion_choice = None


class PromotionMenuTests(unittest.TestCase):
    """Verify promotion menu geometry and click mapping."""

    def test_promotion_choices_match_standard_promotion_options(self):
        self.assertEqual(PROMOTION_CHOICES, [QUEEN_CODE, ROOK_CODE, BISHOP_CODE, KNIGHT_CODE])

    def test_get_promotion_menu_rect_defaults_to_centered_vertical_menu(self):
        # With no move the menu is centered and stacked vertically (one column, four rows).
        rect = get_promotion_menu_rect(board_width=512, board_height=512, info_panel_height=60, square_size=64)

        self.assertEqual((rect.x, rect.y, rect.width, rect.height), (224, 188, 64, 256))

    def test_get_promotion_menu_rect_anchors_to_target_column(self):
        # A promotion on the top rows draws downwards from the target square's column.
        rect = get_promotion_menu_rect(move=_StubMove(end_row=0, end_col=3), square_size=64)

        self.assertEqual((rect.x, rect.y, rect.width, rect.height), (192, 60, 64, 256))

    def test_resolve_promotion_click_returns_piece_code_inside_menu(self):
        rect = get_promotion_menu_rect(board_width=512, board_height=512, info_panel_height=60, square_size=64)

        # Choices are stacked vertically, so each row maps to one option.
        self.assertEqual(resolve_promotion_click((rect.x + 10, rect.y + 10), menu_rect=rect, square_size=64), QUEEN_CODE)
        self.assertEqual(resolve_promotion_click((rect.x + 10, rect.y + 74), menu_rect=rect, square_size=64), ROOK_CODE)
        self.assertEqual(resolve_promotion_click((rect.x + 10, rect.y + 138), menu_rect=rect, square_size=64), BISHOP_CODE)
        self.assertEqual(resolve_promotion_click((rect.x + 10, rect.y + 202), menu_rect=rect, square_size=64), KNIGHT_CODE)

    def test_resolve_promotion_click_returns_none_outside_menu(self):
        rect = get_promotion_menu_rect()
        self.assertIsNone(resolve_promotion_click((rect.x - 5, rect.y), menu_rect=rect))

    def test_handle_promotion_click_keeps_pending_move_on_outside_click(self):
        game_state = GameState()
        input_state = InputState(promotion_move_pending=_StubMove(end_row=0, end_col=0))

        # (0, 0) sits above the menu, which starts below the top info panel.
        result = handle_promotion_click(input_state, game_state, (0, 0))

        self.assertFalse(result)
        self.assertIsNotNone(input_state.promotion_move_pending)


if __name__ == "__main__":
    unittest.main()
