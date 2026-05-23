"""Smoke tests for board creation against the piece package surface."""

import unittest

from src.constants import BISHOP_CODE, KING_CODE, KNIGHT_CODE, PAWN_CODE, QUEEN_CODE, ROOK_CODE
from src.game.board import Board, GameState
from src.game.move import Move
from src.pieces import Bishop, King, Knight, Queen, Rook


class BoardPieceCreationTests(unittest.TestCase):
    """Verify board creation still produces the right piece classes."""

    def test_board_create_piece_returns_expected_standard_classes(self):
        board = Board()

        self.assertIsInstance(board.create_piece("w", ROOK_CODE, (7, 0)), Rook)
        self.assertIsInstance(board.create_piece("w", KNIGHT_CODE, (7, 1)), Knight)
        self.assertIsInstance(board.create_piece("w", BISHOP_CODE, (7, 2)), Bishop)
        self.assertIsInstance(board.create_piece("w", QUEEN_CODE, (7, 3)), Queen)
        self.assertIsInstance(board.create_piece("w", KING_CODE, (7, 4)), King)

    def test_promotion_uses_registry_for_piece_creation(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(8)] for _ in range(8)]
        pawn = game_state.board.create_piece("w", PAWN_CODE, (1, 0))
        game_state.board.grid[1][0] = pawn
        promotion_move = Move((1, 0), (0, 0), game_state.board.grid)

        game_state.make_move(promotion_move, promotion_choice=ROOK_CODE)

        self.assertIsInstance(game_state.board.grid[0][0], Rook)
        self.assertEqual(game_state.board.grid[0][0].pos, (0, 0))


if __name__ == "__main__":
    unittest.main()
