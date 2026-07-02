"""Kho Ga Tron Ba Mia event implementation."""

import random


from ..constants import (
    ARCHBISHOP_CODE,
    BISHOP_CODE,
    BLACK,
    BOARD_COLS,
    BOARD_ROWS,
    CHANCELLOR_CODE,
    KNIGHT_CODE,
    ROOK_CODE,
    WHITE,
)
from ..game.state_helpers import format_piece_fan, format_square
from .base import ChessEvent
from .registry import register_event


@register_event
class KhoGaTronBaMia(ChessEvent):
    """Poison one rook, knight, or bishop for each side."""

    event_key = "kho_ga_tron_ba_mia"
    POISON_DURATION = 3
    ELIGIBLE_CODES = (ROOK_CODE, KNIGHT_CODE, BISHOP_CODE, ARCHBISHOP_CODE, CHANCELLOR_CODE)

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Kho Ga Tron Ba Mia"
        self.warning_description = "KHO GA TRON BA MIA INCOMING! SOME PIECES WILL BE POISONED."
        self.duration = self.POISON_DURATION
        self.poisoned_pieces = []

    def _collect_eligible_pieces(self, target_color):
        """Return pieces that can be poisoned for one side."""
        pieces = []
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is None:
                    continue
                if piece.color != target_color:
                    continue
                if piece.get_piece_code() in self.ELIGIBLE_CODES:
                    pieces.append(piece)
        return pieces

    def _is_piece_on_board(self, target_piece):
        """Return whether a piece object is still present on the board."""
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if self.gs.board.get_piece_at(row, col) is target_piece:
                    return True
        return False

    def execute(self):
        """Poison one eligible piece for each player if available."""
        super().execute()
        self.duration = self.POISON_DURATION
        self.poisoned_pieces = []
        poisoned_msgs = []
        for color in (WHITE, BLACK):
            eligible_pieces = self._collect_eligible_pieces(color)
            if not eligible_pieces:
                continue
            piece = random.choice(eligible_pieces)
            piece.poisoned_turns = self.duration
            self.poisoned_pieces.append(piece)
            poisoned_msgs.append(f"[poi] {format_piece_fan(piece)}@{format_square(*piece.pos)}")
        if poisoned_msgs:
            self.execution_messages.append(", ".join(poisoned_msgs))
        else:
            self.execution_messages.append("0x")

    def tick(self):
        """Reduce poison duration and clear it when it expires."""
        if not self.poisoned_pieces or self.duration == 0:
            return

        self.duration -= 1
        for piece in self.poisoned_pieces:
            if self._is_piece_on_board(piece):
                piece.poisoned_turns = self.duration

        if self.duration == 0:
            self.cleanup()

    def cleanup(self):
        """Clear poison from affected pieces that are still on the board."""
        for piece in self.poisoned_pieces:
            if self._is_piece_on_board(piece):
                piece.poisoned_turns = 0

