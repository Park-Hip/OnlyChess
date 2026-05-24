"""Input-state helpers for board selection, dragging, and move attempts."""

from dataclasses import dataclass, field

from ..constants import BLACK, BOARD_HEIGHT, BOARD_SIZE, INFO_PANEL_HEIGHT, SQ_SIZE, WHITE


@dataclass
class InputState:
    """Track transient UI input state separate from game rules."""

    sq_selected: tuple = ()
    player_clicks: list = field(default_factory=list)
    promotion_move_pending: object | None = None
    dragging: bool = False
    mouse_pos: tuple = (0, 0)
    move_attempt_type: str = "click"
    click_type: str = "first_click"


def reset_selection_state(input_state):
    """Clear selection and dragging state after finishing an interaction."""
    input_state.sq_selected = ()
    input_state.player_clicks = []
    input_state.dragging = False
    input_state.move_attempt_type = "click"
    input_state.click_type = "first_click"


def set_promotion_pending(input_state, move):
    """Store the move awaiting a promotion choice."""
    input_state.promotion_move_pending = move


def clear_promotion_pending(input_state):
    """Clear the current promotion-pending workflow."""
    input_state.promotion_move_pending = None


def is_board_click(
    location,
    square_size=SQ_SIZE,
    info_panel_height=INFO_PANEL_HEIGHT,
    board_height=BOARD_HEIGHT,
    board_size=BOARD_SIZE,
):
    """Return whether a mouse click lands inside the playable board area."""
    board_width = board_size * square_size
    return (
        0 <= location[0] < board_width
        and info_panel_height <= location[1] < info_panel_height + board_height
    )


def get_board_square(location, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT):
    """Convert a mouse location into a board square."""
    col = location[0] // square_size
    row = (location[1] - info_panel_height) // square_size
    return row, col


def clamp_drag_square(location, square_size=SQ_SIZE, info_panel_height=INFO_PANEL_HEIGHT):
    """Clamp drag-release coordinates to the nearest board square."""
    end_col = max(0, min(BOARD_SIZE - 1, location[0] // square_size))
    end_row = max(0, min(BOARD_SIZE - 1, (location[1] - info_panel_height) // square_size))
    return end_row, end_col


def get_active_color(game_state):
    """Return the color string for the side whose turn it is."""
    return WHITE if game_state.white_to_move else BLACK


def handle_board_mouse_down(input_state, game_state, location):
    """Update selection state for a board mouse-down event."""
    input_state.mouse_pos = location
    if not is_board_click(location):
        return

    row, col = get_board_square(location)
    if input_state.sq_selected == (row, col):
        input_state.dragging = True
        input_state.click_type = "second_click"
        return

    piece = game_state.board.get_piece_at(row, col)
    if len(input_state.player_clicks) == 0:
        if piece is not None and piece.color == get_active_color(game_state):
            input_state.sq_selected = (row, col)
            input_state.player_clicks = [input_state.sq_selected]
            input_state.dragging = True
            input_state.click_type = "first_click"
        return

    if piece is not None and piece.color == get_active_color(game_state):
        input_state.sq_selected = (row, col)
        input_state.player_clicks = [input_state.sq_selected]
        input_state.dragging = True
        input_state.click_type = "first_click"
    else:
        input_state.sq_selected = (row, col)
        input_state.player_clicks.append(input_state.sq_selected)
        input_state.move_attempt_type = "click"


def handle_mouse_motion(input_state, location):
    """Track the latest mouse position for dragged-piece rendering."""
    input_state.mouse_pos = location


def handle_board_mouse_up(input_state, location):
    """Convert a drag-release into a move attempt when needed."""
    if input_state.promotion_move_pending is not None:
        return
    if not input_state.dragging or not input_state.player_clicks:
        return

    input_state.dragging = False
    end_square = clamp_drag_square(location)
    if end_square != input_state.player_clicks[0]:
        input_state.player_clicks.append(end_square)
        input_state.move_attempt_type = "drag"
    elif input_state.click_type == "second_click":
        reset_selection_state(input_state)


def move_attempt_ready(input_state):
    """Return whether the current input state contains a full move attempt."""
    return len(input_state.player_clicks) == 2


def retain_origin_after_invalid_drag(input_state):
    """Keep only the origin square selected after an invalid drag attempt."""
    input_state.sq_selected = input_state.player_clicks[0]
    input_state.player_clicks = [input_state.player_clicks[0]]


def resolve_invalid_click_selection(input_state, game_state):
    """Resolve selection state after an invalid click-based move attempt."""
    row, col = input_state.player_clicks[1]
    piece = game_state.board.get_piece_at(row, col)
    if piece is not None and piece.color == get_active_color(game_state):
        input_state.player_clicks = [(row, col)]
        input_state.sq_selected = (row, col)
        return
    reset_selection_state(input_state)
