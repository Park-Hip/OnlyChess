"""Ability menu helpers."""

import pygame as p

from ..abilities import get_abilities_for_piece
from ..constants import INFO_PANEL_HEIGHT, SQ_SIZE
from .ui_constants import ACCENT_GOLD, ACCENT_GREEN, CARD_BG, PANEL_BG, SEPARATOR, TEXT_PRIMARY


ABILITY_MENU_WIDTH = 180
ABILITY_MENU_ITEM_HEIGHT = 40


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


def _get_ability_details(game_state, piece):
    """Return list of (ability_key, display_name, ap_cost) for affordable abilities."""
    return [
        (ability.ability_key, ability.display_name, ability.ap_cost)
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
    """Draw a styled ability menu for one selected piece."""
    details = _get_ability_details(game_state, piece)
    if not details:
        return
    rect = get_ability_menu_rect(square)
    full_rect = p.Rect(rect.x, rect.y, rect.width, rect.height * len(details))

    # Background with rounded corners and gold border
    p.draw.rect(screen, CARD_BG, full_rect, border_radius=8)
    p.draw.rect(screen, ACCENT_GOLD, full_rect, width=1, border_radius=8)

    small_font = p.font.SysFont("Segoe UI", 13)

    for index, (ability_key, display_name, ap_cost) in enumerate(details):
        item_y = rect.y + index * rect.height

        # Separator between items
        if index > 0:
            p.draw.line(screen, SEPARATOR, (rect.x + 8, item_y), (rect.x + rect.width - 8, item_y))

        # Display name
        name_text = font.render(display_name, True, TEXT_PRIMARY)
        screen.blit(name_text, (rect.x + 10, item_y + 10))

        # AP cost pill on the right
        cost_str = f"{ap_cost} AP"
        cost_surf = small_font.render(cost_str, True, ACCENT_GREEN)
        pill_w = cost_surf.get_width() + 10
        pill_rect = p.Rect(rect.x + rect.width - pill_w - 8, item_y + 11, pill_w, 18)
        p.draw.rect(screen, PANEL_BG, pill_rect, border_radius=9)
        p.draw.rect(screen, ACCENT_GREEN, pill_rect, width=1, border_radius=9)
        screen.blit(cost_surf, (pill_rect.x + 5, pill_rect.y + 1))
