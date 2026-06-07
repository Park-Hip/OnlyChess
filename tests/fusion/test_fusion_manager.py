"""Tests for capture-based fusion resolution."""

import unittest

from src.constants import ARCHBISHOP_CODE, BLACK, BOARD_COLS, BOARD_ROWS, CHANCELLOR_CODE, KNIGHT_CODE, ROOK_CODE, WHITE
from src.game.board import GameState
from src.game.move import Move
from src.pieces import Archbishop, Bishop, King, Knight, Rook


class FusionManagerTests(unittest.TestCase):
    """Verify fusion is triggered only by eligible real captures."""

    def _empty_state(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        game_state.white_king_pos = (7, 4)
        game_state.black_king_pos = (0, 4)
        game_state.move_log = [object()] * 8
        return game_state

    def test_knight_capturing_bishop_creates_archbishop(self):
        game_state = self._empty_state()
        knight = Knight(WHITE, (4, 4))
        bishop = Bishop(BLACK, (2, 3))
        game_state.board.set_piece_at(4, 4, knight)
        game_state.board.set_piece_at(2, 3, bishop)

        move = Move((4, 4), (2, 3), game_state.board.grid)
        game_state.make_move(move, is_real_move=True)

        fused_piece = game_state.board.get_piece_at(2, 3)
        self.assertEqual(fused_piece.get_piece_code(), ARCHBISHOP_CODE)
        self.assertEqual(fused_piece.fusion_components, [KNIGHT_CODE, "B"])
        self.assertTrue(fused_piece.has_moved)
        self.assertIs(move.fused_to_piece, fused_piece)

    def test_rook_capturing_knight_creates_chancellor(self):
        game_state = self._empty_state()
        rook = Rook(WHITE, (4, 4))
        knight = Knight(BLACK, (4, 6))
        game_state.board.set_piece_at(4, 4, rook)
        game_state.board.set_piece_at(4, 6, knight)

        game_state.make_move(Move((4, 4), (4, 6), game_state.board.grid), is_real_move=True)

        self.assertEqual(game_state.board.get_piece_at(4, 6).get_piece_code(), CHANCELLOR_CODE)

    def test_fusion_does_not_trigger_before_turn_five(self):
        game_state = self._empty_state()
        game_state.move_log = []
        knight = Knight(WHITE, (4, 4))
        bishop = Bishop(BLACK, (2, 3))
        game_state.board.set_piece_at(4, 4, knight)
        game_state.board.set_piece_at(2, 3, bishop)

        move = Move((4, 4), (2, 3), game_state.board.grid)
        game_state.make_move(move, is_real_move=True)

        self.assertIsNone(move.fused_to_piece)
        self.assertEqual(game_state.board.get_piece_at(2, 3).get_piece_code(), KNIGHT_CODE)

    def test_simulated_capture_does_not_trigger_fusion(self):
        game_state = self._empty_state()
        knight = Knight(WHITE, (4, 4))
        bishop = Bishop(BLACK, (2, 3))
        game_state.board.set_piece_at(4, 4, knight)
        game_state.board.set_piece_at(2, 3, bishop)

        move = Move((4, 4), (2, 3), game_state.board.grid)
        game_state.make_move(move)

        self.assertIsNone(move.fused_to_piece)

    def test_fused_piece_cannot_chain_fusion(self):
        game_state = self._empty_state()
        archbishop = Archbishop(WHITE, (4, 4))
        bishop = Bishop(BLACK, (2, 2))
        game_state.board.set_piece_at(4, 4, archbishop)
        game_state.board.set_piece_at(2, 2, bishop)

        move = Move((4, 4), (2, 2), game_state.board.grid)
        game_state.make_move(move, is_real_move=True)

        self.assertIsNone(move.fused_to_piece)

    def test_base_piece_uses_fused_target_primary_component_for_matching(self):
        game_state = self._empty_state()
        rook = Rook(WHITE, (4, 4))
        archbishop = Archbishop(BLACK, (4, 6))
        game_state.board.set_piece_at(4, 4, rook)
        game_state.board.set_piece_at(4, 6, archbishop)

        game_state.make_move(Move((4, 4), (4, 6), game_state.board.grid), is_real_move=True)

        self.assertEqual(game_state.board.get_piece_at(4, 6).get_piece_code(), CHANCELLOR_CODE)


if __name__ == "__main__":
    unittest.main()
