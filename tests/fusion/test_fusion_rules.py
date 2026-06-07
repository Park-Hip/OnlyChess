"""Tests for fusion rule lookup."""

import unittest

from src.constants import ARCHBISHOP_CODE, BISHOP_CODE, CHANCELLOR_CODE, KNIGHT_CODE, PAWN_CODE, ROOK_CODE, TEMPO_BURST_KEY
from src.fusion.rules import get_fusion_result


class FusionRuleTests(unittest.TestCase):
    """Verify valid and invalid fusion pairs."""

    def test_valid_fusion_pairs_return_expected_results(self):
        self.assertEqual(get_fusion_result(KNIGHT_CODE, BISHOP_CODE), ARCHBISHOP_CODE)
        self.assertEqual(get_fusion_result(ROOK_CODE, KNIGHT_CODE), CHANCELLOR_CODE)
        self.assertEqual(get_fusion_result(ROOK_CODE, BISHOP_CODE), TEMPO_BURST_KEY)

    def test_invalid_fusion_pairs_return_none(self):
        self.assertIsNone(get_fusion_result(BISHOP_CODE, KNIGHT_CODE))
        self.assertIsNone(get_fusion_result(KNIGHT_CODE, ROOK_CODE))
        self.assertIsNone(get_fusion_result(PAWN_CODE, BISHOP_CODE))


if __name__ == "__main__":
    unittest.main()
