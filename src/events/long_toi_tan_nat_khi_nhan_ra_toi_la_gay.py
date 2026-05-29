"""Long Toi Tan Nat Khi Nhan Ra Toi La Gay event implementation."""

import pygame as p

from ..constants import BOARD_COLS, BOARD_ROWS, QUEEN_CODE
from .base import ChessEvent
from .registry import register_event


@register_event
class LongToiTanNatKhiNhanRaToiLaGay(ChessEvent):
    """Remove all queens from the board for both players."""

    event_key = "long_toi_tan_nat_khi_nhan_ra_toi_la_gay"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Long Toi Tan Nat Khi Nhan Ra Toi La Gay"

    def execute(self):
        """Delete every queen currently on the board."""
        super().execute()
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is not None and piece.get_piece_code() == QUEEN_CODE:
                    self.gs.board.set_piece_at(row, col, None)

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw warning text before the event executes."""
        if self.warning_active:
            text = "WARNING: QUEEN PURGE INCOMING! ALL QUEENS WILL BE REMOVED."
            text_object = font.render(text, True, p.Color("red"))
            screen.blit(text_object, (10, info_panel_height + 10))
