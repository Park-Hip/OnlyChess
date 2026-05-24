"""Tests for the extracted Gia Xang Tang event."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KNIGHT_CODE, ROOK_CODE, WHITE
from src.events import GiaXangTang
from src.game.board import GameState
from src.pieces import Rook


class GiaXangTangEventTests(unittest.TestCase):
    """Verify the rook-to-knight event keeps piece state coherent."""

    def test_trigger_warning_marks_event_as_active(self):
        event = GiaXangTang(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_transforms_rooks_into_knights(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_rook = Rook(WHITE, (4, 4))
        black_rook = Rook(BLACK, (2, 2))
        black_rook.has_moved = True
        game_state.board.grid[4][4] = white_rook
        game_state.board.grid[2][2] = black_rook
        event = GiaXangTang(game_state)

        event.execute()

        self.assertEqual(game_state.board.grid[4][4].get_piece_code(), KNIGHT_CODE)
        self.assertEqual(game_state.board.grid[2][2].get_piece_code(), KNIGHT_CODE)
        self.assertFalse(game_state.board.grid[4][4].has_moved)
        self.assertTrue(game_state.board.grid[2][2].has_moved)
        self.assertEqual(game_state.board.grid[2][2].pos, (2, 2))

    def test_non_rook_pieces_are_unchanged(self):
        game_state = GameState()
        event = GiaXangTang(game_state)

        original_piece_code = game_state.board.grid[7][1].get_piece_code()
        event.execute()

        self.assertEqual(game_state.board.grid[7][1].get_piece_code(), original_piece_code)
        self.assertEqual(game_state.board.grid[7][0].get_piece_code(), KNIGHT_CODE)
        self.assertNotEqual(game_state.board.grid[7][0].get_piece_code(), ROOK_CODE)

    def test_gia_xang_tang_prevents_future_castling_from_transformed_corner(self):
        game_state = GameState()
        for col in (5, 6):
            game_state.board.set_piece_at(7, col, None)

        event = GiaXangTang(game_state)
        event.execute()

        king = game_state.board.get_piece_at(7, 4)
        self.assertEqual(king.get_castle_moves(game_state), [])


if __name__ == "__main__":
    unittest.main()
