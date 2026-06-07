"""Tai Xiu event implementation."""

import random

import pygame as p

from ..constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, WHITE
from .base import ChessEvent
from .registry import register_event


@register_event
class TaiXiu(ChessEvent):
    """Randomly remove one non-king piece from one side."""

    event_key = "tai_xiu"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Tai Xiu"

    def _collect_eligible_piece_positions(self, target_color):
        """Return board positions of non-king pieces for the target side."""
        positions = []
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is None:
                    continue
                if piece.color != target_color:
                    continue
                if piece.get_piece_code() == KING_CODE:
                    continue
                positions.append((row, col))
        return positions

    def execute(self):
        """Roll Tai/Xiu and remove one random eligible piece from the chosen side."""
        super().execute()
        outcome = random.choice(["tai", "xiu"])
        target_color = BLACK if outcome == "tai" else WHITE
        eligible_positions = self._collect_eligible_piece_positions(target_color)
        if not eligible_positions:
            return
        row, col = random.choice(eligible_positions)
        self.gs.board.set_piece_at(row, col, None)

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw warning text before the event executes."""
        if self.warning_active:
            text = "WARNING: TAI XIU INCOMING! ONE SIDE WILL LOSE A RANDOM PIECE."
            text_object = font.render(text, True, p.Color("red"))
            screen.blit(text_object, (10, info_panel_height + 10))
