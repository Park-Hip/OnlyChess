"""Regression tests for explicit captured-piece summaries on real moves."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KNIGHT_CODE, PAWN_CODE, ROOK_CODE, WHITE
from src.game.board import Board, GameState
from src.game.capture_tracker import CapturedPieceRecord
from src.game.move import Move
from src.pieces import Pawn, Rook


class CaptureTrackerTests(unittest.TestCase):
    """Verify capture tracking now uses move history instead of board inference."""

    def test_real_capture_updates_white_captured_summary(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.grid[4][4] = Rook(WHITE, (4, 4))
        game_state.board.grid[4][6] = Rook(BLACK, (4, 6))
        move = Move((4, 4), (4, 6), game_state.board.grid)

        game_state.make_move(move, is_real_move=True)

        self.assertEqual(game_state.get_captured_pieces(), ([BLACK + ROOK_CODE], []))
        self.assertEqual(game_state.capture_tracker.white_captured, [CapturedPieceRecord(BLACK, ROOK_CODE)])

    def test_en_passant_capture_is_tracked_for_real_moves(self):
        game_state = GameState()
        game_state.board = Board()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_pawn = Pawn(WHITE, (3, 4))
        black_pawn = Pawn(BLACK, (1, 5))
        game_state.board.grid[3][4] = white_pawn
        game_state.board.grid[1][5] = black_pawn
        game_state.white_to_move = False

        black_double_step = Move((1, 5), (3, 5), game_state.board.grid)
        game_state.make_move(black_double_step, is_real_move=True)

        en_passant = Move((3, 4), (2, 5), game_state.board.grid, is_enpassant_move=True)
        game_state.make_move(en_passant, is_real_move=True)

        self.assertEqual(game_state.get_captured_pieces(), ([BLACK + PAWN_CODE], []))

    def test_promotion_capture_still_tracks_the_captured_piece(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.grid[1][1] = Pawn(WHITE, (1, 1))
        game_state.board.grid[0][0] = Rook(BLACK, (0, 0))
        move = Move((1, 1), (0, 0), game_state.board.grid)

        game_state.make_move(move, promotion_choice=KNIGHT_CODE, is_real_move=True)

        self.assertEqual(game_state.get_captured_pieces(), ([BLACK + ROOK_CODE], []))
        self.assertEqual(game_state.board.grid[0][0].name, KNIGHT_CODE)


if __name__ == "__main__":
    unittest.main()
