"""Board rendering helpers for the chess UI."""

import pygame as p

from ..constants import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    DIMENSION,
    HEIGHT,
    INFO_PANEL_HEIGHT,
    SQ_SIZE,
    WIDTH,
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


def draw_board(screen, dimension=DIMENSION, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT):
    """Draw the checkered board background."""
    colors = get_board_colors()
    for row in range(dimension):
        for col in range(dimension):
            color = colors[(row + col) % 2]
            p.draw.rect(
                screen,
                color,
                p.Rect(col * square_size, row * square_size + info_panel_height, square_size, square_size),
            )


def draw_highlights(screen, game_state, valid_moves, selected_square, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT):
    """Draw last-move and current-selection highlights."""
    for row, col in get_last_move_squares(game_state):
        surface = p.Surface((square_size, square_size))
        surface.set_alpha(100)
        surface.fill(p.Color("yellow"))
        screen.blit(surface, (col * square_size, row * square_size + info_panel_height))

    if selected_square == ():
        return

    row, col = selected_square
    piece = game_state.board.get_piece_at(row, col)
    if piece is None or piece.color != ("w" if game_state.white_to_move else "b"):
        return

    surface = p.Surface((square_size, square_size))
    surface.set_alpha(100)
    surface.fill(p.Color("blue"))
    screen.blit(surface, (col * square_size, row * square_size + info_panel_height))

    surface.fill(p.Color("yellow"))
    for target_row, target_col in get_highlight_targets(valid_moves, selected_square):
        screen.blit(surface, (target_col * square_size, target_row * square_size + info_panel_height))


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


def draw_event_overlays(screen, active_events, font, width=WIDTH, height=HEIGHT, info_panel_height=INFO_PANEL_HEIGHT):
    """Draw UI overlays owned by currently active events."""
    for event in active_events:
        event.draw(screen, font, width, height, info_panel_height)


def draw_endgame_text(screen, text, board_width=BOARD_WIDTH, board_height=BOARD_HEIGHT, info_panel_height=INFO_PANEL_HEIGHT):
    """Draw a centered endgame message over the board."""
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, 0, p.Color("Gray"))
    text_location = p.Rect(0, info_panel_height, board_width, board_height).move(
        board_width / 2 - text_object.get_width() / 2,
        board_height / 2 - text_object.get_height() / 2,
    )
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, p.Color("Black"))
    screen.blit(text_object, text_location.move(2, 2))


def draw_game_board(screen, game_state, valid_moves, selected_square, images, dragging, mouse_pos):
    """Render the full board area for the current frame."""
    draw_board(screen)
    draw_highlights(screen, game_state, valid_moves, selected_square)
    draw_pieces(screen, game_state.board.grid, images, selected_square if dragging else ())
    if dragging and selected_square:
        draw_dragged_piece(screen, game_state, selected_square, images, mouse_pos)
