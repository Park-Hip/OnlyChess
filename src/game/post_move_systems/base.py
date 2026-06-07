"""Base contract for ordered post-move side effects."""


class PostMoveSystem:
    """Base class for one ordered post-move side effect."""

    def apply(self, game_state, move):
        """Apply this side effect after a real move."""
        raise NotImplementedError
