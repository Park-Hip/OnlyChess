"""Dynamic fused piece implementation."""

from .base import Piece
from .registry import create_piece

class DynamicFusedPiece(Piece):
    """A piece that dynamically inherits moves from all its captured components."""

    def __init__(self, color, base_piece_code, components, pos):
        """
        color: 'w' or 'b'
        base_piece_code: The original piece (e.g. 'R') before any fusions.
        components: List of piece codes this piece has absorbed.
        pos: (row, col)
        """
        # Dynamic pieces don't have a static piece_code or material_value,
        # we compute them dynamically or use the base piece.
        super().__init__(color, base_piece_code, pos)
        self.piece_code = base_piece_code
        self.fusion_components = list(components)
        self.primary_component_code = base_piece_code
        
        # Determine material value from the primary component
        dummy = create_piece(base_piece_code, color, pos)
        self.material_value = dummy.material_value if dummy else 0
        
        # A dynamic piece can fuse infinitely.
        self.has_fused = True

    def can_fuse(self):
        """Dynamic pieces can continue to fuse endlessly."""
        return True

    def _calculate_moves(self, gs):
        """Generate moves by unioning the moves of all absorbed components."""
        moves = []
        seen_destinations = set()
        
        for code in self.fusion_components:
            dummy = create_piece(code, self.color, self.pos)
            if dummy is None:
                continue
                
            dummy_moves = dummy._calculate_moves(gs)
            
            for m in dummy_moves:
                dest = (m.end_row, m.end_col)
                if dest not in seen_destinations:
                    seen_destinations.add(dest)
                    moves.append(m)
                    
        return moves

    def get_piece_code(self):
        return self.piece_code

    def get_sprite_key(self):
        """Return the base piece key for rendering. The UI will overlay text."""
        return f"{self.color}{self.piece_code}"

    def get_display_id(self):
        return f"{self.color}{self.piece_code}"

    def get_fusion_tags(self):
        """Return all components so abilities can recognize them."""
        return self.fusion_components

    def get_move_profile_name(self):
        return "Dynamic (" + "+".join(self.fusion_components) + ")"
