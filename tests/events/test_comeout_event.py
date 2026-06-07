"""Tests for the Comeout event."""

import unittest
from unittest.mock import patch

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, PAWN_CODE, QUEEN_CODE, WHITE
from src.events import Comeout
from src.game.board import GameState
from src.pieces import King, Pawn


class ComeoutEventTests(unittest.TestCase):
    """Verify Comeout promotes exactly one random pawn to a queen."""

    def test_trigger_warning_marks_event_as_active(self):
        event = Comeout(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_transforms_selected_pawn_to_queen(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_pawn = Pawn(WHITE, (4, 4))
        black_pawn = Pawn(BLACK, (2, 2))
        black_pawn.has_moved = True
        game_state.board.set_piece_at(4, 4, white_pawn)
        game_state.board.set_piece_at(2, 2, black_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = Comeout(game_state)

        with patch("src.events.comeout.random.choice", return_value=(2, 2, black_pawn)):
            event.execute()

        self.assertEqual(game_state.board.get_piece_at(2, 2).get_piece_code(), QUEEN_CODE)
        self.assertEqual(game_state.board.get_piece_at(2, 2).color, BLACK)
        self.assertTrue(game_state.board.get_piece_at(2, 2).has_moved)
        self.assertEqual(game_state.board.get_piece_at(4, 4).get_piece_code(), PAWN_CODE)
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_execute_is_no_op_when_no_pawns_exist(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = Comeout(game_state)

        event.execute()

        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)
        self.assertNotEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), PAWN_CODE)
        self.assertNotEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), PAWN_CODE)


if __name__ == "__main__":
    unittest.main()
