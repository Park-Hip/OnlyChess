"""Tests for fused chess pieces."""

import unittest

from src.constants import ARCHBISHOP_CODE, BLACK, BOARD_COLS, BOARD_ROWS, CHANCELLOR_CODE, WHITE
from src.game.board import GameState
from src.pieces import Archbishop, Chancellor, King, create_piece, get_registered_piece_codes


class FusedPieceTests(unittest.TestCase):
    """Verify fused pieces stay compatible with standard piece behavior."""

    def _empty_state(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        return game_state

    def test_archbishop_combines_bishop_and_knight_moves(self):
        game_state = self._empty_state()
        archbishop = Archbishop(WHITE, (4, 4))
        game_state.board.set_piece_at(4, 4, archbishop)

        targets = {(move.end_row, move.end_col) for move in archbishop.get_possible_moves(game_state)}

        self.assertIn((2, 3), targets)
        self.assertIn((3, 3), targets)

    def test_chancellor_combines_rook_and_knight_moves(self):
        game_state = self._empty_state()
        chancellor = Chancellor(WHITE, (4, 4))
        game_state.board.set_piece_at(4, 4, chancellor)

        targets = {(move.end_row, move.end_col) for move in chancellor.get_possible_moves(game_state)}

        self.assertIn((2, 3), targets)
        self.assertIn((4, 7), targets)

    def test_fused_pieces_are_registered_and_have_metadata(self):
        archbishop = create_piece(ARCHBISHOP_CODE, WHITE, (4, 4))
        chancellor = create_piece(CHANCELLOR_CODE, BLACK, (3, 3))

        self.assertIn(ARCHBISHOP_CODE, get_registered_piece_codes())
        self.assertIn(CHANCELLOR_CODE, get_registered_piece_codes())
        self.assertFalse(archbishop.can_fuse())
        self.assertFalse(chancellor.can_fuse())
        self.assertEqual(archbishop.get_fusion_tags(), ["N", "B"])
        self.assertEqual(chancellor.get_fusion_tags(), ["R", "N"])

    def test_fused_pieces_use_their_own_sprite_keys(self):
        archbishop = Archbishop(WHITE, (4, 4))
        chancellor = Chancellor(BLACK, (3, 3))

        self.assertEqual(archbishop.get_sprite_key(), "wA")
        self.assertEqual(chancellor.get_sprite_key(), "bC")


if __name__ == "__main__":
    unittest.main()
