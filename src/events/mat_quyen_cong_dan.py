"""Mat Quyen Cong Dan event implementation."""

import random

import pygame as p

from ..constants import BLACK, BOARD_COLS, BOARD_ROWS, PAWN_CODE, WHITE
from ..pieces import create_piece
from .base import ChessEvent
from .registry import register_event


@register_event
class MatQuyenCongDan(ChessEvent):
    """Remove one black pawn and transform one white pawn into a black pawn."""

    event_key = "mat_quyen_cong_dan"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Mat Quyen Cong Dan"

    def _collect_pawn_entries(self, target_color):
        """Return board entries for pawns that match the target color."""
        entries = []
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is None:
                    continue
                if piece.color != target_color:
                    continue
                if piece.get_piece_code() != PAWN_CODE:
                    continue
                entries.append((row, col, piece))
        return entries

    def _copy_pawn_state(self, source_piece, target_piece):
        """Preserve dynamic pawn state while keeping the new pawn identity."""
        preserved_attrs = {"color", "name", "pos", "id", "direction"}
        for attr, value in source_piece.__dict__.items():
            if attr in preserved_attrs:
                continue
            setattr(target_piece, attr, value)

    def execute(self):
        """Remove one black pawn and transform one white pawn into a black pawn."""
        super().execute()

        black_pawns = self._collect_pawn_entries(BLACK)
        if black_pawns:
            row, col, _ = random.choice(black_pawns)
            self.gs.board.set_piece_at(row, col, None)

        white_pawns = self._collect_pawn_entries(WHITE)
        if not white_pawns:
            return

        row, col, white_pawn = random.choice(white_pawns)
        transformed_pawn = create_piece(PAWN_CODE, BLACK, (row, col))
        self._copy_pawn_state(white_pawn, transformed_pawn)
        self.gs.board.replace_piece_at(row, col, transformed_pawn)

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw warning text before the event executes."""
        if self.warning_active:
            text = "WARNING: MAT QUYEN CONG DAN INCOMING! A BLACK PAWN WILL FALL AND A WHITE PAWN WILL SWITCH SIDES."
            text_object = font.render(text, True, p.Color("red"))
            screen.blit(text_object, (10, info_panel_height + 10))
