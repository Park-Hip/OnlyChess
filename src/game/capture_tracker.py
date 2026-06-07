"""Explicit captured-piece tracking for real-move summaries."""

from dataclasses import dataclass

from ..constants import WHITE


@dataclass(frozen=True)
class CapturedPieceRecord:
    """Store the minimum captured-piece data needed by UI and future rules."""

    color: str
    piece_code: str

    def to_display_id(self):
        """Return the current UI-facing sprite key for this record."""
        return f"{self.color}{self.piece_code}"


class CaptureTracker:
    """Track captured pieces without inferring them from the live board."""

    def __init__(self):
        self.white_captured = []
        self.black_captured = []

    def record_move(self, move):
        """Record a captured piece for a real move."""
        if move.piece_captured is None:
            return

        self.record_capture(move.piece_moved.color, move.piece_captured)

    def record_capture(self, capturing_color, captured_piece):
        """Record a captured piece from a move or ability."""
        if captured_piece is None:
            return

        if capturing_color == WHITE:
            self.white_captured.append(
                CapturedPieceRecord(
                    captured_piece.color,
                    captured_piece.get_piece_code(),
                )
            )
        else:
            self.black_captured.append(
                CapturedPieceRecord(
                    captured_piece.color,
                    captured_piece.get_piece_code(),
                )
            )

    def get_captured_pieces(self):
        """Return captured summaries for the UI as copied lists."""
        return (
            [record.to_display_id() for record in self.white_captured],
            [record.to_display_id() for record in self.black_captured],
        )
