"""Helpers for safe board-coordinate access."""

from ..constants import BOARD_COLS, BOARD_ROWS


def is_inside_board(row, col):
    """Return True when the given coordinate is on the board."""
    return 0 <= row < BOARD_ROWS and 0 <= col < BOARD_COLS


def safe_get_piece(board_grid, row, col):
    """Return the piece on a square or None when the square is outside the board."""
    if not is_inside_board(row, col):
        return None
    return board_grid[row][col]


def set_piece(board_grid, row, col, piece):
    """Set a square when the coordinate is valid."""
    if not is_inside_board(row, col):
        raise IndexError(f"Square {(row, col)} is outside the board.")
    board_grid[row][col] = piece
