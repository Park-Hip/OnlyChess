"""Tests for Pawn Sprint ability."""

import unittest

from src.abilities import use_ability
from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, QUEEN_CODE, WHITE
from src.game.board import GameState
from src.pieces import King, Pawn


class PawnSprintTests(unittest.TestCase):
    """Verify Pawn Sprint moves pawns forward up to three squares."""

    def _state(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        return game_state

    def test_pawn_sprint_moves_three_clear_squares(self):
        game_state = self._state()
        pawn = Pawn(WHITE, (6, 3))
        game_state.board.set_piece_at(6, 3, pawn)
        game_state.action_points.ap_by_color[WHITE] = 1

        used = use_ability("pawn_sprint", game_state, (6, 3), (3, 3))

        self.assertTrue(used)
        self.assertIsNone(game_state.board.get_piece_at(6, 3))
        self.assertIs(game_state.board.get_piece_at(3, 3), pawn)
        self.assertTrue(pawn.has_moved)
        self.assertEqual(game_state.action_points.get_ap(WHITE), 0)

    def test_pawn_sprint_rejects_blocked_path(self):
        game_state = self._state()
        pawn = Pawn(WHITE, (6, 3))
        blocker = Pawn(WHITE, (5, 3))
        game_state.board.set_piece_at(6, 3, pawn)
        game_state.board.set_piece_at(5, 3, blocker)
        game_state.action_points.ap_by_color[WHITE] = 1

        used = use_ability("pawn_sprint", game_state, (6, 3), (3, 3))

        self.assertFalse(used)
        self.assertEqual(game_state.action_points.get_ap(WHITE), 1)

    def test_pawn_sprint_promotes_on_final_rank(self):
        game_state = self._state()
        pawn = Pawn(WHITE, (3, 2))
        game_state.board.set_piece_at(3, 2, pawn)
        game_state.action_points.ap_by_color[WHITE] = 1

        used = use_ability("pawn_sprint", game_state, (3, 2), (0, 2))

        self.assertTrue(used)
        self.assertEqual(game_state.board.get_piece_at(0, 2).get_piece_code(), QUEEN_CODE)


if __name__ == "__main__":
    unittest.main()
