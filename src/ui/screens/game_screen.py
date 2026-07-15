"""Screen that runs one full Chess Fusion game session."""

import pygame as p

from ...abilities import use_ability
from ...constants import BLACK, BOARD_HEIGHT, BOARD_WIDTH, INFO_PANEL_HEIGHT, WHITE
from ...game.board import GameState
from ...game.move import Move
from ..ability_menu import (
    draw_ability_menu,
    get_ability_menu_rect,
    get_available_ability_keys,
    resolve_ability_menu_click,
)
from ..audio import move_sound_key
from ..help_overlay import draw_help_overlay, get_help_modal_close_rect
from ..input_handler import (
    InputState,
    ability_attempt_ready,
    clear_ability_state,
    clear_promotion_pending,
    get_active_color,
    get_board_square,
    handle_board_mouse_down,
    handle_board_mouse_up,
    handle_mouse_motion,
    is_board_click,
    move_attempt_ready,
    reset_selection_state,
    resolve_invalid_click_selection,
    retain_origin_after_invalid_drag,
    select_ability,
    set_promotion_pending,
)
from ..message_log import MessageLog, draw_message_log, format_ability_fan, format_move_fan, get_help_button_rect
from ..promotion_menu import draw_promotion_menu, get_promotion_menu_rect, resolve_promotion_click
from ..render_board import draw_endgame_text, draw_game_board
from ..render_panels import draw_info_panels, get_ability_error_text
from ..ui_constants import ACCENT_GOLD, CARD_BG, PANEL_BG, TEXT_PRIMARY
from .base import Screen

MOUSE_WHEEL_SCROLL_SPEED = 30

RESTART_BUTTON_LABEL = "Restart"
MAIN_MENU_BUTTON_LABEL = "Main Menu"
QUIT_BUTTON_LABEL = "Quit"

GAME_OVER_BUTTON_WIDTH = 140
GAME_OVER_BUTTON_HEIGHT = 44
GAME_OVER_BUTTON_SPACING = 16
GAME_OVER_BUTTON_BORDER_RADIUS = 8
GAME_OVER_BUTTON_BORDER_WIDTH = 2
GAME_OVER_BUTTONS_OFFSET_Y = 50  # below the centered endgame text


class GameScreen(Screen):
    """Runs the board, panels, message log, promotion, and ability flow.

    This screen owns everything that used to live in the single main()
    game loop: per-frame state, event handling, move and ability
    resolution, and rendering. Behavior is unchanged from before the
    Screen refactor.
    """

    def __init__(self, shared):
        super().__init__()
        self.shared = shared
        self.fonts = shared.fonts
        self.font_panel = shared.fonts["normal"]
        self.images = shared.images
        self.sound_player = shared.sound_player

        self.game_state = GameState()
        self.valid_moves = self.game_state.get_valid_moves()
        self.message_log = MessageLog()
        self.input_state = InputState()
        self.logged_event_ids = set()
        self.show_help = False
        self.move_made = False

        (
            self.restart_button_rect,
            self.main_menu_button_rect,
            self.quit_button_rect,
        ) = self._build_game_over_button_rects()

    @staticmethod
    def _build_game_over_button_rects():
        """Lay out the Restart / Main Menu / Quit buttons in a centered row."""
        total_width = 3 * GAME_OVER_BUTTON_WIDTH + 2 * GAME_OVER_BUTTON_SPACING
        row_center_y = INFO_PANEL_HEIGHT + BOARD_HEIGHT // 2 + GAME_OVER_BUTTONS_OFFSET_Y
        left_x = BOARD_WIDTH // 2 - total_width // 2

        rects = []
        for index in range(3):
            rect = p.Rect(0, 0, GAME_OVER_BUTTON_WIDTH, GAME_OVER_BUTTON_HEIGHT)
            rect.left = left_x + index * (GAME_OVER_BUTTON_WIDTH + GAME_OVER_BUTTON_SPACING)
            rect.centery = row_center_y
            rects.append(rect)
        return rects

    def _is_game_over(self):
        """Whether the current game has ended in checkmate, stalemate, or timeout."""
        return self.game_state.checkmate or self.game_state.stalemate or self.game_state.timeout

    # ---- event handling ----

    def handle_event(self, event):
        """Handle one pygame event and resolve any ready move or ability."""
        if self._is_game_over():
            if event.type == p.MOUSEBUTTONDOWN:
                self._handle_game_over_click(p.mouse.get_pos())
            return

        if event.type == p.KEYDOWN:
            if event.key == p.K_h:
                self.show_help = not self.show_help
        elif event.type == p.MOUSEBUTTONDOWN:
            if self._handle_mouse_down(p.mouse.get_pos(), event.button):
                return
        elif event.type == p.MOUSEMOTION:
            handle_mouse_motion(self.input_state, p.mouse.get_pos())
        elif event.type == p.MOUSEBUTTONUP:
            handle_board_mouse_up(self.input_state, p.mouse.get_pos())
        elif event.type == p.MOUSEWHEEL:
            mouse_x, _ = p.mouse.get_pos()
            if mouse_x >= BOARD_WIDTH:
                self.message_log.scroll(event.y * MOUSE_WHEEL_SCROLL_SPEED)

        if move_attempt_ready(self.input_state):
            self._process_move_attempt()
        if ability_attempt_ready(self.input_state):
            self._process_ability_attempt()

    def _handle_mouse_down(self, mouse_pos, button):
        """Route a mouse-down click. Returns True if fully consumed here."""
        if self.show_help:
            if get_help_modal_close_rect().collidepoint(mouse_pos):
                self.show_help = False
            return True

        if get_help_button_rect().collidepoint(mouse_pos):
            self.show_help = True
            return True

        if self.input_state.promotion_move_pending is not None:
            self.move_made = self._handle_promotion_click(mouse_pos) or self.move_made
            return True
        if self.input_state.ability_menu_square:
            self._handle_ability_menu_click(mouse_pos)
            return True

        handle_board_mouse_down(self.input_state, self.game_state, mouse_pos, button)
        return False

    def _handle_game_over_click(self, mouse_pos):
        """Resolve a click on the game-over overlay buttons."""
        if self.restart_button_rect.collidepoint(mouse_pos):
            self.next_screen = GameScreen(self.shared)
        elif self.main_menu_button_rect.collidepoint(mouse_pos):
            from .menu_screen import MenuScreen

            self.next_screen = MenuScreen(self.shared)
        elif self.quit_button_rect.collidepoint(mouse_pos):
            self.should_quit = True

    # ---- move and ability resolution ----

    def _try_resolve_move(self):
        """Try to resolve the current UI move attempt against valid moves."""
        move = Move(self.input_state.player_clicks[0], self.input_state.player_clicks[1], self.game_state.board.grid)
        for valid_move in self.valid_moves:
            if move != valid_move:
                continue
            if valid_move.is_pawn_promotion:
                set_promotion_pending(self.input_state, valid_move)
                return True

            self.game_state.make_move(valid_move, is_real_move=True)
            self.sound_player.play(move_sound_key(valid_move))
            reset_selection_state(self.input_state)
            return True

        if self.input_state.promotion_move_pending is None:
            if self.input_state.move_attempt_type == "drag":
                retain_origin_after_invalid_drag(self.input_state)
            else:
                resolve_invalid_click_selection(self.input_state, self.game_state)
        return False

    def _process_move_attempt(self):
        """Resolve a ready move attempt and log it if it succeeded."""
        prev_move_count = len(self.game_state.move_log)
        made = self._try_resolve_move()
        self.move_made = made or self.move_made
        if made and len(self.game_state.move_log) > prev_move_count:
            last_move = self.game_state.move_log[-1]
            if hasattr(last_move, "piece_moved"):
                self._log_move(last_move)

    def _handle_promotion_click(self, mouse_pos):
        """Try to resolve a pending promotion."""
        move = self.input_state.promotion_move_pending
        choice = resolve_promotion_click(mouse_pos, move=move)
        if choice is None:
            return False

        move.promotion_choice = choice
        self.game_state.make_move(move, choice, is_real_move=True)
        self.sound_player.play(move_sound_key(move))
        clear_promotion_pending(self.input_state)
        reset_selection_state(self.input_state)
        return True

    def _try_resolve_ability(self):
        """Try to execute the selected ability against the chosen target."""
        target_square = self.input_state.player_clicks[0]
        succeeded = use_ability(
            self.input_state.selected_ability_key,
            self.game_state,
            self.input_state.ability_source_square,
            target_square,
        )
        if succeeded:
            clear_ability_state(self.input_state)
            reset_selection_state(self.input_state)
            return True
        self.input_state.ability_error = "Invalid ability target"
        self.input_state.player_clicks = []
        return False

    def _process_ability_attempt(self):
        """Resolve a ready ability attempt and log it if it succeeded."""
        ability_key = self.input_state.selected_ability_key
        source_square = self.input_state.ability_source_square
        target_square = self.input_state.player_clicks[0]
        succeeded = self._try_resolve_ability()
        if succeeded:
            self._log_ability(ability_key, source_square, target_square)
            self.move_made = True

    def _handle_ability_menu_click(self, mouse_pos):
        """Resolve a click inside an open ability menu."""
        square = self.input_state.ability_menu_square
        if not square:
            return False
        piece = self.game_state.board.get_piece_at(square[0], square[1])
        ability_keys = get_available_ability_keys(self.game_state, piece)
        menu_rect = get_ability_menu_rect(square)
        ability_key = resolve_ability_menu_click(mouse_pos, ability_keys, menu_rect)
        if ability_key is None:
            clear_ability_state(self.input_state)
            return False

        from ...abilities.registry import get_ability

        ability = get_ability(ability_key)
        select_ability(self.input_state, ability_key, square, ability.requires_target)
        return True

    # ---- per-frame update ----

    def update(self, dt):
        """Refresh valid moves and message log after a move, update cursor."""
        if self.move_made:
            self._log_events()
            self.message_log.auto_scroll_to_bottom()
            self.valid_moves = self.game_state.get_valid_moves()
            self.move_made = False

        if not self.show_help and self.input_state.promotion_move_pending is None:
            self.game_state.update_timer(dt)

        self._update_cursor(p.mouse.get_pos())

    def _update_cursor(self, mouse_pos):
        """Show a pointing hand cursor when hovering interactable UI."""
        if self.show_help and get_help_modal_close_rect().collidepoint(mouse_pos):
            p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
            return
        if not self.show_help and get_help_button_rect().collidepoint(mouse_pos):
            p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
            return
        if self.input_state.promotion_move_pending is not None:
            if resolve_promotion_click(mouse_pos, move=self.input_state.promotion_move_pending) is not None:
                p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
                return
        if self.input_state.ability_menu_square:
            piece = self.game_state.board.get_piece_at(*self.input_state.ability_menu_square)
            ability_keys = get_available_ability_keys(self.game_state, piece)
            menu_rect = get_ability_menu_rect(self.input_state.ability_menu_square)
            if resolve_ability_menu_click(mouse_pos, ability_keys, menu_rect) is not None:
                p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
                return

        if is_board_click(mouse_pos):
            row, col = get_board_square(mouse_pos)
            piece = self.game_state.board.get_piece_at(row, col)
            if piece is not None and piece.color == get_active_color(self.game_state):
                p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
                return
            if len(self.input_state.player_clicks) == 1:
                for move in self.valid_moves:
                    if move.start_row == self.input_state.player_clicks[0][0] and move.start_col == self.input_state.player_clicks[0][1]:
                        if move.end_row == row and move.end_col == col:
                            p.mouse.set_cursor(p.SYSTEM_CURSOR_HAND)
                            return

        p.mouse.set_cursor(p.SYSTEM_CURSOR_ARROW)

    # ---- message log ----

    def _get_display_turn(self):
        """Calculate the chess-style turn number from the move log.

        In standard notation, White and Black share the same turn number
        (e.g. 1. e4 e5). Since Tempo Burst was removed, every entry in the
        move log (standard move or ability) corresponds to exactly one half-turn.
        """
        total_actions = len(self.game_state.move_log)
        return (total_actions - 1) // 2 + 1 if total_actions > 0 else 1

    def _log_move(self, move):
        """Push a FAN-formatted log entry after a successful move."""
        turn = self._get_display_turn()
        is_white = not self.game_state.white_to_move  # Turn already switched after make_move

        fan_text = format_move_fan(move)

        fused = getattr(move, "fused_to_piece", None)
        if fused is not None:
            color_key = "highlight"
        elif move.piece_captured is not None:
            color_key = "primary"
        else:
            color_key = "normal"

        self.message_log.add_move(turn, is_white, fan_text, color_key)

    def _log_ability(self, ability_key, source_square, target_square):
        """Push a FAN-formatted log entry after a successful ability use."""
        turn = self._get_display_turn()
        is_white = not self.game_state.white_to_move

        from ...abilities import get_ability

        ability = get_ability(ability_key)
        fan_text = format_ability_fan(ability, source_square, target_square)
        self.message_log.add_move(turn, is_white, fan_text, "ability")

    def _log_events(self):
        """Log newly triggered event executions to the message log.

        Uses logged_event_ids (a set) to avoid duplicate entries.
        """
        turn = self._get_display_turn()
        for event in self.game_state.event_manager.recently_executed_events:
            eid = id(event)
            exec_key = f"exec:{eid}"
            if exec_key not in self.logged_event_ids:
                self.message_log.add_event(turn, f"--- {event.name} ---", "highlight")
                for msg in getattr(event, "execution_messages", []):
                    self.message_log.add_event(turn, msg, "normal")
                self.logged_event_ids.add(exec_key)

    # ---- rendering ----

    def draw(self, surface):
        """Draw the board, panels, message log, menus, and overlays."""
        surface.fill(PANEL_BG)

        draw_game_board(
            surface,
            self.game_state,
            self.valid_moves,
            self.input_state.sq_selected,
            self.images,
            self.input_state.dragging,
            self.input_state.mouse_pos,
            self.fonts,
        )
        draw_info_panels(surface, self.game_state, self.images, self.font_panel)
        draw_message_log(surface, self.message_log, self.game_state, self.fonts)

        ability_error = get_ability_error_text(self.input_state)
        if ability_error:
            error_text = self.font_panel.render(ability_error, True, ACCENT_GOLD)
            surface.blit(error_text, (10, INFO_PANEL_HEIGHT + 10))

        if self.input_state.promotion_move_pending is not None:
            color = WHITE if self.game_state.white_to_move else BLACK
            move = self.input_state.promotion_move_pending
            menu_rect = get_promotion_menu_rect(move=move)
            draw_promotion_menu(surface, color, self.images, menu_rect)
        if self.input_state.ability_menu_square:
            piece = self.game_state.board.get_piece_at(
                self.input_state.ability_menu_square[0], self.input_state.ability_menu_square[1]
            )
            draw_ability_menu(surface, self.font_panel, self.game_state, piece, self.input_state.ability_menu_square)

        if self.game_state.checkmate:
            winner = "Black" if self.game_state.white_to_move else "White"
            draw_endgame_text(surface, f"CHECKMATE! {winner} wins")
            self._draw_game_over_buttons(surface)
        elif self.game_state.stalemate:
            draw_endgame_text(surface, "STALEMATE!")
            self._draw_game_over_buttons(surface)
        elif self.game_state.timeout:
            winner = "Black" if self.game_state.white_to_move else "White"
            draw_endgame_text(surface, f"TIMEOUT! {winner} wins")
            self._draw_game_over_buttons(surface)

        if self.show_help:
            draw_help_overlay(surface, self.fonts)

    def _draw_game_over_buttons(self, surface):
        """Draw the Restart / Main Menu / Quit buttons below the endgame text."""
        button_font = self.fonts["normal"]
        buttons = (
            (self.restart_button_rect, RESTART_BUTTON_LABEL),
            (self.main_menu_button_rect, MAIN_MENU_BUTTON_LABEL),
            (self.quit_button_rect, QUIT_BUTTON_LABEL),
        )
        for rect, label in buttons:
            p.draw.rect(surface, CARD_BG, rect, border_radius=GAME_OVER_BUTTON_BORDER_RADIUS)
            p.draw.rect(
                surface,
                ACCENT_GOLD,
                rect,
                width=GAME_OVER_BUTTON_BORDER_WIDTH,
                border_radius=GAME_OVER_BUTTON_BORDER_RADIUS,
            )
            text_surface = button_font.render(label, True, TEXT_PRIMARY)
            text_rect = text_surface.get_rect(center=rect.center)
            surface.blit(text_surface, text_rect)
