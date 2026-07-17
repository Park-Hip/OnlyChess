import unittest

from src.constants import WHITE
from src.game.board import GameState
from src.pieces.fused import Inquisitor, Warden


class LimitedFusedPieceTests(unittest.TestCase):
    def setUp(self):
        self.game_state = GameState()
        # Clear board
        for r in range(8):
            for c in range(8):
                self.game_state.board.grid[r][c] = None

    def test_warden_moves_unlimited_orthogonal_but_max_3_diagonal(self):
        warden = Warden(WHITE, (4, 4))
        self.game_state.board.set_piece_at(4, 4, warden)

        moves = warden.get_possible_moves(self.game_state)
        destinations = [(m.end_row, m.end_col) for m in moves]

        # Orthogonal: full range (e.g., to row 0, 7, col 0, 7)
        self.assertIn((0, 4), destinations)
        self.assertIn((7, 4), destinations)
        self.assertIn((4, 0), destinations)
        self.assertIn((4, 7), destinations)

        # Diagonal: max 3 squares (e.g. from 4,4, 1,1 is distance 3, 0,0 is distance 4)
        self.assertIn((1, 1), destinations)  # 3 squares away
        self.assertNotIn((0, 0), destinations)  # 4 squares away

        self.assertIn((7, 7), destinations)  # 3 squares away
        self.assertNotIn((8, 8), destinations) # Off board anyway, but max is 3

    def test_inquisitor_moves_unlimited_diagonal_but_max_3_orthogonal(self):
        inquisitor = Inquisitor(WHITE, (4, 4))
        self.game_state.board.set_piece_at(4, 4, inquisitor)

        moves = inquisitor.get_possible_moves(self.game_state)
        destinations = [(m.end_row, m.end_col) for m in moves]

        # Diagonal: full range
        self.assertIn((0, 0), destinations)
        self.assertIn((1, 7), destinations)

        # Orthogonal: max 3 squares
        self.assertIn((1, 4), destinations)  # 3 squares away
        self.assertNotIn((0, 4), destinations)  # 4 squares away
        self.assertIn((7, 4), destinations)  # 3 squares away

        self.assertIn((4, 1), destinations)  # 3 squares away
        self.assertNotIn((4, 0), destinations)  # 4 squares away


if __name__ == "__main__":
    unittest.main()
