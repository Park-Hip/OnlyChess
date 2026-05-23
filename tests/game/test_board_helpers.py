"""Smoke tests for the reorganized game package."""

import unittest

from src.constants import BOARD_COLS, BOARD_ROWS, STANDARD_PIECE_ORDER
from src.game.board import GameState
from src.game.state_helpers import is_inside_board, safe_get_piece


class GameInitializationTests(unittest.TestCase):
    """Verify core game-state imports and initialization still work."""

    def test_board_dimensions_match_shared_constants(self):
        game_state = GameState()

        self.assertEqual(len(game_state.board.grid), BOARD_ROWS)
        self.assertTrue(all(len(row) == BOARD_COLS for row in game_state.board.grid))

    def test_initial_valid_moves_count_is_20(self):
        game_state = GameState()

        self.assertEqual(len(game_state.get_valid_moves()), 20)

    def test_standard_piece_order_is_used_on_back_rank(self):
        game_state = GameState()
        back_rank = [piece.name for piece in game_state.board.grid[0]]

        self.assertEqual(back_rank, STANDARD_PIECE_ORDER)

    def test_state_helpers_handle_invalid_coordinates_safely(self):
        game_state = GameState()

        self.assertFalse(is_inside_board(-1, 0))
        self.assertFalse(is_inside_board(BOARD_ROWS, BOARD_COLS))
        self.assertIsNone(safe_get_piece(game_state.board.grid, -1, 0))


if __name__ == "__main__":
    unittest.main()
