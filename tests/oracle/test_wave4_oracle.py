"""Wave 4 closes the standard-chess oracle gate for the new engine."""

import unittest

from .new_adapter import NewEngine
from .perft import POSITIONS, perft


class WaveFourOracleTests(unittest.TestCase):
    def test_published_perft_positions_match_through_depth_two(self):
        engine = NewEngine()
        for name, (fen, expected) in POSITIONS.items():
            with self.subTest(position=name):
                self.assertEqual(perft(engine, fen, 1), expected[1])
                self.assertEqual(perft(engine, fen, 2), expected[2])


if __name__ == "__main__":
    unittest.main()
