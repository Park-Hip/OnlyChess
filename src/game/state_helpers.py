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
    """Place a piece on the board, updating its internal position."""
    if not is_inside_board(row, col):
        raise IndexError(f"Square {(row, col)} is outside the board.")
    board_grid[row][col] = piece
    if piece:
        piece.pos = (row, col)


def format_square(row, col):
    """Convert board coordinates to chess square notation (e.g., (6, 4) -> 'e2')."""
    files = "abcdefgh"
    rank = 8 - row
    return f"{files[col]}{rank}"


def format_piece_fan(piece):
    """Convert a piece to its compact event FAN representation (e.g., 'wN', 'bP', 'bC')."""
    if piece is None:
        return ""
    color_prefix = piece.color
    code = piece.get_piece_code()
    # Ensure pawns get a 'P' in event logs, even though they have no letter in standard move SAN
    letter = "P" if code == "p" else code.upper()
    return f"{color_prefix}{letter}"
