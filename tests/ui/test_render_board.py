"""Tests for board-rendering helper functions."""

import unittest

from src.game.board import GameState
from src.game.move import Move
from src.ui.render_board import get_board_colors, get_highlight_targets, get_last_move_squares


class RenderBoardHelperTests(unittest.TestCase):
    """Verify board-render helpers prepare the right state for drawing."""

    def test_get_board_colors_returns_two_colors(self):
        colors = get_board_colors()
        self.assertEqual(len(colors), 2)

    def test_get_last_move_squares_returns_empty_list_without_moves(self):
        self.assertEqual(get_last_move_squares(GameState()), [])

    def test_get_last_move_squares_returns_start_and_end(self):
        game_state = GameState()
        move = Move((6, 4), (4, 4), game_state.board.grid)
        game_state.move_log.append(move)

        self.assertEqual(get_last_move_squares(game_state), [(6, 4), (4, 4)])

    def test_get_last_move_squares_ignores_ability_turn_records(self):
        game_state = GameState()
        game_state.move_log.append({"ability_turn": "w"})

        self.assertEqual(get_last_move_squares(game_state), [])

    def test_get_highlight_targets_filters_moves_by_origin(self):
        game_state = GameState()
        valid_moves = game_state.get_valid_moves()

        targets = get_highlight_targets(valid_moves, (6, 4))

        self.assertEqual(set(targets), {(5, 4), (4, 4)})


if __name__ == "__main__":
    unittest.main()
