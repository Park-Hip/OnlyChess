"""Regression tests for the post-move systems pipeline."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, ROOK_CODE, WHITE
from src.game.board import GameState
from src.game.move import Move
from src.pieces import Rook


class DummyEventManager:
    """Small spy object for counting event update calls."""

    def __init__(self):
        self.update_calls = 0

    def update(self):
        """Record that the event update hook ran."""
        self.update_calls += 1


class GameRulesPipelineTests(unittest.TestCase):
    """Verify real moves trigger side systems while simulated ones do not."""

    def test_white_real_move_updates_tracker_but_not_end_of_turn_event(self):
        game_state = GameState()
        game_state.event_manager = DummyEventManager()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.grid[4][4] = Rook(WHITE, (4, 4))
        game_state.board.grid[4][6] = Rook(BLACK, (4, 6))
        move = Move((4, 4), (4, 6), game_state.board.grid)

        game_state.make_move(move, is_real_move=True)

        self.assertEqual(game_state.get_captured_pieces(), ([BLACK + ROOK_CODE], []))
        self.assertEqual(game_state.event_manager.update_calls, 0)

    def test_black_real_move_triggers_end_of_turn_event_update(self):
        game_state = GameState()
        game_state.event_manager = DummyEventManager()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.grid[4][4] = Rook(BLACK, (4, 4))
        game_state.board.grid[4][6] = Rook(WHITE, (4, 6))
        game_state.white_to_move = False
        move = Move((4, 4), (4, 6), game_state.board.grid)

        game_state.make_move(move, is_real_move=True)

        self.assertEqual(game_state.get_captured_pieces(), ([], [WHITE + ROOK_CODE]))
        self.assertEqual(game_state.event_manager.update_calls, 1)

    def test_simulated_move_generation_does_not_trigger_real_side_systems(self):
        game_state = GameState()
        game_state.event_manager = DummyEventManager()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.grid[7][4] = game_state.board.create_piece(WHITE, KING_CODE, (7, 4))
        game_state.board.grid[0][4] = game_state.board.create_piece(BLACK, KING_CODE, (0, 4))
        game_state.board.grid[4][4] = Rook(WHITE, (4, 4))
        game_state.board.grid[4][6] = Rook(BLACK, (4, 6))
        game_state.white_king_pos = (7, 4)
        game_state.black_king_pos = (0, 4)

        _ = game_state.get_valid_moves()

        self.assertEqual(game_state.get_captured_pieces(), ([], []))
        self.assertEqual(game_state.event_manager.update_calls, 0)


if __name__ == "__main__":
    unittest.main()
