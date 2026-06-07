"""Ability menu helpers."""

import pygame as p

from ..abilities import get_abilities_for_piece
from ..constants import INFO_PANEL_HEIGHT, SQ_SIZE


ABILITY_MENU_WIDTH = 150
ABILITY_MENU_ITEM_HEIGHT = 24


def get_ability_menu_rect(square, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT):
    """Return the menu rectangle anchored beside a board square."""
    row, col = square
    return p.Rect(
        col * square_size + square_size,
        row * square_size + info_panel_height,
        ABILITY_MENU_WIDTH,
        ABILITY_MENU_ITEM_HEIGHT,
    )


def get_available_ability_keys(game_state, piece):
    """Return ability keys that the piece can afford right now."""
    return [
        ability.ability_key
        for ability in get_abilities_for_piece(piece)
        if game_state.action_points.can_spend(piece.color, ability.ap_cost)
    ]


def resolve_ability_menu_click(mouse_pos, ability_keys, menu_rect, item_height=ABILITY_MENU_ITEM_HEIGHT):
    """Return the selected ability key for a click inside the menu."""
    full_rect = p.Rect(menu_rect.x, menu_rect.y, menu_rect.width, menu_rect.height * len(ability_keys))
    if not full_rect.collidepoint(mouse_pos):
        return None
    index = (mouse_pos[1] - menu_rect.y) // item_height
    if 0 <= index < len(ability_keys):
        return ability_keys[index]
    return None


def draw_ability_menu(screen, font, game_state, piece, square):
    """Draw a small ability menu for one selected piece."""
    ability_keys = get_available_ability_keys(game_state, piece)
    if not ability_keys:
        return
    rect = get_ability_menu_rect(square)
    full_rect = p.Rect(rect.x, rect.y, rect.width, rect.height * len(ability_keys))
    p.draw.rect(screen, p.Color("black"), full_rect)
    p.draw.rect(screen, p.Color("white"), full_rect, 1)
    for index, ability_key in enumerate(ability_keys):
        text = font.render(ability_key, True, p.Color("white"))
        screen.blit(text, (rect.x + 6, rect.y + index * rect.height + 4))
