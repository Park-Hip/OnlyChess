"""Tests for fusion rule lookup."""

import unittest

from src.constants import (
    ARCHBISHOP_CODE, BISHOP_CODE, CHANCELLOR_CODE,
    INQUISITOR_CODE, KING_CODE, KNIGHT_CODE,
    PAWN_CODE, ROOK_CODE, WARDEN_CODE,
)
from src.fusion.rules import get_fusion_result


class FusionRuleTests(unittest.TestCase):
    """Verify valid and invalid fusion pairs."""

    def test_valid_fusion_pairs_return_expected_results(self):
        self.assertEqual(get_fusion_result(KNIGHT_CODE, BISHOP_CODE), ARCHBISHOP_CODE)
        self.assertEqual(get_fusion_result(BISHOP_CODE, KNIGHT_CODE), ARCHBISHOP_CODE)
        self.assertEqual(get_fusion_result(ROOK_CODE, KNIGHT_CODE), CHANCELLOR_CODE)
        self.assertEqual(get_fusion_result(KNIGHT_CODE, ROOK_CODE), CHANCELLOR_CODE)
        self.assertEqual(get_fusion_result(ROOK_CODE, BISHOP_CODE), WARDEN_CODE)
        self.assertEqual(get_fusion_result(BISHOP_CODE, ROOK_CODE), INQUISITOR_CODE)

    def test_invalid_fusion_pairs_return_none(self):
        self.assertIsNone(get_fusion_result(PAWN_CODE, BISHOP_CODE))
        self.assertIsNone(get_fusion_result(KING_CODE, ROOK_CODE))


if __name__ == "__main__":
    unittest.main()
