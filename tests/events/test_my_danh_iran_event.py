"""Tests for the My Danh Iran event."""

import unittest
from unittest.mock import patch

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, PAWN_CODE, QUEEN_CODE, ROOK_CODE, WHITE
from src.events import MyDanhIran
from src.game.board import GameState
from src.pieces import King, Pawn, Queen, Rook


class MyDanhIranEventTests(unittest.TestCase):
    """Verify My Danh Iran removes pieces inside a random 2x2 danger zone."""

    def test_trigger_warning_marks_event_as_active(self):
        game_state = GameState()
        with patch("src.events.my_danh_iran.random.randint", side_effect=[2, 3]):
            event = MyDanhIran(game_state)

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_removes_pieces_inside_warning_zone(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        black_pawn = Pawn(BLACK, (2, 3))
        white_queen = Queen(WHITE, (2, 4))
        black_rook = Rook(BLACK, (3, 3))
        white_king = King(WHITE, (7, 4))
        black_king = King(BLACK, (0, 4))
        game_state.board.set_piece_at(2, 3, black_pawn)
        game_state.board.set_piece_at(2, 4, white_queen)
        game_state.board.set_piece_at(3, 3, black_rook)
        game_state.board.set_piece_at(7, 4, white_king)
        game_state.board.set_piece_at(0, 4, black_king)

        with patch("src.events.my_danh_iran.random.randint", side_effect=[2, 3]):
            event = MyDanhIran(game_state)

        event.trigger_warning()
        event.execute()

        self.assertIsNone(game_state.board.get_piece_at(2, 3))
        self.assertIsNone(game_state.board.get_piece_at(2, 4))
        self.assertIsNone(game_state.board.get_piece_at(3, 3))
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_warning_area_is_fixed_during_event_lifetime(self):
        game_state = GameState()
        with patch("src.events.my_danh_iran.random.randint", side_effect=[4, 1]):
            event = MyDanhIran(game_state)

        self.assertEqual(event.warning_area, (4, 1))


if __name__ == "__main__":
    unittest.main()
