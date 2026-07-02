"""Tests for the Tai Xiu event."""

import unittest
from unittest.mock import patch

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, PAWN_CODE, WHITE
from src.events import TaiXiu
from src.game.board import GameState
from src.pieces import King, Pawn


class TaiXiuEventTests(unittest.TestCase):
    """Verify Tai Xiu removes one random non-king piece from the rolled side."""

    def test_trigger_warning_marks_event_as_active(self):
        event = TaiXiu(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_tai_outcome_removes_one_black_non_king_piece(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        black_pawn = Pawn(BLACK, (2, 2))
        game_state.board.set_piece_at(2, 2, black_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = TaiXiu(game_state)

        with patch("src.events.tai_xiu.random.choice", side_effect=["tai", (2, 2)]):
            event.execute()

        self.assertIsNone(game_state.board.get_piece_at(2, 2))
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_xiu_outcome_removes_one_white_non_king_piece(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_pawn = Pawn(WHITE, (5, 5))
        game_state.board.set_piece_at(5, 5, white_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = TaiXiu(game_state)

        with patch("src.events.tai_xiu.random.choice", side_effect=["xiu", (5, 5)]):
            event.execute()

        self.assertIsNone(game_state.board.get_piece_at(5, 5))
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_event_is_no_op_when_target_side_only_has_king(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = TaiXiu(game_state)

        with patch("src.events.tai_xiu.random.choice", return_value="tai"):
            event.execute()

        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)
        self.assertNotEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), PAWN_CODE)

    def test_shielded_piece_is_not_eligible_for_removal(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        shielded_pawn = Pawn(BLACK, (2, 2))
        shielded_pawn.is_shielded = True
        vulnerable_pawn = Pawn(BLACK, (3, 3))
        game_state.board.set_piece_at(2, 2, shielded_pawn)
        game_state.board.set_piece_at(3, 3, vulnerable_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = TaiXiu(game_state)

        with patch("src.events.tai_xiu.random.choice", side_effect=["tai", (3, 3)]):
            event.execute()

        self.assertIs(game_state.board.get_piece_at(2, 2), shielded_pawn)
        self.assertIsNone(game_state.board.get_piece_at(3, 3))


if __name__ == "__main__":
    unittest.main()
