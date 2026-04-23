# src/constants.py
import pygame

# Mặc định kích thước màn hình
WIDTH = 512
HEIGHT = 512
DIMENSION = 8  # Bàn cờ 8x8
SQ_SIZE = WIDTH // DIMENSION # Kích thước 1 ô cờ
MAX_FPS = 15

# Mã màu RGB cho giao diện
COLOR_LIGHT = pygame.Color("white")
COLOR_DARK = pygame.Color("gray")
COLOR_HIGHLIGHT = pygame.Color("yellow")
COLOR_CHECK = pygame.Color("red")
