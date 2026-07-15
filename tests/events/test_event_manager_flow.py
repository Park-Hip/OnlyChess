"""Integration tests for event-manager warning and execution flow."""

import unittest

from src.constants import KNIGHT_CODE, ROOK_CODE
from src.events.manager import DEFAULT_EVENT_POOL, EventManager
from src.game.board import GameState
from src.game.mode_config import DEFAULT_ADVANCED_EVENT_POOL
from src.game.move import Move


class EventManagerFlowTests(unittest.TestCase):
    """Verify warning, execution, and next-event queueing still work."""

    def test_empty_event_pool_remains_empty(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=[])

        self.assertEqual(manager.event_pool, [])
        self.assertIsNone(manager.queued_event)
        self.assertIsNone(manager.queued_event_key)

    def test_default_event_pool_contains_all_implemented_events(self):
        game_state = GameState()
        manager = EventManager(game_state)

        self.assertEqual(manager.event_pool, DEFAULT_EVENT_POOL)
        self.assertEqual(DEFAULT_EVENT_POOL, DEFAULT_ADVANCED_EVENT_POOL)
        self.assertEqual(len(manager.event_pool), 10)

    def test_turn_nine_triggers_warning_for_queued_event(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.event_manager = manager
        game_state.move_log = [object()] * 16

        manager.update()

        self.assertEqual(manager.turn_counter, 8)
        self.assertEqual(game_state.get_full_turn_count(), 8)
        self.assertEqual(game_state.get_turn_number(), 9)
        self.assertIsNotNone(manager.queued_event)
        self.assertTrue(manager.queued_event.warning_active)
        self.assertIn(manager.queued_event, manager.active_events)

    def test_turn_ten_executes_event_and_queues_next_one(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.event_manager = manager
        manager.update()
        game_state.move_log = [object()] * 16
        manager.update()
        game_state.move_log = [object()] * 18

        self.assertEqual(game_state.board.grid[7][0].get_piece_code(), ROOK_CODE)
        manager.update()

        self.assertEqual(manager.turn_counter, 9)
        self.assertEqual(game_state.get_full_turn_count(), 9)
        self.assertEqual(game_state.get_turn_number(), 10)
        self.assertEqual(game_state.board.grid[7][0].get_piece_code(), KNIGHT_CODE)
        self.assertEqual(len(manager.active_events), 0)
        self.assertEqual(manager.queued_event_key, "gia_xang_tang")
        self.assertIsNotNone(manager.queued_event)

    def test_timed_event_is_removed_after_duration_expires(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=["viec_nhe_vol_cao"])
        game_state.event_manager = manager
        game_state.move_log = [object()] * 16
        manager.update()
        game_state.move_log = [object()] * 18
        manager.update()

        self.assertEqual(len(manager.active_events), 1)

        game_state.move_log = [object()] * 20
        manager.update()
        self.assertEqual(len(manager.active_events), 1)

        game_state.move_log = [object()] * 22
        manager.update()

        self.assertEqual(len(manager.active_events), 0)

    def test_real_black_move_pipeline_can_still_reach_event_manager(self):
        game_state = GameState()
        game_state.event_manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.move_log = [object()] * 17
        game_state.event_manager.update()
        game_state.white_to_move = False
        move = Move((1, 0), (2, 0), game_state.board.grid)

        game_state.make_move(move, is_real_move=True)

        self.assertEqual(game_state.event_manager.turn_counter, 9)
        self.assertEqual(game_state.get_turn_number(), 10)


if __name__ == "__main__":
    unittest.main()
