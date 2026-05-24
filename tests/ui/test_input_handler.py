"""Tests for UI input-state helpers."""

import unittest

from src.constants import BOARD_COLS, BOARD_ROWS, INFO_PANEL_HEIGHT, SQ_SIZE
from src.game.board import GameState
from src.ui.input_handler import (
    InputState,
    clamp_drag_square,
    get_board_square,
    handle_board_mouse_down,
    handle_board_mouse_up,
    is_board_click,
    move_attempt_ready,
    reset_selection_state,
    resolve_invalid_click_selection,
    retain_origin_after_invalid_drag,
    set_promotion_pending,
)


class InputHandlerTests(unittest.TestCase):
    """Verify UI-only selection state transitions stay predictable."""

    def test_board_click_detection_uses_panel_bounds(self):
        self.assertFalse(is_board_click((10, INFO_PANEL_HEIGHT - 1)))
        self.assertTrue(is_board_click((10, INFO_PANEL_HEIGHT + 1)))

    def test_board_click_rejects_x_positions_outside_board_width(self):
        self.assertFalse(is_board_click((-1, INFO_PANEL_HEIGHT + 10)))
        self.assertFalse(is_board_click((BOARD_COLS * SQ_SIZE, INFO_PANEL_HEIGHT + 10)))

    def test_board_square_conversion_uses_info_panel_offset(self):
        self.assertEqual(get_board_square((2 * SQ_SIZE + 1, INFO_PANEL_HEIGHT + 3 * SQ_SIZE + 1)), (3, 2))

    def test_mouse_down_selects_friendly_piece(self):
        game_state = GameState()
        input_state = InputState()

        handle_board_mouse_down(input_state, game_state, (1, INFO_PANEL_HEIGHT + 6 * SQ_SIZE + 1))

        self.assertEqual(input_state.sq_selected, (6, 0))
        self.assertEqual(input_state.player_clicks, [(6, 0)])
        self.assertTrue(input_state.dragging)

    def test_drag_release_packages_move_attempt(self):
        game_state = GameState()
        input_state = InputState(sq_selected=(6, 0), player_clicks=[(6, 0)], dragging=True)

        handle_board_mouse_up(input_state, (1, INFO_PANEL_HEIGHT + 5 * SQ_SIZE + 1))

        self.assertTrue(move_attempt_ready(input_state))
        self.assertEqual(input_state.player_clicks, [(6, 0), (5, 0)])
        self.assertEqual(input_state.move_attempt_type, "drag")

    def test_invalid_drag_can_retain_origin_square(self):
        input_state = InputState(sq_selected=(6, 0), player_clicks=[(6, 0), (5, 0)])

        retain_origin_after_invalid_drag(input_state)

        self.assertEqual(input_state.sq_selected, (6, 0))
        self.assertEqual(input_state.player_clicks, [(6, 0)])

    def test_invalid_click_can_reselect_friendly_piece(self):
        game_state = GameState()
        input_state = InputState(player_clicks=[(6, 0), (6, 1)], sq_selected=(6, 1))

        resolve_invalid_click_selection(input_state, game_state)

        self.assertEqual(input_state.player_clicks, [(6, 1)])
        self.assertEqual(input_state.sq_selected, (6, 1))

    def test_promotion_pending_blocks_drag_release_updates(self):
        input_state = InputState(sq_selected=(6, 0), player_clicks=[(6, 0)], dragging=True)
        set_promotion_pending(input_state, object())

        handle_board_mouse_up(input_state, (1, INFO_PANEL_HEIGHT + 5 * SQ_SIZE + 1))

        self.assertEqual(input_state.player_clicks, [(6, 0)])

    def test_reset_selection_state_clears_transient_fields(self):
        input_state = InputState(
            sq_selected=(3, 3),
            player_clicks=[(3, 3), (4, 3)],
            dragging=True,
            move_attempt_type="drag",
            click_type="second_click",
        )

        reset_selection_state(input_state)

        self.assertEqual(input_state.sq_selected, ())
        self.assertEqual(input_state.player_clicks, [])
        self.assertFalse(input_state.dragging)
        self.assertEqual(input_state.move_attempt_type, "click")
        self.assertEqual(input_state.click_type, "first_click")

    def test_clamp_drag_square_stays_within_board(self):
        self.assertEqual(clamp_drag_square((-10, INFO_PANEL_HEIGHT - 50)), (0, 0))
        self.assertEqual(clamp_drag_square((999, INFO_PANEL_HEIGHT + 999)), (BOARD_ROWS - 1, BOARD_COLS - 1))


if __name__ == "__main__":
    unittest.main()
