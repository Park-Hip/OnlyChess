"""My Danh Iran event implementation."""

import random

import pygame as p

from ..constants import BOARD_COLS, BOARD_ROWS, SQ_SIZE
from .base import ChessEvent
from .registry import register_event


@register_event
class MyDanhIran(ChessEvent):
    """Destroy every piece inside a random 2x2 danger zone."""

    event_key = "my_danh_iran"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "My Danh Iran"
        self.warning_area = self._choose_warning_area()

    def _choose_warning_area(self):
        """Choose the top-left square of a valid 2x2 warning area."""
        row = random.randint(2, 5)
        col = random.randint(0, BOARD_COLS - 2)
        return (row, col)

    def _iter_warning_squares(self):
        """Yield every square covered by the 2x2 warning zone."""
        start_row, start_col = self.warning_area
        for row in range(start_row, start_row + 2):
            for col in range(start_col, start_col + 2):
                yield row, col

    def _is_piece_shielded(self, piece):
        """Return whether the piece should survive the strike."""
        return getattr(piece, "is_shielded", False)

    def execute(self):
        """Destroy every non-shielded piece inside the warning zone."""
        super().execute()
        for row, col in self._iter_warning_squares():
            piece = self.gs.board.get_piece_at(row, col)
            if piece is None:
                continue
            if self._is_piece_shielded(piece):
                continue
            self.gs.board.set_piece_at(row, col, None)

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw the warning banner and highlight the 2x2 danger zone."""
        if not self.warning_active:
            return

        text = "WARNING: MY DANH IRAN INCOMING! A RANDOM 2X2 ZONE WILL BE DESTROYED."
        text_object = font.render(text, True, p.Color("red"))
        screen.blit(text_object, (10, info_panel_height + 10))

        overlay = p.Surface((SQ_SIZE * 2, SQ_SIZE * 2))
        overlay.set_alpha(100)
        overlay.fill(p.Color("red"))
        row, col = self.warning_area
        screen.blit(overlay, (col * SQ_SIZE, row * SQ_SIZE + info_panel_height))
