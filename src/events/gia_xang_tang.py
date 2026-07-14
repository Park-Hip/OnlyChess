"""Gia Xang Tang event implementation."""


from ..constants import BOARD_COLS, BOARD_ROWS, CHANCELLOR_CODE, KNIGHT_CODE, ROOK_CODE, WARDEN_CODE
from ..pieces import create_piece
from .base import ChessEvent
from .registry import register_event


@register_event
class GiaXangTang(ChessEvent):
    """Transform all rooks on the board into knights."""

    event_key = "gia_xang_tang"

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Gia Xang Tang"
        self.warning_description = "GIA XANG TANG INCOMING! ALL ROOKS BECOME KNIGHTS."

    def execute(self):
        """Transform every rook into a knight while preserving piece state."""
        super().execute()
        transformed = False
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece and piece.get_piece_code() in (ROOK_CODE, CHANCELLOR_CODE, WARDEN_CODE):
                    new_knight = create_piece(KNIGHT_CODE, piece.color, (row, col))
                    new_knight.has_moved = piece.has_moved
                    self.gs.board.replace_piece_at(row, col, new_knight)
                    transformed = True
                    
        if transformed:
            self.execution_messages.append("(All) R=N")
        else:
            self.execution_messages.append("0x")

