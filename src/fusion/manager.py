"""Fusion capture resolution."""

from ..pieces.dynamic_fused import DynamicFusedPiece
from ..constants import KING_CODE


class FusionManager:
    """Apply dynamic capture-based fusion rules after real moves."""

    def __init__(self, game_state):
        self.gs = game_state

    def handle_move(self, move):
        """Apply fusion effects for a real standard capture when eligible."""
        if not self._can_attempt_fusion(move):
            return None

        capturing_piece = getattr(move, "promoted_to_piece", None) or move.piece_moved
        captured_piece = move.piece_captured
        
        # Don't fuse Kings
        if captured_piece.name == KING_CODE or not capturing_piece.can_fuse():
            return None

        # Build component list
        base_components = capturing_piece.fusion_components if capturing_piece.has_fused else [capturing_piece.get_piece_code()]
        captured_components = captured_piece.fusion_components if getattr(captured_piece, "has_fused", False) else [captured_piece.get_piece_code()]
        
        new_components = list(base_components)
        for comp in captured_components:
            if comp not in new_components:
                new_components.append(comp)

        base_code = capturing_piece.primary_component_code if capturing_piece.has_fused else capturing_piece.get_piece_code()
        
        fused_piece = DynamicFusedPiece(capturing_piece.color, base_code, new_components, (move.end_row, move.end_col))
        fused_piece.has_moved = True
        
        # Copy shield if capturing piece was shielded
        fused_piece.is_shielded = getattr(capturing_piece, "is_shielded", False)
        fused_piece.shield_owner = getattr(capturing_piece, "shield_owner", None)
        fused_piece.shield_turns = getattr(capturing_piece, "shield_turns", 0)
        
        self.gs.board.replace_piece_at(move.end_row, move.end_col, fused_piece)
        move.fused_to_piece = fused_piece
        
        # Re-register shield in tracker
        if fused_piece.is_shielded:
            self.gs.shield_tracker.active_pieces = [
                fused_piece if p == capturing_piece else p 
                for p in self.gs.shield_tracker.active_pieces
            ]
            
        return "Dynamic"

    def _can_attempt_fusion(self, move):
        """Return whether a move meets basic fusion requirements."""
        if not getattr(move, "is_real_move", False):
            return False
        if move.piece_captured is None:
            return False
        return True
