"""Tests for the Kho Ga Tron Ba Mia event."""

import unittest
from unittest.mock import patch

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, BISHOP_CODE, KNIGHT_CODE, ROOK_CODE, WHITE
from src.events import KhoGaTronBaMia
from src.game.board import GameState
from src.pieces import Bishop, King, Knight, Pawn, Queen, Rook


class KhoGaTronBaMiaEventTests(unittest.TestCase):
    """Verify Kho Ga Tron Ba Mia poisons eligible pieces temporarily."""

    def test_trigger_warning_marks_event_as_active(self):
        event = KhoGaTronBaMia(GameState())

        event.trigger_warning()

        self.assertTrue(event.warning_active)

    def test_execute_poisons_one_eligible_piece_per_side(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_rook = Rook(WHITE, (4, 4))
        white_queen = Queen(WHITE, (5, 5))
        black_bishop = Bishop(BLACK, (2, 2))
        game_state.board.set_piece_at(4, 4, white_rook)
        game_state.board.set_piece_at(5, 5, white_queen)
        game_state.board.set_piece_at(2, 2, black_bishop)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = KhoGaTronBaMia(game_state)

        with patch(
            "src.events.kho_ga_tron_ba_mia.random.choice",
            side_effect=[white_rook, black_bishop],
        ):
            event.execute()

        self.assertEqual(white_rook.poisoned_turns, 3)
        self.assertEqual(black_bishop.poisoned_turns, 3)
        self.assertFalse(hasattr(white_queen, "poisoned_turns"))

    def test_poison_restricts_rook_bishop_and_knight_movement(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_rook = Rook(WHITE, (4, 4))
        white_bishop = Bishop(WHITE, (4, 2))
        black_knight = Knight(BLACK, (2, 2))
        game_state.board.set_piece_at(4, 4, white_rook)
        game_state.board.set_piece_at(4, 2, white_bishop)
        game_state.board.set_piece_at(2, 2, black_knight)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))

        white_rook.poisoned_turns = 3
        white_bishop.poisoned_turns = 3
        black_knight.poisoned_turns = 3

        rook_targets = {(move.end_row, move.end_col) for move in white_rook.get_possible_moves(game_state)}
        bishop_targets = {(move.end_row, move.end_col) for move in white_bishop.get_possible_moves(game_state)}
        knight_moves = black_knight.get_possible_moves(game_state)

        self.assertEqual(white_rook.get_piece_code(), ROOK_CODE)
        self.assertEqual(white_bishop.get_piece_code(), BISHOP_CODE)
        self.assertEqual(black_knight.get_piece_code(), KNIGHT_CODE)
        self.assertEqual(rook_targets, {(3, 4), (5, 4), (4, 3), (4, 5)})
        self.assertEqual(bishop_targets, {(3, 1), (3, 3), (5, 1), (5, 3)})
        self.assertEqual(knight_moves, [])

    def test_tick_restores_poisoned_pieces_after_three_turns(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_rook = Rook(WHITE, (4, 4))
        black_bishop = Bishop(BLACK, (2, 2))
        game_state.board.set_piece_at(4, 4, white_rook)
        game_state.board.set_piece_at(2, 2, black_bishop)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = KhoGaTronBaMia(game_state)

        with patch(
            "src.events.kho_ga_tron_ba_mia.random.choice",
            side_effect=[white_rook, black_bishop],
        ):
            event.execute()

        event.tick()
        event.tick()
        event.tick()

        self.assertEqual(white_rook.poisoned_turns, 0)
        self.assertEqual(black_bishop.poisoned_turns, 0)
        self.assertEqual(event.duration, 0)
        self.assertGreater(len(white_rook.get_possible_moves(game_state)), 4)

    def test_execute_skips_sides_without_eligible_pieces(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_pawn = Pawn(WHITE, (6, 4))
        black_rook = Rook(BLACK, (2, 2))
        game_state.board.set_piece_at(6, 4, white_pawn)
        game_state.board.set_piece_at(2, 2, black_rook)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        event = KhoGaTronBaMia(game_state)

        with patch("src.events.kho_ga_tron_ba_mia.random.choice", return_value=black_rook):
            event.execute()

        self.assertFalse(hasattr(white_pawn, "poisoned_turns"))
        self.assertEqual(black_rook.poisoned_turns, 3)

if __name__ == "__main__":
    unittest.main()
