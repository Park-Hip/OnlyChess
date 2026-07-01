"""Board rendering helpers for the chess UI."""

import pygame as p

from ..constants import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    DIMENSION,
    INFO_PANEL_HEIGHT,
    SQ_SIZE,
)
from .ui_constants import COLOR_DARK, COLOR_LIGHT


def get_board_colors():
    """Return the alternating board colors used for the chessboard."""
    return [COLOR_LIGHT, COLOR_DARK]


def get_last_move_squares(game_state):
    """Return the start/end squares of the most recent move if one exists."""
    if len(game_state.move_log) == 0:
        return []
    last_move = game_state.move_log[-1]
    if not hasattr(last_move, "start_row") or not hasattr(last_move, "end_row"):
        return []
    return [
        (last_move.start_row, last_move.start_col),
        (last_move.end_row, last_move.end_col),
    ]


def get_highlight_targets(valid_moves, square):
    """Return legal destination squares for the selected origin square."""
    row, col = square
    return [
        (move.end_row, move.end_col)
        for move in valid_moves
        if move.start_row == row and move.start_col == col
    ]


def draw_board(screen, dimension=DIMENSION, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT, fonts=None):
    """Draw the checkered board background and coordinate notations."""
    colors = get_board_colors()
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    
    for row in range(dimension):
        for col in range(dimension):
            square_color_idx = (row + col) % 2
            color = colors[square_color_idx]
            text_color = colors[1 - square_color_idx]
            
            rect = p.Rect(col * square_size, row * square_size + info_panel_height, square_size, square_size)
            p.draw.rect(screen, color, rect)
            
            if fonts:
                font = fonts["small"]
                if col == 0:
                    text_surface = font.render(ranks[row], True, text_color)
                    screen.blit(text_surface, (rect.x + 2, rect.y + 2))
                if row == 7:
                    text_surface = font.render(files[col], True, text_color)
                    text_rect = text_surface.get_rect(bottomright=(rect.right - 2, rect.bottom - 2))
                    screen.blit(text_surface, text_rect)


def draw_highlights(screen, game_state, valid_moves, selected_square, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT):
    """Draw last-move and current-selection highlights."""
    for row, col in get_last_move_squares(game_state):
        surface = p.Surface((square_size, square_size))
        surface.set_alpha(80)
        surface.fill(p.Color("#C9A84C"))  # Gold tint for last move
        screen.blit(surface, (col * square_size, row * square_size + info_panel_height))

    if selected_square == ():
        return

    row, col = selected_square
    piece = game_state.board.get_piece_at(row, col)
    if piece is None or piece.color != ("w" if game_state.white_to_move else "b"):
        return

    surface = p.Surface((square_size, square_size))
    surface.set_alpha(100)
    surface.fill(p.Color("#8B6F47"))  # Warm brown tint for selection
    screen.blit(surface, (col * square_size, row * square_size + info_panel_height))

    valid_surface = p.Surface((square_size, square_size), p.SRCALPHA)
    for target_row, target_col in get_highlight_targets(valid_moves, selected_square):
        target_piece = game_state.board.get_piece_at(target_row, target_col)
        valid_surface.fill((0, 0, 0, 0))
        if target_piece is None:
            # Dot for empty square
            p.draw.circle(valid_surface, (201, 168, 76, 120), (square_size // 2, square_size // 2), square_size // 6)
        else:
            # Hollow ring for captures
            p.draw.circle(valid_surface, (201, 168, 76, 120), (square_size // 2, square_size // 2), square_size // 2, width=6)
        screen.blit(valid_surface, (target_col * square_size, target_row * square_size + info_panel_height))


def draw_pieces(screen, board_grid, images, dragged_square=(), dimension=DIMENSION, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT):
    """Draw all board pieces except a currently dragged one."""
    for row in range(dimension):
        for col in range(dimension):
            if (row, col) == dragged_square:
                continue
            piece = board_grid[row][col]
            if piece:
                screen.blit(
                    images[piece.get_sprite_key()],
                    p.Rect(col * square_size, row * square_size + info_panel_height, square_size, square_size),
                )


def draw_shield_overlays(screen, board_grid, dimension=DIMENSION, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT):
    """Draw a simple outline around shielded pieces."""
    for row in range(dimension):
        for col in range(dimension):
            piece = board_grid[row][col]
            if piece is not None and getattr(piece, "is_shielded", False):
                rect = p.Rect(
                    col * square_size + 4,
                    row * square_size + info_panel_height + 4,
                    square_size - 8,
                    square_size - 8,
                )
                p.draw.rect(screen, p.Color("cyan"), rect, 3)


def draw_dragged_piece(screen, game_state, dragged_square, images, mouse_pos, square_size=SQ_SIZE):
    """Draw the currently dragged piece under the mouse cursor."""
    if not dragged_square:
        return
    row, col = dragged_square
    piece = game_state.board.get_piece_at(row, col)
    if piece is None:
        return
    image = images[piece.get_sprite_key()]
    screen.blit(image, p.Rect(mouse_pos[0] - square_size // 2, mouse_pos[1] - square_size // 2, square_size, square_size))





def draw_endgame_text(screen, text, board_width=BOARD_WIDTH, board_height=BOARD_HEIGHT, info_panel_height=INFO_PANEL_HEIGHT):
    """Draw a centered endgame message over the board."""
    font = p.font.SysFont("Segoe UI", 32, True, False)
    text_object = font.render(text, 0, p.Color("#C9A84C"))
    text_location = p.Rect(0, info_panel_height, board_width, board_height).move(
        board_width / 2 - text_object.get_width() / 2,
        board_height / 2 - text_object.get_height() / 2,
    )
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color("#2B1B17"))
    screen.blit(text_object, text_location.move(2, 2))


def draw_game_board(screen, game_state, valid_moves, selected_square, images, dragging, mouse_pos, fonts=None):
    """Render the full board area for the current frame."""
    draw_board(screen, fonts=fonts)
    draw_highlights(screen, game_state, valid_moves, selected_square)
    draw_pieces(screen, game_state.board.grid, images, selected_square if dragging else ())
    draw_shield_overlays(screen, game_state.board.grid)
    if dragging and selected_square:
        draw_dragged_piece(screen, game_state, selected_square, images, mouse_pos)
