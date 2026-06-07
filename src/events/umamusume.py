"""Umamusume event implementation."""

import pygame as p

from ..constants import BOARD_COLS, BOARD_ROWS, KING_CODE, KNIGHT_CODE
from ..pieces import create_piece
from .base import ChessEvent
from .registry import register_event


@register_event
class Umamusume(ChessEvent):
    """Transform all non-king pieces on the board into knights."""

    event_key = "umamusume"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Umamusume"

    def execute(self):
        """Replace every non-king piece with a knight of the same color."""
        super().execute()
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is None or piece.get_piece_code() == KING_CODE:
                    continue
                new_knight = create_piece(KNIGHT_CODE, piece.color, (row, col))
                new_knight.has_moved = piece.has_moved
                self.gs.board.replace_piece_at(row, col, new_knight)

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw warning text before the event executes."""
        if self.warning_active:
            text = "WARNING: UMAMUSUME INCOMING! ALL NON-KING PIECES BECOME KNIGHTS."
            text_object = font.render(text, True, p.Color("red"))
            screen.blit(text_object, (10, info_panel_height + 10))
