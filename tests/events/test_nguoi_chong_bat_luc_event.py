"""Tests for the Nguoi Chong Bat Luc event."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, WHITE
from src.events import NguoiChongBatLuc
from src.game.board import GameState
from src.pieces import King, Knight, Rook


class NguoiChongBatLucEventTests(unittest.TestCase):
    """Verify Nguoi Chong Bat Luc temporarily immobilizes both kings."""

    def test_trigger_warning_marks_event_as_active(self):
        event = NguoiChongBatLuc(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_immobilizes_both_kings_but_not_other_pieces(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_king = King(WHITE, (7, 4))
        black_king = King(BLACK, (0, 4))
        white_knight = Knight(WHITE, (4, 4))
        game_state.board.set_piece_at(7, 4, white_king)
        game_state.board.set_piece_at(0, 4, black_king)
        game_state.board.set_piece_at(4, 4, white_knight)
        event = NguoiChongBatLuc(game_state)

        event.execute()

        self.assertFalse(white_king.is_active)
        self.assertFalse(black_king.is_active)
        self.assertTrue(white_knight.is_active)
        self.assertEqual(white_king.immobilized_turns, 1)
        self.assertEqual(black_king.immobilized_turns, 1)

    def test_immobilized_king_has_no_moves_or_castling(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_king = King(WHITE, (7, 4))
        black_king = King(BLACK, (0, 4))
        white_rook = Rook(WHITE, (7, 7))
        game_state.board.set_piece_at(7, 4, white_king)
        game_state.board.set_piece_at(0, 4, black_king)
        game_state.board.set_piece_at(7, 7, white_rook)
        event = NguoiChongBatLuc(game_state)

        event.execute()
        moves = white_king.get_possible_moves(game_state)

        self.assertEqual(moves, [])
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)

    def test_tick_restores_kings_after_one_turn(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_king = King(WHITE, (7, 4))
        black_king = King(BLACK, (0, 4))
        game_state.board.set_piece_at(7, 4, white_king)
        game_state.board.set_piece_at(0, 4, black_king)
        event = NguoiChongBatLuc(game_state)

        event.execute()
        event.tick()

        self.assertTrue(white_king.is_active)
        self.assertTrue(black_king.is_active)
        self.assertEqual(white_king.immobilized_turns, 0)
        self.assertEqual(black_king.immobilized_turns, 0)
        self.assertEqual(event.duration, 0)


if __name__ == "__main__":
    unittest.main()
