"""Event-update post-move system."""

from .base import PostMoveSystem


class EventUpdatePostMoveSystem(PostMoveSystem):
    """Advance event timing after each completed full turn."""

    def apply(self, game_state, move):
        """Update event timing when a full turn finishes."""
        if game_state.just_finished_full_turn():
            game_state.event_manager.update()
