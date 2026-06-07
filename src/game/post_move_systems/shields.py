"""Shield-expiration post-move system."""

from .base import PostMoveSystem


class ShieldExpiryPostMoveSystem(PostMoveSystem):
    """Expire shields after the completed move."""

    def apply(self, game_state, move):
        """Expire shields based on the color that just completed a move."""
        game_state.expire_shields_after_turn(move.piece_moved.color)
