"""Shared constants for board rules and game-domain values."""

import os
import sys

# Screen sizing
BOARD_WIDTH = 512
BOARD_HEIGHT = 512
INFO_PANEL_HEIGHT = 60
LOG_PANEL_WIDTH = 250
WIDTH = BOARD_WIDTH + LOG_PANEL_WIDTH
HEIGHT = BOARD_HEIGHT + (2 * INFO_PANEL_HEIGHT)
MAX_FPS = 60

# Board sizing
BOARD_SIZE = 8
BOARD_ROWS = BOARD_SIZE
BOARD_COLS = BOARD_SIZE
LAST_BOARD_INDEX = BOARD_SIZE - 1
DIMENSION = BOARD_SIZE
SQ_SIZE = BOARD_WIDTH // DIMENSION

# Piece codes
PAWN_CODE = "p"
KNIGHT_CODE = "N"
BISHOP_CODE = "B"
ROOK_CODE = "R"
QUEEN_CODE = "Q"
KING_CODE = "K"
STANDARD_PIECE_ORDER = [
    ROOK_CODE,
    KNIGHT_CODE,
    BISHOP_CODE,
    QUEEN_CODE,
    KING_CODE,
    BISHOP_CODE,
    KNIGHT_CODE,
    ROOK_CODE,
]

# Colors
WHITE = "w"
BLACK = "b"

# Action Points
STARTING_AP = 0
MAX_AP = 5
AP_GAIN_MOVE_INTERVAL = 2

# Events
EVENT_CYCLE_TURNS = 10
EVENT_WARNING_OFFSET = 8
EVENT_EXECUTE_OFFSET = 9


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    return os.path.join(base_path, relative_path)
