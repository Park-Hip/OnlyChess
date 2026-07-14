"""Tests for the Viec Nhe Vol Cao event."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, PAWN_CODE, WHITE
from src.events import ViecNheVolCao
from src.game.board import GameState
from src.pieces import King, Knight, Pawn


class ViecNheVolCaoEventTests(unittest.TestCase):
    """Verify Viec Nhe Vol Cao temporarily prevents pawn movement."""

    def test_trigger_warning_marks_event_as_active(self):
        event = ViecNheVolCao(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_stuns_all_pawns_but_not_other_pieces(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_pawn = Pawn(WHITE, (6, 4))
        black_pawn = Pawn(BLACK, (1, 3))
        white_knight = Knight(WHITE, (4, 4))
        game_state.board.set_piece_at(6, 4, white_pawn)
        game_state.board.set_piece_at(1, 3, black_pawn)
        game_state.board.set_piece_at(4, 4, white_knight)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = ViecNheVolCao(game_state)

        event.execute()

        self.assertFalse(white_pawn.is_active)
        self.assertFalse(black_pawn.is_active)
        self.assertTrue(white_knight.is_active)
        self.assertEqual(white_pawn.stunned_turns, 2)
        self.assertEqual(black_pawn.stunned_turns, 2)
        self.assertEqual(game_state.board.get_piece_at(7, 4).get_piece_code(), KING_CODE)
        self.assertEqual(game_state.board.get_piece_at(0, 4).get_piece_code(), KING_CODE)

    def test_stunned_pawns_have_no_moves_but_can_be_captured(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        stunned_pawn = Pawn(WHITE, (4, 4))
        black_knight = Knight(BLACK, (2, 3))
        game_state.board.set_piece_at(4, 4, stunned_pawn)
        game_state.board.set_piece_at(2, 3, black_knight)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = ViecNheVolCao(game_state)

        event.execute()
        knight_capture_squares = [
            (move.end_row, move.end_col) for move in black_knight.get_possible_moves(game_state)
        ]

        self.assertEqual(stunned_pawn.get_possible_moves(game_state), [])
        self.assertIn((4, 4), knight_capture_squares)

    def test_tick_restores_pawns_after_two_turns(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_pawn = Pawn(WHITE, (6, 4))
        game_state.board.set_piece_at(6, 4, white_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = ViecNheVolCao(game_state)

        event.execute()
        event.tick()

        self.assertFalse(white_pawn.is_active)
        self.assertEqual(white_pawn.stunned_turns, 1)

        event.tick()

        self.assertTrue(white_pawn.is_active)
        self.assertEqual(white_pawn.stunned_turns, 0)
        self.assertEqual(event.duration, 0)
        self.assertEqual(white_pawn.get_piece_code(), PAWN_CODE)

    def test_cleanup_does_not_restore_captured_pawns_to_the_board(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_pawn = Pawn(WHITE, (6, 4))
        game_state.board.set_piece_at(6, 4, white_pawn)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = ViecNheVolCao(game_state)

        event.execute()
        game_state.board.set_piece_at(6, 4, None)
        event.tick()
        event.tick()

        self.assertIsNone(game_state.board.get_piece_at(6, 4))


if __name__ == "__main__":
    unittest.main()
