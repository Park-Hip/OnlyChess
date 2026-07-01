"""Pygame entry point for the chess application."""

import pygame as p

from .abilities import use_ability
from .constants import BLACK, BOARD_WIDTH, HEIGHT, INFO_PANEL_HEIGHT, MAX_FPS, WHITE, WIDTH
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
from .ui.help_overlay import draw_help_overlay, get_help_modal_close_rect
from .ui.message_log import MessageLog, draw_message_log, format_ability_fan, format_move_fan, get_help_button_rect
from .ui.promotion_menu import draw_promotion_menu, get_promotion_menu_rect, resolve_promotion_click
from .ui.render_board import draw_endgame_text, draw_game_board
from .ui.render_panels import draw_info_panels, get_ability_error_text
from .ui.ui_constants import ACCENT_GOLD, PANEL_BG


def _get_display_turn(game_state):
    """Calculate the chess-style turn number from the move log.

    In standard notation, White and Black share the same turn number
    (e.g. 1. e4 e5). Since Tempo Burst was removed, every entry in the 
    move log (standard move or ability) corresponds to exactly one half-turn.
    """
    total_actions = len(game_state.move_log)
    return (total_actions - 1) // 2 + 1 if total_actions > 0 else 1


def _log_move(message_log, game_state, move):
    """Push a FAN-formatted log entry after a successful move."""
    turn = _get_display_turn(game_state)
    is_white = not game_state.white_to_move  # Turn already switched after make_move

    fan_text = format_move_fan(move)

    # Determine color key based on move type
    fused = getattr(move, "fused_to_piece", None)
    if fused is not None:
        color_key = "highlight"
    elif move.piece_captured is not None:
        color_key = "primary"
    else:
        color_key = "normal"

    message_log.add_move(turn, is_white, fan_text, color_key)


def _log_ability(message_log, game_state, ability_key, source_square, target_square):
    """Push a FAN-formatted log entry after a successful ability use."""
    turn = _get_display_turn(game_state)
    # finish_ability_turn already switched the turn, so invert to get the user who acted
    is_white = not game_state.white_to_move
    from .abilities import get_ability
    ability = get_ability(ability_key)
    fan_text = format_ability_fan(ability, source_square, target_square)
    message_log.add_move(turn, is_white, fan_text, "ability")


def _log_events(message_log, game_state, logged_event_ids):
    """Log newly triggered event executions to the message log.

    Uses logged_event_ids (a set) to avoid duplicate entries.
    """
    turn = _get_display_turn(game_state)
    for event in game_state.event_manager.recently_executed_events:
        eid = id(event)
        exec_key = f"exec:{eid}"
        if exec_key not in logged_event_ids:
            message_log.add_event(turn, f"--- {event.name} ---", "highlight")
            for msg in getattr(event, "execution_messages", []):
                message_log.add_event(turn, msg, "normal")
            logged_event_ids.add(exec_key)


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
    """Try to resolve a pending promotion."""
    move = input_state.promotion_move_pending
    choice = resolve_promotion_click(mouse_pos, move=move)
    if choice is None:
        return False
    
    move.promotion_choice = choice
    game_state.make_move(move, choice, is_real_move=True)
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
    
    from .abilities.registry import get_ability
    ability = get_ability(ability_key)
    select_ability(input_state, ability_key, input_state.ability_menu_square, ability.requires_target)
    return True


def update_cursor(input_state, game_state, show_help, valid_moves, mouse_pos):
    """Update the mouse cursor to a pointing hand if hovering over interactable UI."""
    from .ui.input_handler import is_board_click, get_board_square, get_active_color
    
    if show_help and get_help_modal_close_rect().collidepoint(mouse_pos):
        p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
        return
    if not show_help and get_help_button_rect().collidepoint(mouse_pos):
        p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
        return
    if input_state.promotion_move_pending is not None:
        if resolve_promotion_click(mouse_pos, move=input_state.promotion_move_pending) is not None:
            p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
            return
    if input_state.ability_menu_square:
        piece = game_state.board.get_piece_at(*input_state.ability_menu_square)
        ability_keys = get_available_ability_keys(game_state, piece)
        menu_rect = get_ability_menu_rect(input_state.ability_menu_square)
        if resolve_ability_menu_click(mouse_pos, ability_keys, menu_rect) is not None:
            p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
            return

    if is_board_click(mouse_pos):
        row, col = get_board_square(mouse_pos)
        piece = game_state.board.get_piece_at(row, col)
        if piece is not None and piece.color == get_active_color(game_state):
            p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
            return
        if len(input_state.player_clicks) == 1:
            for move in valid_moves:
                if move.start_row == input_state.player_clicks[0][0] and move.start_col == input_state.player_clicks[0][1]:
                    if move.end_row == row and move.end_col == col:
                        p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
                        return

    p.mouse.set_cursor(p.SYSTEM_CURSOR_ARROW)


def main():
    """Run the main Pygame game loop."""
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    p.display.set_caption("Chess Fusion")
    clock = p.time.Clock()
    screen.fill(PANEL_BG)

    game_state = GameState()
    valid_moves = game_state.get_valid_moves()
    move_made = False

    images = load_images(image_loader=p.image.load, scaler=p.transform.scale)

    # Fonts — use Segoe UI for consistent Vietnamese character support
    fonts = {
        "title": p.font.SysFont("Segoe UI", 24, bold=True),
        "normal": p.font.SysFont("Segoe UI", 16, bold=True),
        "small": p.font.SysFont("Segoe UI", 13),
    }
    font_panel = fonts["normal"]

    message_log = MessageLog()
    input_state = InputState()
    logged_event_ids = set()  # Track which events have been logged to avoid duplicates
    show_help = False
    running = True

    while running:
        for event in p.event.get():
            if event.type == p.QUIT:
                running = False
            elif event.type == p.KEYDOWN:
                if event.key == p.K_h:
                    show_help = not show_help
            elif event.type == p.MOUSEBUTTONDOWN:
                mouse_pos = p.mouse.get_pos()

                # Help overlay interactions
                if show_help:
                    close_rect = get_help_modal_close_rect()
                    if close_rect.collidepoint(mouse_pos):
                        show_help = False
                    continue

                # Help button in sidebar
                help_btn = get_help_button_rect()
                if help_btn.collidepoint(mouse_pos):
                    show_help = True
                    continue

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
            elif event.type == p.MOUSEWHEEL:
                mouse_x, _ = p.mouse.get_pos()
                if mouse_x >= BOARD_WIDTH:
                    scroll_speed = 30
                    message_log.scroll(event.y * scroll_speed)

            if move_attempt_ready(input_state):
                prev_move_count = len(game_state.move_log)
                move_made = process_move_attempt(input_state, game_state, valid_moves) or move_made
                # Log the move if it was successfully applied
                if move_made and len(game_state.move_log) > prev_move_count:
                    last_move = game_state.move_log[-1]
                    if hasattr(last_move, "piece_moved"):
                        _log_move(message_log, game_state, last_move)

            if ability_attempt_ready(input_state):
                ability_key = input_state.selected_ability_key
                source_sq = input_state.ability_source_square
                target_sq = input_state.player_clicks[0]
                ability_succeeded = process_ability_attempt(input_state, game_state)
                if ability_succeeded:
                    _log_ability(message_log, game_state, ability_key, source_sq, target_sq)
                    move_made = True

        if move_made:
            _log_events(message_log, game_state, logged_event_ids)
            message_log.auto_scroll_to_bottom()
            valid_moves = game_state.get_valid_moves()
            move_made = False

        # --- Hover Cursor ---
        update_cursor(input_state, game_state, show_help, valid_moves, p.mouse.get_pos())

        # --- Rendering ---
        screen.fill(PANEL_BG)

        draw_game_board(
            screen,
            game_state,
            valid_moves,
            input_state.sq_selected,
            images,
            input_state.dragging,
            input_state.mouse_pos,
            fonts,
        )
        draw_info_panels(screen, game_state, images, font_panel)
        draw_message_log(screen, message_log, game_state, fonts)

        ability_error = get_ability_error_text(input_state)
        if ability_error:
            error_text = font_panel.render(ability_error, True, ACCENT_GOLD)
            screen.blit(error_text, (10, INFO_PANEL_HEIGHT + 10))

        if input_state.promotion_move_pending is not None:
            color = WHITE if game_state.white_to_move else BLACK
            move = input_state.promotion_move_pending
            menu_rect = get_promotion_menu_rect(move=move)
            draw_promotion_menu(screen, color, images, menu_rect)
        if input_state.ability_menu_square:
            piece = game_state.board.get_piece_at(input_state.ability_menu_square[0], input_state.ability_menu_square[1])
            draw_ability_menu(screen, font_panel, game_state, piece, input_state.ability_menu_square)

        if game_state.checkmate:
            winner = "Black" if game_state.white_to_move else "White"
            draw_endgame_text(screen, f"CHECKMATE! {winner} wins")
        elif game_state.stalemate:
            draw_endgame_text(screen, "STALEMATE!")

        if show_help:
            draw_help_overlay(screen, fonts)

        clock.tick(MAX_FPS)
        p.display.flip()


if __name__ == "__main__":
    main()
