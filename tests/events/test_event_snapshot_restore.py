"""Tests for event snapshot restoration during undo flow."""

import unittest

from src.constants import KNIGHT_CODE, ROOK_CODE
from src.events import EventManager
from src.game.board import GameState
from src.game.move import Move


class EventSnapshotRestoreTests(unittest.TestCase):
    """Verify event snapshots restore board and warning state generically."""

    def test_handle_undo_restores_board_before_event_resolution(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.event_manager = manager
        game_state.move_log = [object()] * 18
        manager.update()
        game_state.move_log = [object()] * 20
        manager.update()

        self.assertEqual(game_state.board.grid[7][0].get_piece_code(), KNIGHT_CODE)

        restored = manager.handle_undo()

        self.assertTrue(restored)
        self.assertEqual(game_state.board.grid[7][0].get_piece_code(), ROOK_CODE)
        self.assertIsNotNone(manager.restore_snapshot)

    def test_sync_state_rebuilds_warning_event_from_snapshot_key(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.event_manager = manager
        game_state.move_log = [object()] * 18
        manager.update()
        game_state.move_log = [object()] * 20
        manager.update()
        manager.handle_undo()
        game_state.move_log = [object()] * 18

        manager.sync_state()

        self.assertEqual(manager.turn_counter, 9)
        self.assertEqual(manager.queued_event_key, "gia_xang_tang")
        self.assertIsNotNone(manager.queued_event)
        self.assertTrue(manager.queued_event.warning_active)
        self.assertEqual(len(manager.active_events), 1)

    def test_main_undo_order_keeps_event_warning_ready_for_turn_nine(self):
        game_state = GameState()
        manager = EventManager(game_state, event_pool=["gia_xang_tang"])
        game_state.event_manager = manager
        game_state.move_log = [object()] * 19
        game_state.white_to_move = False
        move = Move((1, 0), (2, 0), game_state.board.grid)

        game_state.make_move(move, is_real_move=True)
        self.assertEqual(game_state.event_manager.turn_counter, 10)

        game_state.event_manager.handle_undo()
        game_state.undo_move()
        game_state.event_manager.sync_state()

        self.assertEqual(game_state.event_manager.turn_counter, 9)
        self.assertEqual(game_state.event_manager.queued_event_key, "gia_xang_tang")
        self.assertTrue(game_state.event_manager.active_events[0].warning_active)


if __name__ == "__main__":
    unittest.main()
