import unittest

from src.constants import KNIGHT_CODE, ROOK_CODE, BLACK, WHITE
from src.pieces.dynamic_fused import DynamicFusedPiece

class DynamicFusionTests(unittest.TestCase):

    def test_dynamic_fused_piece_components(self):
        """Test that dynamic fused pieces properly record their components."""
        # A Rook that captures a Knight
        fused_piece = DynamicFusedPiece(WHITE, ROOK_CODE, [ROOK_CODE, KNIGHT_CODE], (4, 4))
        
        self.assertEqual(fused_piece.color, WHITE)
        self.assertEqual(fused_piece.get_piece_code(), ROOK_CODE)
        self.assertEqual(fused_piece.fusion_components, [ROOK_CODE, KNIGHT_CODE])
        self.assertEqual(fused_piece.primary_component_code, ROOK_CODE)
        self.assertTrue(fused_piece.has_fused)

    def test_dynamic_fused_piece_get_sprite_key(self):
        """Test that the base sprite key is returned correctly for UI."""
        fused_piece = DynamicFusedPiece(BLACK, KNIGHT_CODE, [KNIGHT_CODE, ROOK_CODE], (0, 0))
        self.assertEqual(fused_piece.get_sprite_key(), BLACK + KNIGHT_CODE)
        
    def test_dynamic_fused_piece_tags(self):
        """Test that tags return all components."""
        fused_piece = DynamicFusedPiece(WHITE, ROOK_CODE, [ROOK_CODE, KNIGHT_CODE], (4, 4))
        self.assertEqual(set(fused_piece.get_fusion_tags()), {ROOK_CODE, KNIGHT_CODE})

if __name__ == "__main__":
    unittest.main()
