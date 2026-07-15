"""Ordered post-move systems for real move side effects."""

from .action_points import ActionPointsPostMoveSystem
from .capture_tracking import CaptureTrackingPostMoveSystem
from .events import EventUpdatePostMoveSystem
from .fusion import FusionPostMoveSystem
from .shields import ShieldExpiryPostMoveSystem


def create_default_post_move_systems(game_state):
    """Return the ordered post-move systems for the current ruleset."""
    return [
        CaptureTrackingPostMoveSystem(),
        FusionPostMoveSystem(),
        ActionPointsPostMoveSystem(),
        ShieldExpiryPostMoveSystem(),
        EventUpdatePostMoveSystem(),
    ]
