"""Shared constants for board rules and UI rendering."""

import pygame

# Screen sizing
BOARD_WIDTH = 512
BOARD_HEIGHT = 512
INFO_PANEL_HEIGHT = 60
WIDTH = BOARD_WIDTH
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

# UI colors
COLOR_LIGHT = pygame.Color("white")
COLOR_DARK = pygame.Color("gray")
COLOR_HIGHLIGHT = pygame.Color("yellow")
COLOR_CHECK = pygame.Color("red")
