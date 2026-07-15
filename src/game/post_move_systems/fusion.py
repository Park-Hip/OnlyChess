"""Fusion-resolution post-move system."""

from .base import PostMoveSystem


class FusionPostMoveSystem(PostMoveSystem):
    """Resolve capture-triggered fusion after a real move."""

    def apply(self, game_state, move):
        """Apply fusion logic for the completed move."""
        game_state.fusion_manager.handle_move(move)
