"""Tests for Tempo Burst fusion behavior."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, WHITE
from src.game.board import GameState
from src.game.move import Move
from src.pieces import Bishop, King, Rook
from src.ui.render_panels import get_tempo_burst_text


class TempoBurstTests(unittest.TestCase):
    """Verify Rook+Bishop fusion grants one extra rook move."""

    def _empty_state(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        game_state.move_log = [object()] * 8
        return game_state

    def test_rook_capturing_bishop_starts_tempo_burst_without_replacing_rook(self):
        game_state = self._empty_state()
        rook = Rook(WHITE, (4, 4))
        bishop = Bishop(BLACK, (4, 6))
        game_state.board.set_piece_at(4, 4, rook)
        game_state.board.set_piece_at(4, 6, bishop)

        game_state.make_move(Move((4, 4), (4, 6), game_state.board.grid), is_real_move=True)

        self.assertIs(game_state.board.get_piece_at(4, 6), rook)
        self.assertTrue(rook.has_fused)
        self.assertTrue(game_state.tempo_burst_pending)
        self.assertIs(game_state.tempo_burst_piece, rook)
        self.assertEqual(game_state.tempo_burst_owner, WHITE)
        self.assertEqual(get_tempo_burst_text(game_state), "Tempo Burst: extra rook move")

    def test_only_tempo_burst_rook_can_move_during_extra_move(self):
        game_state = self._empty_state()
        rook = Rook(WHITE, (4, 4))
        other_rook = Rook(WHITE, (6, 6))
        game_state.board.set_piece_at(4, 4, rook)
        game_state.board.set_piece_at(6, 6, other_rook)
        game_state.tempo_burst_pending = True
        game_state.tempo_burst_piece = rook
        game_state.tempo_burst_owner = WHITE

        moves = game_state.get_all_possible_moves()

        self.assertTrue(all(move.piece_moved is rook for move in moves))

    def test_tempo_burst_clears_after_extra_move(self):
        game_state = self._empty_state()
        rook = Rook(WHITE, (4, 4))
        game_state.board.set_piece_at(4, 4, rook)
        game_state.tempo_burst_pending = True
        game_state.tempo_burst_piece = rook
        game_state.tempo_burst_owner = WHITE

        game_state.make_move(Move((4, 4), (4, 5), game_state.board.grid), is_real_move=True)

        self.assertFalse(game_state.tempo_burst_pending)
        self.assertIsNone(game_state.tempo_burst_piece)
        self.assertIsNone(game_state.tempo_burst_owner)
        self.assertEqual(get_tempo_burst_text(game_state), "")


if __name__ == "__main__":
    unittest.main()
