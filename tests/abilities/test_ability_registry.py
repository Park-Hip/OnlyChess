"""Tests for ability registry and shared turn rules."""

import unittest

from src.abilities import get_abilities_for_piece, get_ability, get_registered_ability_keys
from src.constants import BOARD_COLS, BOARD_ROWS, WHITE
from src.game.board import GameState
from src.pieces import King, Knight
from src.pieces.dynamic_fused import DynamicFusedPiece
from src.constants import BISHOP_CODE, KNIGHT_CODE


class AbilityRegistryTests(unittest.TestCase):
    """Verify ability registration and common validation."""

    def test_registered_ability_keys_include_all_standard_abilities(self):
        self.assertIn("knight_swap", get_registered_ability_keys())
        self.assertIn("bishop_snipe", get_registered_ability_keys())
        self.assertIn("rook_shield", get_registered_ability_keys())
        self.assertIn("pawn_sprint", get_registered_ability_keys())

    def test_get_ability_returns_stable_ability_instances(self):
        self.assertEqual(get_ability("knight_swap").ap_cost, 2)
        self.assertEqual(get_ability("bishop_snipe").ap_cost, 3)
        self.assertEqual(get_ability("rook_shield").ap_cost, 3)
        self.assertEqual(get_ability("pawn_sprint").ap_cost, 1)

    def test_fused_piece_gets_component_abilities(self):
        fused = DynamicFusedPiece(WHITE, KNIGHT_CODE, [KNIGHT_CODE, BISHOP_CODE], (4, 4))
        ability_keys = [ability.ability_key for ability in get_abilities_for_piece(fused)]

        self.assertIn("knight_swap", ability_keys)
        self.assertIn("bishop_snipe", ability_keys)

    def test_insufficient_ap_blocks_ability_without_side_effects(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        knight = Knight(WHITE, (4, 4))
        game_state.board.set_piece_at(4, 4, knight)
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))

        used = get_ability("knight_swap").use(game_state, knight, (4, 4))

        self.assertFalse(used)
        self.assertEqual(game_state.action_points.get_ap(WHITE), 0)


if __name__ == "__main__":
    unittest.main()
