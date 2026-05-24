"""Integration tests for event-manager warning and execution flow."""

import unittest

from src.constants import KNIGHT_CODE, ROOK_CODE
from src.events import EventManager
from src.game.board import GameState
from src.game.move import Move


class EventManagerFlowTests(unittest.TestCase):
    """Verify warning, execution, and next-event queueing still work."""

    def test_turn_nine_triggers_warning_for_queued_event(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.event_manager = manager
        game_state.move_log = [object()] * 18

        manager.update()

        self.assertEqual(manager.turn_counter, 9)
        self.assertIsNotNone(manager.queued_event)
        self.assertTrue(manager.queued_event.warning_active)
        self.assertIn(manager.queued_event, manager.active_events)

    def test_turn_ten_executes_event_and_queues_next_one(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.event_manager = manager
        manager.update()
        game_state.move_log = [object()] * 18
        manager.update()
        game_state.move_log = [object()] * 20

        self.assertEqual(game_state.board.grid[7][0].get_piece_code(), ROOK_CODE)
        manager.update()

        self.assertEqual(manager.turn_counter, 10)
        self.assertEqual(game_state.board.grid[7][0].get_piece_code(), KNIGHT_CODE)
        self.assertEqual(len(manager.active_events), 0)
        self.assertEqual(manager.queued_event_key, "gia_xang_tang")
        self.assertEqual(len(manager.snapshots), 1)

    def test_real_black_move_pipeline_can_still_reach_event_manager(self):
        game_state = GameState()
        game_state.event_manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.move_log = [object()] * 19
        game_state.event_manager.update()
        game_state.white_to_move = False
        move = Move((1, 0), (2, 0), game_state.board.grid)

        game_state.make_move(move, is_real_move=True)

        self.assertEqual(game_state.event_manager.turn_counter, 10)


if __name__ == "__main__":
    unittest.main()
