"""Tests for the Mat Quyen Cong Dan event."""

import unittest
from unittest.mock import patch

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, PAWN_CODE, WHITE
from src.events import MatQuyenCongDan
from src.game.board import GameState
from src.pieces import King, Pawn


class MatQuyenCongDanEventTests(unittest.TestCase):
    """Verify Mat Quyen Cong Dan removes one black pawn and converts one white pawn."""

    def test_trigger_warning_marks_event_as_active(self):
        event = MatQuyenCongDan(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_removes_black_pawn_and_converts_white_pawn(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        black_pawn = Pawn(BLACK, (2, 2))
        white_pawn = Pawn(WHITE, (5, 5))
        white_pawn.has_moved = True
        white_pawn.stunned_turns = 2
        game_state.board.set_piece_at(2, 2, black_pawn)
        game_state.board.set_piece_at(5, 5, white_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = MatQuyenCongDan(game_state)

        with patch(
            "src.events.mat_quyen_cong_dan.random.choice",
            side_effect=[(2, 2, black_pawn), (5, 5, white_pawn)],
        ):
            event.execute()

        converted_pawn = game_state.board.get_piece_at(5, 5)
        self.assertIsNone(game_state.board.get_piece_at(2, 2))
        self.assertEqual(converted_pawn.get_piece_code(), PAWN_CODE)
        self.assertEqual(converted_pawn.color, BLACK)
        self.assertTrue(converted_pawn.has_moved)
        self.assertEqual(converted_pawn.direction, 1)
        self.assertEqual(converted_pawn.stunned_turns, 2)
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_execute_skips_black_removal_when_no_black_pawns_exist(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_pawn = Pawn(WHITE, (5, 5))
        game_state.board.set_piece_at(5, 5, white_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = MatQuyenCongDan(game_state)

        with patch(
            "src.events.mat_quyen_cong_dan.random.choice",
            return_value=(5, 5, white_pawn),
        ):
            event.execute()

        converted_pawn = game_state.board.get_piece_at(5, 5)
        self.assertEqual(converted_pawn.get_piece_code(), PAWN_CODE)
        self.assertEqual(converted_pawn.color, BLACK)
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_execute_skips_white_transformation_when_no_white_pawns_exist(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        black_pawn = Pawn(BLACK, (2, 2))
        game_state.board.set_piece_at(2, 2, black_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = MatQuyenCongDan(game_state)

        with patch(
            "src.events.mat_quyen_cong_dan.random.choice",
            return_value=(2, 2, black_pawn),
        ):
            event.execute()

        self.assertIsNone(game_state.board.get_piece_at(2, 2))
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_execute_is_no_op_when_no_pawns_exist(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = MatQuyenCongDan(game_state)

        event.execute()

        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)
        self.assertNotEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), PAWN_CODE)
        self.assertNotEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), PAWN_CODE)


if __name__ == "__main__":
    unittest.main()
