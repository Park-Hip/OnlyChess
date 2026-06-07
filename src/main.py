"""Pygame entry point for the chess application."""

import pygame as p

from .abilities import use_ability
from .constants import BLACK, BOARD_HEIGHT, HEIGHT, INFO_PANEL_HEIGHT, MAX_FPS, WHITE, WIDTH
from .game.board import GameState
from .game.move import Move
from .ui.assets import load_images
from .ui.input_handler import (
    InputState,
    ability_attempt_ready,
    clear_ability_state,
    clear_promotion_pending,
    handle_board_mouse_down,
    handle_board_mouse_up,
    handle_mouse_motion,
    move_attempt_ready,
    reset_selection_state,
    resolve_invalid_click_selection,
    retain_origin_after_invalid_drag,
    set_promotion_pending,
    select_ability,
)
from .ui.ability_menu import draw_ability_menu, get_available_ability_keys, get_ability_menu_rect, resolve_ability_menu_click
from .ui.promotion_menu import draw_promotion_menu, resolve_promotion_click
from .ui.render_board import draw_endgame_text, draw_event_overlays, draw_game_board
from .ui.render_panels import draw_info_panels, get_ability_error_text


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
    if choice is None:
        return False

    game_state.make_move(input_state.promotion_move_pending, choice, is_real_move=True)
    clear_promotion_pending(input_state)
    reset_selection_state(input_state)
    return True


def process_ability_attempt(input_state, game_state):
    """Try to execute the selected ability against the chosen target."""
    target_square = input_state.player_clicks[0]
    succeeded = use_ability(
        input_state.selected_ability_key,
        game_state,
        input_state.ability_source_square,
        target_square,
    )
    if succeeded:
        clear_ability_state(input_state)
        reset_selection_state(input_state)
        return True
    input_state.ability_error = "Invalid ability target"
    input_state.player_clicks = []
    return False


def handle_ability_menu_click(input_state, game_state, mouse_pos):
    """Resolve a click inside an open ability menu."""
    if not input_state.ability_menu_square:
        return False
    piece = game_state.board.get_piece_at(input_state.ability_menu_square[0], input_state.ability_menu_square[1])
    ability_keys = get_available_ability_keys(game_state, piece)
    menu_rect = get_ability_menu_rect(input_state.ability_menu_square)
    ability_key = resolve_ability_menu_click(mouse_pos, ability_keys, menu_rect)
    if ability_key is None:
        clear_ability_state(input_state)
        return False
    select_ability(input_state, ability_key, input_state.ability_menu_square)
    return True


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
                if input_state.ability_menu_square:
                    handle_ability_menu_click(input_state, game_state, mouse_pos)
                    continue
                handle_board_mouse_down(input_state, game_state, mouse_pos, event.button)
            elif event.type == p.MOUSEMOTION:
                handle_mouse_motion(input_state, p.mouse.get_pos())
            elif event.type == p.MOUSEBUTTONUP:
                handle_board_mouse_up(input_state, p.mouse.get_pos())
            if move_attempt_ready(input_state):
                move_made = process_move_attempt(input_state, game_state, valid_moves) or move_made
            if ability_attempt_ready(input_state):
                move_made = process_ability_attempt(input_state, game_state) or move_made

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
        ability_error = get_ability_error_text(input_state)
        if ability_error:
            error_text = font_panel.render(ability_error, True, p.Color("orange"))
            screen.blit(error_text, (10, INFO_PANEL_HEIGHT + 10))

        if input_state.promotion_move_pending:
            color = WHITE if game_state.white_to_move else BLACK
            draw_promotion_menu(screen, color, images)
        if input_state.ability_menu_square:
            piece = game_state.board.get_piece_at(input_state.ability_menu_square[0], input_state.ability_menu_square[1])
            draw_ability_menu(screen, font_panel, game_state, piece, input_state.ability_menu_square)

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
