"""Post-move rule pipeline for real turn side effects."""


def run_post_move_systems(game_state, move):
    """Run post-move systems that should only happen after real moves."""
    game_state.capture_tracker.record_move(move)
    game_state.fusion_manager.handle_move(move)
    game_state.action_points.gain_for_move(move.piece_moved.color)
    game_state.expire_shields_after_turn(move.piece_moved.color)

    if game_state.just_finished_full_turn():
        game_state.event_manager.update()
