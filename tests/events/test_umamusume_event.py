"""Tests for the Umamusume event."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, KNIGHT_CODE, QUEEN_CODE, WHITE
from src.events import Umamusume
from src.game.board import GameState
from src.pieces import King, Queen


class UmamusumeEventTests(unittest.TestCase):
    """Verify Umamusume transforms all non-king pieces into knights."""

    def test_trigger_warning_marks_event_as_active(self):
        event = Umamusume(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_transforms_all_non_king_pieces_to_knights(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_queen = Queen(WHITE, (4, 4))
        black_queen = Queen(BLACK, (2, 2))
        black_queen.has_moved = True
        white_king = King(WHITE, (7, 4))
        black_king = King(BLACK, (0, 4))
        game_state.board.set_piece_at(4, 4, white_queen)
        game_state.board.set_piece_at(2, 2, black_queen)
        game_state.board.set_piece_at(7, 4, white_king)
        game_state.board.set_piece_at(0, 4, black_king)
        event = Umamusume(game_state)

        event.execute()

        self.assertEqual(game_state.board.get_piece_at(4, 4).get_piece_code(), KNIGHT_CODE)
        self.assertEqual(game_state.board.get_piece_at(2, 2).get_piece_code(), KNIGHT_CODE)
        self.assertTrue(game_state.board.get_piece_at(2, 2).has_moved)
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_event_changes_standard_starting_board_piece_mix(self):
        game_state = GameState()
        event = Umamusume(game_state)

        event.execute()

        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(7, 3).get_piece_code(), KNIGHT_CODE)
        self.assertNotEqual(game_state.board.get_piece_at(7, 3).get_piece_code(), QUEEN_CODE)

if __name__ == "__main__":
    unittest.main()
