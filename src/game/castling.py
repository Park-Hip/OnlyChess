"""Helpers for castling state and king-specific castling control."""

from dataclasses import dataclass

from ..constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, ROOK_CODE, WHITE


@dataclass
class CastleRights:
    """Track castling availability for both sides."""

    wks: bool
    bks: bool
    wqs: bool
    bqs: bool


def create_initial_castle_rights():
    """Return the initial castling rights for a new game."""
    return CastleRights(True, True, True, True)


def copy_castle_rights(castle_rights):
    """Return a copy of the current castling rights."""
    return CastleRights(
        castle_rights.wks,
        castle_rights.bks,
        castle_rights.wqs,
        castle_rights.bqs,
    )


def restore_castle_rights_from_log(castle_rights_log):
    """Return the latest castling rights stored in the log."""
    return copy_castle_rights(castle_rights_log[-1])


def update_castle_rights_for_move(castle_rights, move):
    """Update castling rights after a move or rook capture."""
    moved_piece = move.piece_moved
    captured_piece = move.piece_captured

    if moved_piece.get_piece_code() == KING_CODE:
        if moved_piece.color == WHITE:
            castle_rights.wks = False
            castle_rights.wqs = False
        else:
            castle_rights.bks = False
            castle_rights.bqs = False
    elif moved_piece.get_piece_code() == ROOK_CODE:
        if moved_piece.color == WHITE:
            if move.start_row == BOARD_ROWS - 1:
                if move.start_col == 0:
                    castle_rights.wqs = False
                elif move.start_col == BOARD_COLS - 1:
                    castle_rights.wks = False
        else:
            if move.start_row == 0:
                if move.start_col == 0:
                    castle_rights.bqs = False
                elif move.start_col == BOARD_COLS - 1:
                    castle_rights.bks = False

    if captured_piece and captured_piece.get_piece_code() == ROOK_CODE:
        if captured_piece.color == WHITE:
            if move.end_row == BOARD_ROWS - 1:
                if move.end_col == 0:
                    castle_rights.wqs = False
                elif move.end_col == BOARD_COLS - 1:
                    castle_rights.wks = False
        else:
            if move.end_row == 0:
                if move.end_col == 0:
                    castle_rights.bqs = False
                elif move.end_col == BOARD_COLS - 1:
                    castle_rights.bks = False


def get_piece_moves(piece, game_state, include_castle=True):
    """Return moves while keeping castling control local to king logic."""
    if piece.get_piece_code() == KING_CODE:
        return piece.get_possible_moves(game_state, include_castle=include_castle)
    return piece.get_possible_moves(game_state)
