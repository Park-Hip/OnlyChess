"""Gia Xang Tang event implementation."""

import pygame as p

from ..constants import BOARD_COLS, BOARD_ROWS, CHANCELLOR_CODE, KNIGHT_CODE, ROOK_CODE
from ..pieces import create_piece
from .base import ChessEvent
from .registry import register_event


@register_event
class GiaXangTang(ChessEvent):
    """Transform all rooks on the board into knights."""

    event_key = "gia_xang_tang"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Gia Xang Tang"

    def execute(self):
        """Transform every rook into a knight while preserving piece state."""
        super().execute()
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece and piece.get_piece_code() in (ROOK_CODE, CHANCELLOR_CODE):
                    new_knight = create_piece(KNIGHT_CODE, piece.color, (row, col))
                    new_knight.has_moved = piece.has_moved
                    self.gs.board.replace_piece_at(row, col, new_knight)

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw the warning banner before the event resolves."""
        if self.warning_active:
            text = "WARNING: GIA XANG TANG INCOMING! ALL ROOKS BECOME KNIGHTS."
            text_object = font.render(text, True, p.Color("red"))
            screen.blit(text_object, (10, info_panel_height + 10))
