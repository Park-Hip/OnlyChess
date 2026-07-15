"""Post-move rule pipeline for real turn side effects."""


def run_post_move_systems(game_state, move):
    """Run ordered post-move systems that should only happen after real moves."""
    for system in game_state.post_move_systems:
        system.apply(game_state, move)
