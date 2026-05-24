"""Promotion menu drawing and click-resolution helpers."""

import pygame as p

from ..constants import BOARD_HEIGHT, BOARD_WIDTH, INFO_PANEL_HEIGHT, KNIGHT_CODE, BISHOP_CODE, QUEEN_CODE, ROOK_CODE, SQ_SIZE


PROMOTION_CHOICES = [QUEEN_CODE, ROOK_CODE, BISHOP_CODE, KNIGHT_CODE]


def get_promotion_menu_rect(
    board_width=BOARD_WIDTH,
    board_height=BOARD_HEIGHT,
    info_panel_height=INFO_PANEL_HEIGHT,
    square_size=SQ_SIZE,
):
    """Return the rect that bounds the promotion-choice menu."""
    menu_width = len(PROMOTION_CHOICES) * square_size
    menu_height = square_size
    start_x = board_width // 2 - menu_width // 2
    start_y = info_panel_height + board_height // 2 - menu_height // 2
    return p.Rect(start_x, start_y, menu_width, menu_height)


def resolve_promotion_click(mouse_pos, menu_rect=None, square_size=SQ_SIZE):
    """Return the selected promotion piece code for a click inside the menu."""
    if menu_rect is None:
        menu_rect = get_promotion_menu_rect(square_size=square_size)
    if not menu_rect.collidepoint(mouse_pos):
        return None
    index = (mouse_pos[0] - menu_rect.x) // square_size
    if 0 <= index < len(PROMOTION_CHOICES):
        return PROMOTION_CHOICES[index]
    return None


def draw_promotion_menu(screen, color, images, menu_rect=None, square_size=SQ_SIZE):
    """Draw the promotion-choice menu centered over the board."""
    if menu_rect is None:
        menu_rect = get_promotion_menu_rect(square_size=square_size)

    p.draw.rect(screen, p.Color("gray"), menu_rect)
    p.draw.rect(screen, p.Color("black"), menu_rect, 2)

    for index, piece_code in enumerate(PROMOTION_CHOICES):
        image = images[color + piece_code]
        screen.blit(
            image,
            p.Rect(menu_rect.x + index * square_size, menu_rect.y, square_size, square_size),
        )
