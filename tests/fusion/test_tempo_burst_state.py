"""Tests for the TempoBurstState helper."""

import unittest

from src.constants import WHITE
from src.fusion.tempo_burst_state import TempoBurstState
from src.pieces import Rook


class TempoBurstStateTests(unittest.TestCase):
    """Verify Tempo Burst runtime state transitions."""

    def test_start_sets_pending_piece_and_owner(self):
        rook = Rook(WHITE, (4, 4))
        state = TempoBurstState()

        state.start(rook)

        self.assertTrue(state.pending)
        self.assertIs(state.piece, rook)
        self.assertEqual(state.owner, WHITE)

    def test_clear_resets_all_fields(self):
        rook = Rook(WHITE, (4, 4))
        state = TempoBurstState()
        state.start(rook)

        state.clear()

        self.assertFalse(state.pending)
        self.assertIsNone(state.piece)
        self.assertIsNone(state.owner)


if __name__ == "__main__":
    unittest.main()
