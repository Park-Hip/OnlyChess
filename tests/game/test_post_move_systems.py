"""Tests for the ordered post-move systems package."""

import unittest

from src.constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, WHITE
from src.game.board import GameState
from src.game.move import Move
from src.pieces import Rook


class RecordingSystem:
    """Minimal post-move system spy for ordering assertions."""

    def __init__(self, label, sink):
        self.label = label
        self.sink = sink

    def apply(self, game_state, move):
        """Record that this system ran."""
        self.sink.append(self.label)


class PostMoveSystemsTests(unittest.TestCase):
    """Verify ordered post-move systems wiring."""

    def _state(self):
        game_state = GameState()
        game_state.board.grid = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        game_state.board.grid[7][4] = game_state.board.create_piece(WHITE, KING_CODE, (7, 4))
        game_state.board.grid[0][4] = game_state.board.create_piece(BLACK, KING_CODE, (0, 4))
        game_state.white_king_pos = (7, 4)
        game_state.black_king_pos = (0, 4)
        return game_state

    def test_run_post_move_systems_uses_registered_order(self):
        from src.game.rules import run_post_move_systems

        game_state = self._state()
        game_state.board.grid[4][4] = Rook(WHITE, (4, 4))
        game_state.board.grid[4][6] = Rook(BLACK, (4, 6))
        move = Move((4, 4), (4, 6), game_state.board.grid)
        move.is_real_move = True

        calls = []
        game_state.post_move_systems = [
            RecordingSystem("capture", calls),
            RecordingSystem("fusion", calls),
            RecordingSystem("ap", calls),
            RecordingSystem("shields", calls),
            RecordingSystem("events", calls),
        ]

        run_post_move_systems(game_state, move)

        self.assertEqual(calls, ["capture", "fusion", "ap", "shields", "events"])

    def test_create_default_post_move_systems_returns_expected_system_types(self):
        from src.game.post_move_systems import create_default_post_move_systems

        game_state = self._state()
        systems = create_default_post_move_systems(game_state)

        self.assertEqual(
            [system.__class__.__name__ for system in systems],
            [
                "CaptureTrackingPostMoveSystem",
                "FusionPostMoveSystem",
                "ActionPointsPostMoveSystem",
                "ShieldExpiryPostMoveSystem",
                "EventUpdatePostMoveSystem",
            ],
        )


if __name__ == "__main__":
    unittest.main()
