"""Tests for Knight Swap ability."""

import unittest

from src.abilities import use_ability
from src.constants import BOARD_COLS, BOARD_ROWS, WHITE
from src.game.board import GameState
from src.pieces import King, Knight, Rook


class KnightSwapTests(unittest.TestCase):
    """Verify Knight Swap swaps friendly pieces and consumes AP."""

    def test_knight_swap_exchanges_two_friendly_pieces(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        knight = Knight(WHITE, (4, 4))
        king = King(WHITE, (7, 4))
        game_state.board.set_piece_at(4, 4, knight)
        game_state.board.set_piece_at(7, 4, king)
        game_state.white_king_pos = (7, 4)
        game_state.action_points.ap_by_color[WHITE] = 2

        used = use_ability("knight_swap", game_state, (4, 4), (7, 4))

        self.assertTrue(used)
        self.assertIs(game_state.board.get_piece_at(7, 4), knight)
        self.assertIs(game_state.board.get_piece_at(4, 4), king)
        self.assertEqual(game_state.white_king_pos, (4, 4))
        self.assertEqual(game_state.action_points.get_ap(WHITE), 0)

    def test_knight_swap_rejects_enemy_or_empty_target(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        knight = Knight(WHITE, (4, 4))
        enemy = Rook("b", (4, 5))
        game_state.board.set_piece_at(4, 4, knight)
        game_state.board.set_piece_at(4, 5, enemy)
        game_state.action_points.ap_by_color[WHITE] = 2

        used = use_ability("knight_swap", game_state, (4, 4), (4, 5))

        self.assertFalse(used)
        self.assertEqual(game_state.action_points.get_ap(WHITE), 2)


if __name__ == "__main__":
    unittest.main()
