"""Tests for the ShieldTracker helper."""

import unittest

from src.constants import BLACK, WHITE
from src.game.shield_tracker import ShieldTracker
from src.pieces import Pawn, Rook


class ShieldTrackerTests(unittest.TestCase):
    """Verify shield bookkeeping is owned by ShieldTracker."""

    def test_add_shield_marks_piece_and_tracks_once(self):
        tracker = ShieldTracker()
        rook = Rook(WHITE, (4, 4))

        tracker.add(rook, WHITE)
        tracker.add(rook, WHITE)

        self.assertTrue(rook.is_shielded)
        self.assertEqual(rook.shield_owner, WHITE)
        self.assertEqual(len(tracker.active_pieces), 1)

    def test_expire_after_turn_clears_only_opponent_owned_shields(self):
        tracker = ShieldTracker()
        white_piece = Rook(WHITE, (4, 4))
        black_piece = Pawn(BLACK, (3, 3))
        tracker.add(white_piece, WHITE)
        tracker.add(black_piece, BLACK)

        tracker.expire_after_turn(BLACK)

        self.assertFalse(white_piece.is_shielded)
        self.assertEqual(white_piece.shield_turns, 0)
        self.assertTrue(black_piece.is_shielded)
        self.assertEqual(black_piece.shield_owner, BLACK)


if __name__ == "__main__":
    unittest.main()
