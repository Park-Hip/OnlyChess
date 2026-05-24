"""Panel rendering helpers for player summaries and event countdown UI."""

import pygame as p

from ..constants import HEIGHT, INFO_PANEL_HEIGHT, WIDTH
from .ui_constants import PANEL_BACKGROUND


MINI_PIECE_SIZE = 24


def get_material_text(score, is_top_panel):
    """Return the score text that should appear on a player panel."""
    if is_top_panel and score < 0:
        return f"+{-score}"
    if not is_top_panel and score > 0:
        return f"+{score}"
    return ""


def draw_captured_pieces_row(screen, captured_pieces, images, start_x, start_y, mini_size=MINI_PIECE_SIZE):
    """Draw a row of captured-piece mini-icons and return the next x position."""
    current_x = start_x
    for piece_key in captured_pieces:
        image = p.transform.scale(images[piece_key], (mini_size, mini_size))
        screen.blit(image, (current_x, start_y))
        current_x += mini_size // 2
    return current_x


def draw_info_panels(screen, game_state, images, font):
    """Draw player panels, captured pieces, score summaries, and event countdown."""
    p.draw.rect(screen, p.Color(PANEL_BACKGROUND), p.Rect(0, 0, WIDTH, INFO_PANEL_HEIGHT))
    p.draw.rect(screen, p.Color(PANEL_BACKGROUND), p.Rect(0, HEIGHT - INFO_PANEL_HEIGHT, WIDTH, INFO_PANEL_HEIGHT))

    score = game_state.get_material_advantage()
    white_captured, black_captured = game_state.get_captured_pieces()

    name_text_black = font.render("Player 2", True, p.Color("white"))
    screen.blit(name_text_black, (10, 10))

    next_x = draw_captured_pieces_row(screen, black_captured, images, 10, 32)
    black_score_text = get_material_text(score, is_top_panel=True)
    if black_score_text:
        score_text = font.render(black_score_text, True, p.Color("white"))
        screen.blit(score_text, (next_x + 10, 34))

    name_text_white = font.render("Player 1", True, p.Color("white"))
    screen.blit(name_text_white, (10, HEIGHT - INFO_PANEL_HEIGHT + 10))

    next_x = draw_captured_pieces_row(screen, white_captured, images, 10, HEIGHT - INFO_PANEL_HEIGHT + 32)
    white_score_text = get_material_text(score, is_top_panel=False)
    if white_score_text:
        score_text = font.render(white_score_text, True, p.Color("white"))
        screen.blit(score_text, (next_x + 10, HEIGHT - INFO_PANEL_HEIGHT + 34))

    turn_text = font.render(f"Turn: {game_state.get_turn_number()}", True, p.Color("white"))
    event_text = font.render(
        f"Next Event in: {game_state.get_turns_to_next_event()}",
        True,
        p.Color("yellow"),
    )
    screen.blit(turn_text, (WIDTH - 150, HEIGHT - INFO_PANEL_HEIGHT + 10))
    screen.blit(event_text, (WIDTH - 150, HEIGHT - INFO_PANEL_HEIGHT + 30))
