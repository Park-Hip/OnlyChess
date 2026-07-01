"""Tai Xiu event implementation."""

import random


from ..constants import BLACK, BOARD_COLS, BOARD_ROWS, KING_CODE, WHITE
from ..game.state_helpers import format_piece_fan
from .base import ChessEvent
from .registry import register_event


@register_event
class TaiXiu(ChessEvent):
    """Randomly remove one non-king piece from one side."""

    event_key = "tai_xiu"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Tai Xiu"
        self.warning_description = "TAI XIU INCOMING! ONE SIDE WILL LOSE A RANDOM PIECE."

    def _collect_eligible_piece_positions(self, target_color):
        """Return board positions of removable non-king pieces for the target side."""
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
                if getattr(piece, "is_shielded", False):
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
            self.execution_messages.append("0x")
            return
        row, col = random.choice(eligible_positions)
        piece = self.gs.board.get_piece_at(row, col)
        self.execution_messages.append(f"x{format_piece_fan(piece)}")
        self.gs.board.set_piece_at(row, col, None)

