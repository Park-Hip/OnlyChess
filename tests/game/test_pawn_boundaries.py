"""Regression tests for pawn movement near board edges."""

import unittest

from src.game.board import Board, GameState
from src.pieces.piece import Pawn


class PawnBoundaryTests(unittest.TestCase):
    """Ensure pawn move generation stays inside the board."""

    def test_white_pawn_on_top_row_has_no_generated_moves(self):
        game_state = GameState()
        game_state.board = Board()
        game_state.board.grid = [[None for _ in range(8)] for _ in range(8)]
        pawn = Pawn("w", (0, 0))
        game_state.board.grid[0][0] = pawn

        self.assertEqual(pawn.get_possible_moves(game_state), [])

    def test_black_pawn_on_bottom_row_has_no_generated_moves(self):
        game_state = GameState()
        game_state.board = Board()
        game_state.board.grid = [[None for _ in range(8)] for _ in range(8)]
        pawn = Pawn("b", (7, 7))
        game_state.board.grid[7][7] = pawn

        self.assertEqual(pawn.get_possible_moves(game_state), [])


if __name__ == "__main__":
    unittest.main()
