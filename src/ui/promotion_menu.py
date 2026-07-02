"""Promotion menu drawing and click-resolution helpers."""

import pygame as p

from ..constants import BOARD_HEIGHT, BOARD_WIDTH, INFO_PANEL_HEIGHT, KNIGHT_CODE, BISHOP_CODE, QUEEN_CODE, ROOK_CODE, SQ_SIZE


PROMOTION_CHOICES = [QUEEN_CODE, ROOK_CODE, BISHOP_CODE, KNIGHT_CODE]


def get_promotion_menu_rect(
    move=None,
    board_width=BOARD_WIDTH,
    board_height=BOARD_HEIGHT,
    info_panel_height=INFO_PANEL_HEIGHT,
    square_size=SQ_SIZE,
):
    """Return the rect that bounds the promotion-choice menu."""
    menu_width = square_size
    menu_height = len(PROMOTION_CHOICES) * square_size
    if move is not None:
        # Draw vertically inline, starting at the target square and extending downwards or upwards
        start_x = move.end_col * square_size
        # If white is promoting at top (row 0), draw menu down. If black at bottom (row 7), draw menu up.
        if move.end_row <= 3:
            start_y = info_panel_height + move.end_row * square_size
        else:
            start_y = info_panel_height + (move.end_row + 1) * square_size - menu_height
    else:
        start_x = board_width // 2 - menu_width // 2
        start_y = info_panel_height + board_height // 2 - menu_height // 2
    return p.Rect(start_x, start_y, menu_width, menu_height)


def resolve_promotion_click(mouse_pos, move=None, menu_rect=None, square_size=SQ_SIZE):
    """Return the selected promotion piece code for a click inside the menu."""
    if menu_rect is None:
        menu_rect = get_promotion_menu_rect(move=move, square_size=square_size)
    if not menu_rect.collidepoint(mouse_pos):
        return None
    index = (mouse_pos[1] - menu_rect.y) // square_size
    if 0 <= index < len(PROMOTION_CHOICES):
        return PROMOTION_CHOICES[index]
    return None


def draw_promotion_menu(screen, color, images, menu_rect=None, square_size=SQ_SIZE):
    """Draw the promotion-choice menu."""
    if menu_rect is None:
        menu_rect = get_promotion_menu_rect(square_size=square_size)

    p.draw.rect(screen, p.Color("#4A3728"), menu_rect)  # Dark oak
    p.draw.rect(screen, p.Color("#C9A84C"), menu_rect, 2)  # Gold border

    for index, piece_code in enumerate(PROMOTION_CHOICES):
        image = images[color + piece_code]
        screen.blit(
            image,
            p.Rect(menu_rect.x, menu_rect.y + index * square_size, square_size, square_size),
        )
