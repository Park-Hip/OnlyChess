"""Comeout event implementation."""

import random

import pygame as p

from ..constants import BOARD_COLS, BOARD_ROWS, PAWN_CODE, QUEEN_CODE
from ..pieces import create_piece
from .base import ChessEvent
from .registry import register_event


@register_event
class Comeout(ChessEvent):
    """Promote one random pawn on the board into a queen."""

    event_key = "comeout"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Comeout"

    def execute(self):
        """Transform a random pawn into a queen on the same square."""
        super().execute()
        pawn_positions = []
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is not None and piece.get_piece_code() == PAWN_CODE:
                    pawn_positions.append((row, col, piece))

        if not pawn_positions:
            return

        row, col, pawn = random.choice(pawn_positions)
        promoted_queen = create_piece(QUEEN_CODE, pawn.color, (row, col))
        promoted_queen.has_moved = pawn.has_moved
        self.gs.board.replace_piece_at(row, col, promoted_queen)

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw warning text before the event executes."""
        if self.warning_active:
            text = "WARNING: COMEOUT INCOMING! A RANDOM PAWN WILL BECOME A QUEEN."
            text_object = font.render(text, True, p.Color("red"))
            screen.blit(text_object, (10, info_panel_height + 10))
