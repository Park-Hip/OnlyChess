"""Tests for Action Point tracking and integration."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, MAX_AP, WHITE
from src.game.action_points import ActionPointTracker
from src.game.board import GameState
from src.game.move import Move
from src.pieces import King, Rook


class ActionPointTrackerTests(unittest.TestCase):
    """Verify AP gain and spending rules."""

    def test_tracker_starts_empty_for_both_players(self):
        tracker = ActionPointTracker()

        self.assertEqual(tracker.get_ap(WHITE), 0)
        self.assertEqual(tracker.get_ap(BLACK), 0)

    def test_tracker_awards_one_ap_every_two_moves(self):
        tracker = ActionPointTracker()

        tracker.gain_for_move(WHITE)
        self.assertEqual(tracker.get_ap(WHITE), 0)

        tracker.gain_for_move(WHITE)
        self.assertEqual(tracker.get_ap(WHITE), 1)

    def test_tracker_caps_ap(self):
        tracker = ActionPointTracker()

        for _ in range(MAX_AP * 2 + 4):
            tracker.gain_for_move(WHITE)

        self.assertEqual(tracker.get_ap(WHITE), MAX_AP)

    def test_spend_requires_enough_ap(self):
        tracker = ActionPointTracker()

        self.assertFalse(tracker.spend(WHITE, 1))
        tracker.ap_by_color[WHITE] = 2
        self.assertTrue(tracker.spend(WHITE, 1))
        self.assertEqual(tracker.get_ap(WHITE), 1)


class ActionPointIntegrationTests(unittest.TestCase):
    """Verify real move flow updates AP without affecting simulations."""

    def _minimal_state(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.set_piece_at(7, 4, King(WHITE, (7, 4)))
        game_state.board.set_piece_at(0, 4, King(BLACK, (0, 4)))
        game_state.white_king_pos = (7, 4)
        game_state.black_king_pos = (0, 4)
        return game_state

    def test_real_move_records_ap_progress(self):
        game_state = self._minimal_state()
        rook = Rook(WHITE, (4, 4))
        game_state.board.set_piece_at(4, 4, rook)
        move = Move((4, 4), (4, 5), game_state.board.grid)

        game_state.make_move(move, is_real_move=True)

        self.assertEqual(game_state.action_points.get_move_count(WHITE), 1)
        self.assertEqual(game_state.action_points.get_ap(WHITE), 0)
        self.assertEqual(game_state.action_points.get_move_count(BLACK), 0)

    def test_second_real_move_awards_ap(self):
        game_state = self._minimal_state()
        rook = Rook(WHITE, (4, 4))
        game_state.board.set_piece_at(4, 4, rook)

        game_state.make_move(Move((4, 4), (4, 5), game_state.board.grid), is_real_move=True)
        game_state.white_to_move = True
        game_state.make_move(Move((4, 5), (4, 6), game_state.board.grid), is_real_move=True)

        self.assertEqual(game_state.action_points.get_move_count(WHITE), 2)
        self.assertEqual(game_state.action_points.get_ap(WHITE), 1)

    def test_simulated_move_does_not_update_ap(self):
        game_state = self._minimal_state()
        rook = Rook(WHITE, (4, 4))
        game_state.board.set_piece_at(4, 4, rook)

        game_state.make_move(Move((4, 4), (4, 5), game_state.board.grid))

        self.assertEqual(game_state.action_points.get_move_count(WHITE), 0)
        self.assertEqual(game_state.action_points.get_ap(WHITE), 0)


if __name__ == "__main__":
    unittest.main()
