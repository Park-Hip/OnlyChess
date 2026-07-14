"""Tests for the Long Toi Tan Nat Khi Nhan Ra Toi La Gay event."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, QUEEN_CODE, WHITE
from src.events import LongToiTanNatKhiNhanRaToiLaGay
from src.game.board import GameState
from src.pieces import King, Queen


class LongToiTanNatKhiNhanRaToiLaGayEventTests(unittest.TestCase):
    """Verify this event removes all queens and keeps non-queens unchanged."""

    def test_trigger_warning_marks_event_as_active(self):
        event = LongToiTanNatKhiNhanRaToiLaGay(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_removes_all_queens(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 3, Queen(WHITE, (7, 3)))
        game_state.board.set_piece_at(0, 3, Queen(BLACK, (0, 3)))
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = LongToiTanNatKhiNhanRaToiLaGay(game_state)

        event.execute()

        self.assertIsNone(game_state.board.get_piece_at(7, 3))
        self.assertIsNone(game_state.board.get_piece_at(0, 3))
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_execute_is_no_op_when_no_queens_exist(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = LongToiTanNatKhiNhanRaToiLaGay(game_state)

        event.execute()

        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)
        self.assertNotEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), QUEEN_CODE)
        self.assertNotEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), QUEEN_CODE)


if __name__ == "__main__":
    unittest.main()
