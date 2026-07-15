"""Action Point gain post-move system."""

from .base import PostMoveSystem


class ActionPointsPostMoveSystem(PostMoveSystem):
    """Award Action Point progress after a real move."""

    def apply(self, game_state, move):
        """Record one completed move for the mover."""
        game_state.action_points.gain_for_move(move.piece_moved.color)
