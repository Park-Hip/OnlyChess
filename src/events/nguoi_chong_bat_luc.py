"""Nguoi Chong Bat Luc event implementation."""

import pygame as p

from ..constants import BOARD_COLS, BOARD_ROWS, KING_CODE
from .base import ChessEvent
from .registry import register_event


@register_event
class NguoiChongBatLuc(ChessEvent):
    """Immobilize both kings for one full turn."""

    event_key = "nguoi_chong_bat_luc"
    IMMOBILIZE_DURATION = 1

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Nguoi Chong Bat Luc"
        self.duration = self.IMMOBILIZE_DURATION
        self.immobilized_kings = []

    def _collect_kings(self):
        """Return every king currently on the board."""
        kings = []
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is not None and piece.get_piece_code() == KING_CODE:
                    kings.append(piece)
        return kings

    def _is_piece_on_board(self, target_piece):
        """Return whether a piece object is still present on the board."""
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if self.gs.board.get_piece_at(row, col) is target_piece:
                    return True
        return False

    def execute(self):
        """Prevent both kings from moving or castling."""
        super().execute()
        self.duration = self.IMMOBILIZE_DURATION
        self.immobilized_kings = self._collect_kings()
        for king in self.immobilized_kings:
            king.is_active = False
            king.immobilized_turns = self.duration

    def tick(self):
        """Reduce immobilize duration and restore kings when it expires."""
        if not self.immobilized_kings or self.duration == 0:
            return

        self.duration -= 1
        for king in self.immobilized_kings:
            if self._is_piece_on_board(king):
                king.immobilized_turns = self.duration

        if self.duration == 0:
            self.cleanup()

    def cleanup(self):
        """Restore king movement for kings still on the board."""
        for king in self.immobilized_kings:
            if self._is_piece_on_board(king):
                king.is_active = True
                king.immobilized_turns = 0

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw warning text before the event executes."""
        if self.warning_active:
            text = "WARNING: NGUOI CHONG BAT LUC INCOMING! BOTH KINGS WILL BE IMMOBILIZED."
            text_object = font.render(text, True, p.Color("red"))
            screen.blit(text_object, (10, info_panel_height + 10))
