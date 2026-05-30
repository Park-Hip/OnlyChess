"""Tests for Rook Shield ability."""

import unittest

from src.abilities import use_ability
from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, WHITE
from src.events import MyDanhIran
from src.game.board import GameState
from src.game.move import Move
from src.pieces import King, Pawn, Rook


class RookShieldTests(unittest.TestCase):
    """Verify Rook Shield protects pieces temporarily."""

    def _state(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        return game_state

    def test_rook_shield_protects_rook_and_adjacent_friendly_pieces(self):
        game_state = self._state()
        rook = Rook(WHITE, (4, 4))
        pawn = Pawn(WHITE, (4, 5))
        enemy = Pawn(BLACK, (5, 4))
        game_state.board.set_piece_at(4, 4, rook)
        game_state.board.set_piece_at(4, 5, pawn)
        game_state.board.set_piece_at(5, 4, enemy)
        game_state.action_points.ap_by_color[WHITE] = 3

        used = use_ability("rook_shield", game_state, (4, 4), (4, 4))

        self.assertTrue(used)
        self.assertTrue(rook.is_shielded)
        self.assertTrue(pawn.is_shielded)
        self.assertFalse(getattr(enemy, "is_shielded", False))
        self.assertEqual(game_state.action_points.get_ap(WHITE), 0)
        self.assertEqual(len(game_state.shield_tracker.active_pieces), 2)

    def test_shield_blocks_standard_capture_generation_and_event_damage(self):
        game_state = self._state()
        rook = Rook(WHITE, (2, 3))
        enemy_rook = Rook(BLACK, (2, 0))
        game_state.board.set_piece_at(2, 3, rook)
        game_state.board.set_piece_at(2, 0, enemy_rook)
        game_state.add_shielded_piece(rook, WHITE)

        targets = {(move.end_row, move.end_col) for move in enemy_rook.get_possible_moves(game_state)}
        event = MyDanhIran(game_state)
        event.warning_area = (2, 3)
        event.execute()

        self.assertNotIn((2, 3), targets)
        self.assertIs(game_state.board.get_piece_at(2, 3), rook)

    def test_shield_expires_after_opponent_completes_turn(self):
        game_state = self._state()
        rook = Rook(WHITE, (4, 4))
        black_rook = Rook(BLACK, (1, 1))
        game_state.board.set_piece_at(4, 4, rook)
        game_state.board.set_piece_at(1, 1, black_rook)
        game_state.add_shielded_piece(rook, WHITE)
        game_state.white_to_move = False

        game_state.make_move(Move((1, 1), (1, 2), game_state.board.grid), is_real_move=True)

        self.assertFalse(rook.is_shielded)
        self.assertEqual(rook.shield_turns, 0)


if __name__ == "__main__":
    unittest.main()
