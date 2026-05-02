# src/constants.py
import pygame

# Mặc định kích thước màn hình
BOARD_WIDTH = 512
BOARD_HEIGHT = 512
INFO_PANEL_HEIGHT = 60
WIDTH = BOARD_WIDTH
HEIGHT = BOARD_HEIGHT + (2 * INFO_PANEL_HEIGHT)
DIMENSION = 8  # Bàn cờ 8x8
SQ_SIZE = BOARD_WIDTH // DIMENSION # Kích thước 1 ô cờ
MAX_FPS = 60

# Mã màu RGB cho giao diện
COLOR_LIGHT = pygame.Color("white")
COLOR_DARK = pygame.Color("gray")
COLOR_HIGHLIGHT = pygame.Color("yellow")
COLOR_CHECK = pygame.Color("red")
