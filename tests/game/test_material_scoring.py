"""Regression tests for material scoring helpers."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, WHITE
from src.game.board import GameState
from src.game.move import Move
from src.game.scoring import calculate_material_advantage
from src.pieces import Knight, Queen, Rook


class MaterialScoringTests(unittest.TestCase):
    """Verify material summaries now delegate to a focused helper."""

    def test_starting_position_is_materially_balanced(self):
        game_state = GameState()

        self.assertEqual(game_state.get_material_advantage(), 0)

    def test_helper_uses_piece_metadata_for_custom_grid_scores(self):
        grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        grid[4][4] = Queen(WHITE, (4, 4))
        grid[3][3] = Knight(BLACK, (3, 3))

        self.assertEqual(calculate_material_advantage(grid), 6)

    def test_board_summary_uses_helper_after_a_real_capture(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        white_rook = Rook(WHITE, (4, 4))
        black_knight = Knight(BLACK, (4, 6))
        game_state.board.grid[4][4] = white_rook
        game_state.board.grid[4][6] = black_knight

        move = Move((4, 4), (4, 6), game_state.board.grid)
        game_state.make_move(move, is_real_move=True)

        # Rook (5) captures Knight (3), triggering dynamic fusion.
        # DynamicFusedPiece inherits base piece material value (Rook = 5).
        self.assertEqual(game_state.get_material_advantage(), 5)


if __name__ == "__main__":
    unittest.main()
