"""Captured-piece summary post-move system."""

from .base import PostMoveSystem


class CaptureTrackingPostMoveSystem(PostMoveSystem):
    """Record captured-piece summaries after a real move."""

    def apply(self, game_state, move):
        """Record any capture produced by the move."""
        game_state.capture_tracker.record_move(move)
