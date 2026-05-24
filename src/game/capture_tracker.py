"""Explicit captured-piece tracking for real-move summaries."""

from ..constants import WHITE


class CaptureTracker:
    """Track captured pieces without inferring them from the live board."""

    def __init__(self):
        self.white_captured = []
        self.black_captured = []

    def record_move(self, move):
        """Record a captured piece for a real move."""
        if move.piece_captured is None:
            return

        if move.piece_moved.color == WHITE:
            self.white_captured.append(move.piece_captured.get_display_id())
        else:
            self.black_captured.append(move.piece_captured.get_display_id())

    def get_captured_pieces(self):
        """Return captured summaries for the UI as copied lists."""
        return list(self.white_captured), list(self.black_captured)
