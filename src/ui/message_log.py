"""Message log data structure and sidebar rendering (chess.com-style grid)."""

import pygame as p

from ..constants import (
    BOARD_WIDTH,
    HEIGHT,
    INFO_PANEL_HEIGHT,
    LOG_PANEL_WIDTH,
    PAWN_CODE,
)
from .ui_constants import (
    ACCENT_GOLD,
    ACCENT_GREEN,
    ACCENT_RED,
    CARD_BG,
    SEPARATOR,
    SIDEBAR_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

MAX_LOG_ENTRIES = 100

# --- Piece code to SAN letter mapping ---
_PIECE_LETTER = {
    "p": "",     # Pawns have no letter prefix in SAN
    "N": "N",
    "B": "B",
    "R": "R",
    "Q": "Q",
    "K": "K",
}

# --- Layout constants ---
ROW_HEIGHT = 28
TURN_COL_WIDTH = 30
MOVE_COL_WIDTH = (LOG_PANEL_WIDTH - TURN_COL_WIDTH - 20) // 2  # ~100px each


def _wrap_text(text, font, max_width):
    """Wrap text into multiple lines that fit within max_width."""
    words = text.split(' ')
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines


class MessageLog:
    """Turn-based message log with chess.com-style grid structure.

    Each turn stores White and Black move texts plus optional event lines.
    """

    def __init__(self, max_entries=MAX_LOG_ENTRIES):
        self._turns = {}       # {turn_num: {"w": [...], "b": [...], "events": [...]}}
        self._turn_order = []  # Ordered list of turn numbers for rendering
        self._max_entries = max_entries
        self.scroll_y = 0
        self._force_scroll_to_bottom = False

    def add_move(self, turn, is_white, text, color_key="normal"):
        """Record a move for a specific turn and side."""
        self._ensure_turn(turn)
        side_key = "w" if is_white else "b"
        self._turns[turn][side_key].append((text, color_key))

    def add_event(self, turn, text, color_key="warning"):
        """Record a global event line after a specific turn."""
        self._ensure_turn(turn)
        self._turns[turn]["events"].append((text, color_key))

    def _ensure_turn(self, turn):
        """Create the turn entry if it doesn't exist yet."""
        if turn not in self._turns:
            self._turns[turn] = {"w": [], "b": [], "events": []}
            self._turn_order.append(turn)
            # Trim oldest turns if we exceed the cap
            while len(self._turn_order) > self._max_entries:
                oldest = self._turn_order.pop(0)
                del self._turns[oldest]

    def get_all_turns(self):
        """Return all turn numbers for rendering."""
        return self._turn_order

    def scroll(self, dy):
        """Scroll the log vertically by dy pixels."""
        self.scroll_y += dy
        self._force_scroll_to_bottom = False

    def auto_scroll_to_bottom(self):
        """Flag the log to jump to the newest items on the next render pass."""
        self._force_scroll_to_bottom = True

    def get_turn_data(self, turn):
        """Return the data dict for a specific turn."""
        return self._turns.get(turn, {"w": [], "b": [], "events": []})

    def clear(self):
        """Remove all entries."""
        self._turns.clear()
        self._turn_order.clear()


# --- Color mapping ---
_COLOR_MAP = {
    "normal": TEXT_SECONDARY,
    "highlight": ACCENT_GOLD,
    "primary": TEXT_PRIMARY,
    "warning": ACCENT_RED,
    "ability": ACCENT_GREEN,
}


def _get_color(color_key):
    """Return the pygame Color for a log color key."""
    return _COLOR_MAP.get(color_key, TEXT_SECONDARY)


# --- Row colors for alternating stripes ---
_ROW_COLOR_EVEN = SIDEBAR_BG
_ROW_COLOR_ODD = CARD_BG


def draw_message_log(screen, message_log, game_state, fonts):
    """Draw the right-side message log panel in a chess.com-style grid.

    Layout: [Turn#] [White Move] [Black Move]
    Each row has alternating background colors for readability.

    Args:
        screen: Pygame display surface.
        message_log: MessageLog instance.
        game_state: Current GameState (used for event warning info).
        fonts: dict with 'normal' and 'small' pygame Font objects.
    """
    font = fonts["normal"]
    small_font = fonts["small"]
    sidebar_x = BOARD_WIDTH
    bottom_y = HEIGHT - INFO_PANEL_HEIGHT

    # --- Background ---
    sidebar_rect = p.Rect(sidebar_x, INFO_PANEL_HEIGHT, LOG_PANEL_WIDTH, bottom_y - INFO_PANEL_HEIGHT)
    p.draw.rect(screen, SIDEBAR_BG, sidebar_rect)
    # Gold left border
    p.draw.line(screen, ACCENT_GOLD, (sidebar_x, INFO_PANEL_HEIGHT), (sidebar_x, bottom_y))

    # --- Header ---
    header_rect = p.Rect(sidebar_x, INFO_PANEL_HEIGHT, LOG_PANEL_WIDTH, 36)
    p.draw.rect(screen, CARD_BG, header_rect)
    p.draw.line(screen, SEPARATOR, (sidebar_x, INFO_PANEL_HEIGHT + 36),
                (sidebar_x + LOG_PANEL_WIDTH, INFO_PANEL_HEIGHT + 36))
    header_text = font.render("Moves", True, ACCENT_GOLD)
    screen.blit(header_text, (sidebar_x + 15, INFO_PANEL_HEIGHT + 8))

    # --- Event Warning Card ---
    content_start_y = INFO_PANEL_HEIGHT + 42
    event_mgr = game_state.event_manager
    queued = event_mgr.queued_event
    show_warning = queued is not None and getattr(queued, "warning_active", False)
    if show_warning:
        warning_name = queued.name
        warning_desc_text = getattr(queued, "warning_description", "")
        
        card_x = sidebar_x + 8
        card_y = content_start_y
        card_w = LOG_PANEL_WIDTH - 16
        
        # Calculate dynamic height
        wrapped_lines = _wrap_text(warning_desc_text, small_font, card_w - 24) if warning_desc_text else []
        card_h = 56 + (len(wrapped_lines) * 16)
        
        card_rect = p.Rect(card_x, card_y, card_w, card_h)
        p.draw.rect(screen, CARD_BG, card_rect, border_radius=6)
        p.draw.rect(screen, ACCENT_RED, card_rect, width=1, border_radius=6)
        # Red accent bar
        p.draw.rect(screen, ACCENT_RED, p.Rect(card_x, card_y, 4, card_h), border_radius=6)

        warn_title = small_font.render("EVENT WARNING", True, ACCENT_RED)
        screen.blit(warn_title, (card_x + 12, card_y + 6))
        
        warn_name_surf = small_font.render(warning_name, True, TEXT_PRIMARY)
        screen.blit(warn_name_surf, (card_x + 12, card_y + 22))
        
        turns_left = game_state.get_turns_to_next_event()
        warn_turns = small_font.render(f"in {turns_left} turn(s)", True, TEXT_SECONDARY)
        screen.blit(warn_turns, (card_x + 12, card_y + 38))
        
        desc_y = card_y + 54
        for line in wrapped_lines:
            line_surf = small_font.render(line, True, TEXT_SECONDARY)
            screen.blit(line_surf, (card_x + 12, desc_y))
            desc_y += 16

        content_start_y = card_y + card_h + 8

    # --- Column Headers ---
    col_header_y = content_start_y
    turn_x = sidebar_x + 8
    white_x = sidebar_x + TURN_COL_WIDTH + 10
    black_x = white_x + MOVE_COL_WIDTH + 5

    num_header = small_font.render("#", True, TEXT_SECONDARY)
    w_header = small_font.render("White", True, TEXT_SECONDARY)
    b_header = small_font.render("Black", True, TEXT_SECONDARY)
    screen.blit(num_header, (turn_x + 4, col_header_y))
    screen.blit(w_header, (white_x, col_header_y))
    screen.blit(b_header, (black_x, col_header_y))
    content_start_y = col_header_y + 20
    p.draw.line(screen, SEPARATOR, (sidebar_x + 8, content_start_y - 2),
                (sidebar_x + LOG_PANEL_WIDTH - 8, content_start_y - 2))

    # --- Move Rows ---
    help_button_top = bottom_y - 45
    available_height = help_button_top - content_start_y - 10

    all_turns = message_log.get_all_turns()
    total_rows = 0
    for turn in all_turns:
        turn_data = message_log.get_turn_data(turn)
        total_rows += 1
        if turn_data["events"]:
            total_rows += len(turn_data["events"])

    total_content_height = total_rows * ROW_HEIGHT
    max_scroll = max(0, total_content_height - available_height)

    if message_log._force_scroll_to_bottom:
        message_log.scroll_y = -max_scroll
        message_log._force_scroll_to_bottom = False

    # Clamp scroll
    if message_log.scroll_y > 0:
        message_log.scroll_y = 0
    elif message_log.scroll_y < -max_scroll:
        message_log.scroll_y = -max_scroll

    # Set clip rect for scrolling content
    clip_rect = p.Rect(sidebar_x, content_start_y, LOG_PANEL_WIDTH, available_height)
    screen.set_clip(clip_rect)

    y = content_start_y + message_log.scroll_y
    row_index = 0

    for turn in all_turns:
        turn_data = message_log.get_turn_data(turn)

        # Alternating row background
        row_bg = _ROW_COLOR_ODD if row_index % 2 == 1 else _ROW_COLOR_EVEN
        row_rect = p.Rect(sidebar_x + 4, y, LOG_PANEL_WIDTH - 8, ROW_HEIGHT)
        p.draw.rect(screen, row_bg, row_rect, border_radius=3)

        # Turn number
        turn_text = small_font.render(f"{turn}.", True, TEXT_SECONDARY)
        screen.blit(turn_text, (turn_x + 2, y + 6))

        # White move(s) — join multiple moves with comma (e.g. Tempo Burst)
        if turn_data["w"]:
            white_parts = []
            for text, color_key in turn_data["w"]:
                white_parts.append((text, color_key))
            # Render the first move text; if multiple, join with ", "
            combined_text = ", ".join(t for t, _ in white_parts)
            # Use the most "important" color
            best_color = _pick_best_color(white_parts)
            w_surf = small_font.render(combined_text, True, best_color)
            # Clip to column width
            screen.blit(w_surf, (white_x, y + 6), area=p.Rect(0, 0, MOVE_COL_WIDTH - 2, ROW_HEIGHT))

        # Black move(s)
        if turn_data["b"]:
            black_parts = []
            for text, color_key in turn_data["b"]:
                black_parts.append((text, color_key))
            combined_text = ", ".join(t for t, _ in black_parts)
            best_color = _pick_best_color(black_parts)
            b_surf = small_font.render(combined_text, True, best_color)
            screen.blit(b_surf, (black_x, y + 6), area=p.Rect(0, 0, MOVE_COL_WIDTH - 2, ROW_HEIGHT))

        y += ROW_HEIGHT
        row_index += 1

        # Event rows (full-width, centered)
        if turn_data["events"]:
            for event_text, event_color_key in turn_data["events"]:
                event_row_rect = p.Rect(sidebar_x + 4, y, LOG_PANEL_WIDTH - 8, ROW_HEIGHT)
                p.draw.rect(screen, CARD_BG, event_row_rect, border_radius=3)
                event_surf = small_font.render(event_text, True, _get_color(event_color_key))
                event_x = sidebar_x + (LOG_PANEL_WIDTH - event_surf.get_width()) // 2
                screen.blit(event_surf, (event_x, y + 6))
                y += ROW_HEIGHT
                row_index += 1

    # Clear clip rect so help button can draw
    screen.set_clip(None)

    # --- Help Button (pill at bottom of sidebar) ---
    help_rect = p.Rect(sidebar_x + (LOG_PANEL_WIDTH - 100) // 2, bottom_y - 45, 100, 30)
    p.draw.rect(screen, CARD_BG, help_rect, border_radius=8)
    p.draw.rect(screen, ACCENT_GOLD, help_rect, width=1, border_radius=8)
    help_text = small_font.render("Help [H]", True, ACCENT_GOLD)
    screen.blit(help_text, (help_rect.centerx - help_text.get_width() // 2,
                            help_rect.centery - help_text.get_height() // 2))


def _pick_best_color(parts):
    """Pick the most visually important color from a list of (text, color_key) pairs."""
    priority = {"warning": 0, "highlight": 1, "ability": 2, "primary": 3, "normal": 4}
    best_key = min(parts, key=lambda p: priority.get(p[1], 5))[1]
    return _get_color(best_key)


def get_help_button_rect():
    """Return the clickable rect for the sidebar help button."""
    sidebar_x = BOARD_WIDTH
    bottom_y = HEIGHT - INFO_PANEL_HEIGHT
    return p.Rect(sidebar_x + (LOG_PANEL_WIDTH - 100) // 2, bottom_y - 45, 100, 30)


# --- FAN (Fusion Algebraic Notation) Helpers ---

def format_move_fan(move):
    """Convert a Move object into compact Fusion Algebraic Notation.

    Examples:
        e4, Nf3, Bxc6, O-O, e8=Q, Rxd5=C (fusion)
    """
    piece = move.piece_moved
    piece_code = piece.get_piece_code()
    piece_letter = _PIECE_LETTER.get(piece_code, piece_code)

    # Castling
    if move.is_castle_move:
        if move.end_col - move.start_col == 2:
            return "O-O"
        return "O-O-O"

    dest = _square_name(move.end_row, move.end_col)
    is_capture = move.piece_captured is not None

    # Build the base notation
    if piece_code == PAWN_CODE:
        if is_capture:
            start_file = _col_to_file(move.start_col)
            text = f"{start_file}x{dest}"
        else:
            text = dest
    else:
        if is_capture:
            text = f"{piece_letter}x{dest}"
        else:
            text = f"{piece_letter}{dest}"

    # Pawn promotion
    if move.is_pawn_promotion:
        promo_piece = getattr(move, "promoted_to_piece", None)
        if promo_piece:
            promo_code = promo_piece.get_piece_code()
            text += f"={_PIECE_LETTER.get(promo_code, promo_code)}"
        else:
            text += "=Q"

    # Fusion result
    fused = getattr(move, "fused_to_piece", None)
    if fused is not None:
        fused_code = fused.get_piece_code()
        fused_letter = _PIECE_LETTER.get(fused_code, fused_code)
        text += f"={fused_letter}"

    return text


def format_ability_fan(ability, source_square, target_square):
    """Convert an ability use into compact FAN notation.

    Examples:
        ~Ne3<>c2 [-2AP], ~Bc4xa6 [-3AP], ~Rh1[] [-3AP], ~e2>>e5 [-1AP]
    """
    source_name = _square_name(source_square[0], source_square[1])
    target_name = _square_name(target_square[0], target_square[1])

    key = ability.ability_key
    cost_str = f"[-{ability.ap_cost}AP]"

    if key == "knight_swap":
        return f"~N{source_name}<>{target_name} {cost_str}"
    elif key == "bishop_snipe":
        return f"~B{source_name}x{target_name} {cost_str}"
    elif key == "rook_shield":
        return f"~R{source_name}[] {cost_str}"
    elif key == "pawn_sprint":
        return f"~{source_name}>>{target_name} {cost_str}"
    else:
        return f"~{ability.display_name} {cost_str}"


def _square_name(row, col):
    """Convert board coordinates to chess notation (e.g. (6, 4) -> 'e2')."""
    files = "abcdefgh"
    rank = 8 - row
    return f"{files[col]}{rank}"


def _col_to_file(col):
    """Convert a column index to a file letter."""
    return "abcdefgh"[col]
