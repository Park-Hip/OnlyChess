"""Help overlay modal for the Chess Fusion quick reference screen."""

import pygame as p

from ..constants import HEIGHT, WIDTH
from .ui_constants import (
    ACCENT_GOLD,
    ACCENT_GREEN,
    CARD_BG,
    PANEL_BG,
    SEPARATOR,
    SIDEBAR_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def draw_help_overlay(screen, fonts):
    """Draw a semi-transparent help overlay with fusion and ability reference.

    Args:
        screen: Pygame display surface.
        fonts: dict with 'title', 'normal', and 'small' pygame Font objects.
    """
    title_font = fonts["title"]
    font = fonts["normal"]
    small_font = fonts["small"]

    # Dimming overlay
    overlay = p.Surface((WIDTH, HEIGHT), p.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # Modal window
    modal_w = 540
    modal_h = 400
    modal_rect = p.Rect((WIDTH - modal_w) // 2, (HEIGHT - modal_h) // 2, modal_w, modal_h)
    p.draw.rect(screen, SIDEBAR_BG, modal_rect, border_radius=14)
    p.draw.rect(screen, ACCENT_GOLD, modal_rect, width=2, border_radius=14)

    # Title bar
    title_bar = p.Rect(modal_rect.x, modal_rect.y, modal_w, 50)
    p.draw.rect(screen, CARD_BG, title_bar, border_radius=14)
    # Fill bottom corners of title bar to be square
    p.draw.rect(screen, CARD_BG, p.Rect(title_bar.x, title_bar.y + 30, modal_w, 20))

    title = title_font.render("Quick Reference", True, ACCENT_GOLD)
    screen.blit(title, (modal_rect.centerx - title.get_width() // 2, modal_rect.y + 12))

    # Close button
    close_rect = _get_close_button_rect(modal_rect)
    p.draw.rect(screen, PANEL_BG, close_rect, border_radius=14)
    p.draw.rect(screen, TEXT_SECONDARY, close_rect, width=1, border_radius=14)
    close_text = small_font.render("X", True, TEXT_SECONDARY)
    screen.blit(close_text, (close_rect.centerx - close_text.get_width() // 2,
                             close_rect.centery - close_text.get_height() // 2))

    # Vertical divider
    p.draw.line(screen, SEPARATOR,
                (modal_rect.centerx, modal_rect.y + 65),
                (modal_rect.centerx, modal_rect.bottom - 20))

    _draw_fusion_column(screen, font, small_font, modal_rect)
    _draw_ability_column(screen, font, small_font, modal_rect)

    # Footer
    footer = small_font.render("Press [H] to close", True, TEXT_SECONDARY)
    screen.blit(footer, (modal_rect.centerx - footer.get_width() // 2, modal_rect.bottom - 25))


def _draw_fusion_column(screen, font, small_font, modal_rect):
    """Draw the left column listing valid fusion pairs."""
    col_x = modal_rect.x + 25
    screen.blit(font.render("Fusions", True, TEXT_PRIMARY), (col_x, modal_rect.y + 70))

    fusions = [
        ("Knight + Bishop", "Archbishop", "Moves as Knight or Bishop"),
        ("Rook + Knight", "Chancellor", "Moves as Rook or Knight"),
        ("Rook + Bishop", "Warden", "+ max 3 sq. diagonal"),
        ("Bishop + Rook", "Inquisitor", "+ max 3 sq. orthogonal"),
    ]
    y = modal_rect.y + 100
    for pair, result, desc in fusions:
        screen.blit(small_font.render(pair, True, TEXT_PRIMARY), (col_x, y))
        screen.blit(small_font.render("= " + result, True, ACCENT_GOLD), (col_x + 10, y + 20))
        screen.blit(small_font.render(desc, True, TEXT_SECONDARY), (col_x + 10, y + 40))
        y += 65


def _draw_ability_column(screen, font, small_font, modal_rect):
    """Draw the right column listing active abilities with AP costs."""
    col_x = modal_rect.centerx + 20
    screen.blit(font.render("Abilities", True, TEXT_PRIMARY), (col_x, modal_rect.y + 70))

    abilities = [
        ("Knight Swap", "2 AP", "Swap positions"),
        ("Bishop Snipe", "3 AP", "Ranged capture"),
        ("Rook Shield", "3 AP", "Protect adjacent"),
        ("Pawn Sprint", "1 AP", "Move 3 forward"),
    ]
    y = modal_rect.y + 105
    for name, cost, desc in abilities:
        screen.blit(small_font.render(name, True, TEXT_PRIMARY), (col_x, y))
        # AP cost pill
        cost_surf = small_font.render(cost, True, ACCENT_GREEN)
        cost_pill = p.Rect(modal_rect.right - 30 - cost_surf.get_width() - 8, y - 1,
                           cost_surf.get_width() + 12, 20)
        p.draw.rect(screen, PANEL_BG, cost_pill, border_radius=10)
        p.draw.rect(screen, ACCENT_GREEN, cost_pill, width=1, border_radius=10)
        screen.blit(cost_surf, (cost_pill.x + 6, cost_pill.y + 1))
        # Description
        screen.blit(small_font.render(desc, True, TEXT_SECONDARY), (col_x, y + 22))
        y += 58


def _get_close_button_rect(modal_rect):
    """Return the rect for the modal close button."""
    return p.Rect(modal_rect.right - 42, modal_rect.y + 12, 28, 28)


def get_help_modal_close_rect():
    """Return the close-button rect for external click detection."""
    modal_w = 540
    modal_h = 400
    modal_rect = p.Rect((WIDTH - modal_w) // 2, (HEIGHT - modal_h) // 2, modal_w, modal_h)
    return _get_close_button_rect(modal_rect)
