"""Long Toi Tan Nat Khi Nhan Ra Toi La Gay event implementation."""


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
        self.warning_description = "QUEEN PURGE INCOMING! ALL QUEENS WILL BE REMOVED."

    def execute(self):
        """Delete every queen currently on the board."""
        super().execute()
        queens_removed = False
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is not None and piece.get_piece_code() == QUEEN_CODE:
                    self.gs.board.set_piece_at(row, col, None)
                    queens_removed = True
        
        if queens_removed:
            self.execution_messages.append("x(All) Q")
        else:
            self.execution_messages.append("0x")

