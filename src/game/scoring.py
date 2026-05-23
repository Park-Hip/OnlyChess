"""Material scoring helpers for board summaries."""

from ..constants import WHITE


def calculate_material_advantage(board_grid):
    """Return white material minus black material for the current grid."""
    white_score = 0
    black_score = 0

    for row in board_grid:
        for piece in row:
            if piece is None:
                continue
            if piece.color == WHITE:
                white_score += piece.get_material_value()
            else:
                black_score += piece.get_material_value()

    return white_score - black_score
