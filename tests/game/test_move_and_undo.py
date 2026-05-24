"""Regression tests for move bookkeeping and internal rollback behavior."""

import unittest

from src.constants import BLACK, KNIGHT_CODE, WHITE
from src.game.board import Board, GameState
from src.game.move import Move
from src.pieces import Pawn, Rook


class MoveRollbackTests(unittest.TestCase):
    """Lock in move-state bookkeeping used by internal rollback."""

    def test_double_pawn_move_sets_en_passant_square(self):
        game_state = GameState()
        move = Move((6, 4), (4, 4), game_state.board.grid)

        game_state.make_move(move)

        self.assertEqual(game_state.enpassant_possible, (5, 4))

    def test_move_then_rollback_restores_turn_and_piece_position(self):
        game_state = GameState()
        move = Move((6, 4), (4, 4), game_state.board.grid)

        game_state.make_move(move)
        game_state._rollback_last_move()

        self.assertTrue(game_state.white_to_move)
        self.assertIsNotNone(game_state.board.grid[6][4])
        self.assertIsNone(game_state.board.grid[4][4])

    def test_move_records_previous_piece_state_for_rollback(self):
        game_state = GameState()
        pawn = game_state.board.grid[6][4]
        move = Move((6, 4), (4, 4), game_state.board.grid)

        game_state.make_move(move)

        self.assertEqual(move.moved_piece_prev_pos, (6, 4))
        self.assertFalse(move.moved_piece_prev_has_moved)
        self.assertTrue(pawn.has_moved)

    def test_capture_records_captured_piece_snapshot(self):
        game_state = GameState()
        game_state.board = Board()
        game_state.board.grid = [[None for _ in range(8)] for _ in range(8)]
        white_rook = Rook(WHITE, (4, 4))
        black_rook = Rook(BLACK, (4, 6))
        game_state.board.grid[4][4] = white_rook
        game_state.board.grid[4][6] = black_rook
        move = Move((4, 4), (4, 6), game_state.board.grid)

        game_state.make_move(move)

        self.assertEqual(move.captured_piece_prev_pos, (4, 6))
        self.assertFalse(move.captured_piece_prev_has_moved)

    def test_en_passant_rollback_restores_both_pawns(self):
        game_state = GameState()
        game_state.board = Board()
        game_state.board.grid = [[None for _ in range(8)] for _ in range(8)]
        white_pawn = Pawn(WHITE, (3, 4))
        black_pawn = Pawn(BLACK, (1, 5))
        game_state.board.grid[3][4] = white_pawn
        game_state.board.grid[1][5] = black_pawn
        game_state.white_to_move = False

        black_double_step = Move((1, 5), (3, 5), game_state.board.grid)
        game_state.make_move(black_double_step)

        en_passant = Move((3, 4), (2, 5), game_state.board.grid, is_enpassant_move=True)
        game_state.make_move(en_passant)
        game_state._rollback_last_move()

        self.assertIs(game_state.board.grid[3][4], white_pawn)
        self.assertIs(game_state.board.grid[3][5], black_pawn)
        self.assertIsNone(game_state.board.grid[2][5])

    def test_promotion_records_promoted_piece(self):
        game_state = GameState()
        game_state.board = Board()
        game_state.board.grid = [[None for _ in range(8)] for _ in range(8)]
        pawn = Pawn(WHITE, (1, 0))
        game_state.board.grid[1][0] = pawn
        move = Move((1, 0), (0, 0), game_state.board.grid)

        game_state.make_move(move, promotion_choice=KNIGHT_CODE)

        self.assertIsNotNone(move.promoted_to_piece)
        self.assertEqual(move.promoted_to_piece.name, KNIGHT_CODE)

    def test_rollback_restores_has_moved_flag(self):
        game_state = GameState()
        pawn = game_state.board.grid[6][4]
        move = Move((6, 4), (4, 4), game_state.board.grid)

        game_state.make_move(move)
        game_state._rollback_last_move()

        self.assertFalse(pawn.has_moved)


if __name__ == "__main__":
    unittest.main()
