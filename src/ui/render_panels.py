"""Panel rendering helpers for player summaries and event countdown UI."""

import pygame as p

from ..constants import BOARD_WIDTH, HEIGHT, INFO_PANEL_HEIGHT, WIDTH
from ..constants import BLACK, WHITE
from .ui_constants import ACCENT_GOLD, ACCENT_GREEN, CARD_BG, PANEL_BG, TEXT_PRIMARY


MINI_PIECE_SIZE = 24


def get_material_text(score, is_top_panel):
    """Return the score text that should appear on a player panel."""
    if is_top_panel and score < 0:
        return f"+{-score}"
    if not is_top_panel and score > 0:
        return f"+{score}"
    return ""


def get_ap_text(game_state, color):
    """Return AP text for one player panel."""
    return f"AP: {game_state.action_points.get_ap(color)}"


def get_ability_error_text(input_state):
    """Return transient ability error text."""
    return getattr(input_state, "ability_error", "")


def draw_captured_pieces_row(screen, captured_pieces, images, start_x, start_y, mini_size=MINI_PIECE_SIZE):
    """Draw a row of captured-piece mini-icons and return the next x position."""
    current_x = start_x
    for piece_key in captured_pieces:
        image = p.transform.scale(images[piece_key], (mini_size, mini_size))
        screen.blit(image, (current_x, start_y))
        current_x += mini_size // 2
    return current_x


def _draw_ap_pill(screen, font, text, x, y, active=False):
    """Draw an AP value inside a small green pill badge."""
    color = ACCENT_GOLD if active else ACCENT_GREEN
    ap_surf = font.render(text, True, color)
    pill_rect = p.Rect(x, y, ap_surf.get_width() + 16, 26)
    p.draw.rect(screen, CARD_BG, pill_rect, border_radius=13)
    p.draw.rect(screen, color, pill_rect, width=2 if active else 1, border_radius=13)
    screen.blit(ap_surf, (pill_rect.x + 8, pill_rect.y + 4))


def draw_info_panels(screen, game_state, images, font):
    """Draw player panels, captured pieces, score summaries, and event countdown."""
    # --- Top Panel (Player 2 / Black) ---
    p.draw.rect(screen, PANEL_BG, p.Rect(0, 0, WIDTH, INFO_PANEL_HEIGHT))
    p.draw.line(screen, ACCENT_GOLD, (0, INFO_PANEL_HEIGHT - 1), (WIDTH, INFO_PANEL_HEIGHT - 1))

    score = game_state.get_material_advantage()
    white_captured, black_captured = game_state.get_captured_pieces()

    is_black_turn = not game_state.white_to_move
    name_text_black = font.render("Player 2", True, ACCENT_GOLD if is_black_turn else TEXT_PRIMARY)
    screen.blit(name_text_black, (10, 10))
    _draw_ap_pill(screen, font, get_ap_text(game_state, BLACK), 110, 8, is_black_turn)

    next_x = draw_captured_pieces_row(screen, black_captured, images, 10, 35)
    black_score_text = get_material_text(score, is_top_panel=True)
    if black_score_text:
        score_text = font.render(black_score_text, True, TEXT_PRIMARY)
        screen.blit(score_text, (next_x + 10, 36))

    # --- Bottom Panel (Player 1 / White) ---
    bottom_y = HEIGHT - INFO_PANEL_HEIGHT
    p.draw.rect(screen, PANEL_BG, p.Rect(0, bottom_y, WIDTH, INFO_PANEL_HEIGHT))
    p.draw.line(screen, ACCENT_GOLD, (0, bottom_y), (WIDTH, bottom_y))

    is_white_turn = game_state.white_to_move
    name_text_white = font.render("Player 1", True, ACCENT_GOLD if is_white_turn else TEXT_PRIMARY)
    screen.blit(name_text_white, (10, bottom_y + 10))
    _draw_ap_pill(screen, font, get_ap_text(game_state, WHITE), 110, bottom_y + 8, is_white_turn)

    next_x = draw_captured_pieces_row(screen, white_captured, images, 10, bottom_y + 35)
    white_score_text = get_material_text(score, is_top_panel=False)
    if white_score_text:
        score_text = font.render(white_score_text, True, TEXT_PRIMARY)
        screen.blit(score_text, (next_x + 10, bottom_y + 36))

    # Turn counter and event countdown (right side of bottom panel)
    turn_text = font.render(f"Turn: {game_state.get_turn_number()}", True, TEXT_PRIMARY)
    event_text = font.render(
        f"Next Event in: {game_state.get_turns_to_next_event()}",
        True,
        ACCENT_GOLD,
    )
    screen.blit(turn_text, (BOARD_WIDTH - 150, bottom_y + 10))
    screen.blit(event_text, (BOARD_WIDTH - 150, bottom_y + 30))
