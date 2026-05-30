"""Runtime state for the Tempo Burst extra-move effect."""


class TempoBurstState:
    """Track the temporary extra-move state granted by Tempo Burst."""

    def __init__(self):
        self.pending = False
        self.piece = None
        self.owner = None

    def start(self, rook):
        """Start a new Tempo Burst for the given rook."""
        self.pending = True
        self.piece = rook
        self.owner = rook.color

    def clear(self):
        """Clear any active Tempo Burst state."""
        self.pending = False
        self.piece = None
        self.owner = None
