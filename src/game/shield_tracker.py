"""Shield state tracking for temporary protected pieces."""


class ShieldTracker:
    """Track shielded pieces and expire them after the correct turn."""

    def __init__(self):
        self.active_pieces = []

    def add(self, piece, owner_color):
        """Apply a temporary shield to one piece."""
        piece.is_shielded = True
        piece.shield_owner = owner_color
        piece.shield_turns = 1
        if piece not in self.active_pieces:
            self.active_pieces.append(piece)

    def expire_after_turn(self, completed_turn_color):
        """Remove shields whose protected owner did not just move."""
        for piece in list(self.active_pieces):
            if getattr(piece, "shield_owner", None) == completed_turn_color:
                continue
            piece.is_shielded = False
            piece.shield_turns = 0
            piece.shield_owner = None
            self.active_pieces.remove(piece)
