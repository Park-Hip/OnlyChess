"""Tests for Bishop Snipe ability."""

import unittest

from src.abilities import use_ability
from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, WHITE
from src.game.board import GameState
from src.pieces import Bishop, King, Pawn


class BishopSnipeTests(unittest.TestCase):
    """Verify Bishop Snipe captures without moving or triggering fusion."""

    def _state(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        return game_state

    def test_bishop_snipe_captures_diagonal_enemy(self):
        game_state = self._state()
        bishop = Bishop(WHITE, (4, 4))
        target = Pawn(BLACK, (2, 2))
        game_state.board.set_piece_at(4, 4, bishop)
        game_state.board.set_piece_at(2, 2, target)
        game_state.action_points.ap_by_color[WHITE] = 3

        used = use_ability("bishop_snipe", game_state, (4, 4), (2, 2))

        self.assertTrue(used)
        self.assertIs(game_state.board.get_piece_at(4, 4), bishop)
        self.assertIsNone(game_state.board.get_piece_at(2, 2))
        self.assertEqual(game_state.get_captured_pieces()[0], ["bp"])
        self.assertEqual(game_state.action_points.get_ap(WHITE), 0)

    def test_bishop_snipe_rejects_blocked_or_shielded_targets(self):
        game_state = self._state()
        bishop = Bishop(WHITE, (4, 4))
        blocker = Pawn(WHITE, (3, 3))
        target = Pawn(BLACK, (2, 2))
        target.is_shielded = True
        game_state.board.set_piece_at(4, 4, bishop)
        game_state.board.set_piece_at(3, 3, blocker)
        game_state.board.set_piece_at(2, 2, target)
        game_state.action_points.ap_by_color[WHITE] = 3

        used = use_ability("bishop_snipe", game_state, (4, 4), (2, 2))

        self.assertFalse(used)
        self.assertEqual(game_state.action_points.get_ap(WHITE), 3)


if __name__ == "__main__":
    unittest.main()
