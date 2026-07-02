"""Comeout event implementation."""

import random


from ..constants import BOARD_COLS, BOARD_ROWS, PAWN_CODE, QUEEN_CODE
from ..pieces import create_piece
from ..game.state_helpers import format_piece_fan, format_square
from .base import ChessEvent
from .registry import register_event


@register_event
class Comeout(ChessEvent):
    """Promote one random pawn on the board into a queen."""

    event_key = "comeout"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Comeout"
        self.warning_description = "COMEOUT INCOMING! A RANDOM PAWN WILL BECOME A QUEEN."

    def _copy_status_state(self, source_piece, target_piece):
        """Preserve dynamic status fields while changing the piece identity."""
        preserved_attrs = {"color", "name", "pos", "id", "direction"}
        for attr, value in source_piece.__dict__.items():
            if attr in preserved_attrs:
                continue
            setattr(target_piece, attr, value)

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
            self.execution_messages.append("0x")
            return

        row, col, pawn = random.choice(pawn_positions)
        self.execution_messages.append(f"{format_piece_fan(pawn)}@{format_square(row, col)}=Q")
        promoted_queen = create_piece(QUEEN_CODE, pawn.color, (row, col))
        self._copy_status_state(pawn, promoted_queen)
        self.gs.board.replace_piece_at(row, col, promoted_queen)

