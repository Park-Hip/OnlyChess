"""Wave 3's first honest old-engine/new-engine comparison.

The fixture deliberately covers only ordinary slide/leap chess.  Positions that
need castling, en passant, or promotion wait for the mod verbs that define them.
"""

import unittest

from .adapters import OldEngine
from .compare import compare
from .new_adapter import NewEngine
from .position import STARTING_FEN


CURATED_POSITIONS = (
    STARTING_FEN,
    "4k3/8/8/8/3p4/4P3/8/4K3 w - - 0 1",
    "4k3/8/8/3p4/4P3/8/8/4K3 b - - 0 1",
    "4k3/8/8/8/8/8/3N4/4K3 w - - 0 1",
)


class WaveThreeAdapterTests(unittest.TestCase):
    def test_new_engine_matches_the_legacy_engine_for_supported_positions(self):
        differences = compare(OldEngine(), NewEngine(), CURATED_POSITIONS)
        self.assertEqual(differences, [], "\n".join(str(item) for item in differences))


if __name__ == "__main__":
    unittest.main()
