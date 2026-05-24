"""Pygame entry point for the chess application."""

import pygame as p

from .constants import BLACK, BOARD_HEIGHT, HEIGHT, INFO_PANEL_HEIGHT, MAX_FPS, WHITE, WIDTH
from .game.board import GameState
from .game.move import Move
from .ui.assets import load_images
from .ui.input_handler import (
    InputState,
    clear_promotion_pending,
    handle_board_mouse_down,
    handle_board_mouse_up,
    handle_mouse_motion,
    move_attempt_ready,
    reset_selection_state,
    resolve_invalid_click_selection,
    retain_origin_after_invalid_drag,
    set_promotion_pending,
)
from .ui.promotion_menu import draw_promotion_menu, resolve_promotion_click
from .ui.render_board import draw_endgame_text, draw_event_overlays, draw_game_board
from .ui.render_panels import draw_info_panels


def process_move_attempt(input_state, game_state, valid_moves):
    """Try to resolve the current UI move attempt against valid moves."""
    move = Move(input_state.player_clicks[0], input_state.player_clicks[1], game_state.board.grid)
    for valid_move in valid_moves:
        if move != valid_move:
            continue
        if valid_move.is_pawn_promotion:
            set_promotion_pending(input_state, valid_move)
            return True

        game_state.make_move(valid_move, is_real_move=True)
        reset_selection_state(input_state)
        return True

    if input_state.promotion_move_pending is None:
        if input_state.move_attempt_type == "drag":
            retain_origin_after_invalid_drag(input_state)
        else:
            resolve_invalid_click_selection(input_state, game_state)
    return False


def handle_promotion_click(input_state, game_state, mouse_pos):
    """Resolve a promotion-menu click and apply the chosen move if valid."""
    if input_state.promotion_move_pending is None:
        return False

    choice = resolve_promotion_click(mouse_pos)
    if choice is not None:
        game_state.make_move(input_state.promotion_move_pending, choice, is_real_move=True)
        clear_promotion_pending(input_state)
        reset_selection_state(input_state)
        return True

    clear_promotion_pending(input_state)
    reset_selection_state(input_state)
    return False


def main():
    """Run the main Pygame game loop."""
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))

    game_state = GameState()
    valid_moves = game_state.get_valid_moves()
    move_made = False

    images = load_images(image_loader=p.image.load, scaler=p.transform.scale)
    font_panel = p.font.SysFont("Helvetica", 16, True, False)
    input_state = InputState()
    running = True

    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
            elif event.type == p.MOUSEBUTTONDOWN:
                mouse_pos = p.mouse.get_pos()
                if input_state.promotion_move_pending is not None:
                    move_made = handle_promotion_click(input_state, game_state, mouse_pos) or move_made
                    continue
                handle_board_mouse_down(input_state, game_state, mouse_pos)
            elif event.type == p.MOUSEMOTION:
                handle_mouse_motion(input_state, p.mouse.get_pos())
            elif event.type == p.MOUSEBUTTONUP:
                handle_board_mouse_up(input_state, p.mouse.get_pos())
            elif event.type == p.KEYDOWN and event.key == p.K_z:
                game_state.event_manager.handle_undo()
                game_state.undo_move()
                game_state.event_manager.sync_state()
                clear_promotion_pending(input_state)
                reset_selection_state(input_state)
                move_made = True

            if move_attempt_ready(input_state):
                move_made = process_move_attempt(input_state, game_state, valid_moves) or move_made

        if move_made:
            valid_moves = game_state.get_valid_moves()
            move_made = False

        draw_game_board(
            screen,
            game_state,
            valid_moves,
            input_state.sq_selected,
            images,
            input_state.dragging,
            input_state.mouse_pos,
        )
        draw_info_panels(screen, game_state, images, font_panel)

        if input_state.promotion_move_pending:
            color = WHITE if game_state.white_to_move else BLACK
            draw_promotion_menu(screen, color, images)

        draw_event_overlays(screen, game_state.event_manager.active_events, font_panel)

        if game_state.checkmate:
            winner = "Black" if game_state.white_to_move else "White"
            draw_endgame_text(screen, f"CHECKMATE! {winner} wins")
        elif game_state.stalemate:
            draw_endgame_text(screen, "STALEMATE!")

        clock.tick(MAX_FPS)
        p.display.flip()


if __name__ == "__main__":
    main()
