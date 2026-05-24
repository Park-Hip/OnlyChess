"""Post-move rule pipeline for real turn side effects."""


def run_post_move_systems(game_state, move):
    """Run post-move systems that should only happen after real moves."""
    game_state.capture_tracker.record_move(move)

    if game_state.just_finished_full_turn():
        game_state.event_manager.update()
