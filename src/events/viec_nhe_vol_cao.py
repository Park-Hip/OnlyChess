"""Viec Nhe Vol Cao event implementation."""


from ..constants import BOARD_COLS, BOARD_ROWS, PAWN_CODE
from .base import ChessEvent
from .registry import register_event


@register_event
class ViecNheVolCao(ChessEvent):
    """Stun every pawn so they cannot move for two full turns."""

    event_key = "viec_nhe_vol_cao"
    STUN_DURATION = 2

    def __init__(self, game_state):
        super().__init__(game_state)
        self.name = "Viec Nhe Vol Cao"
        self.warning_description = "VIEC NHE VOL CAO INCOMING! ALL PAWNS WILL BE STUNNED."
        self.duration = self.STUN_DURATION
        self.stunned_pawns = []

    def _collect_pawns(self):
        """Return every pawn currently on the board."""
        pawns = []
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                piece = self.gs.board.get_piece_at(row, col)
                if piece is not None and piece.get_piece_code() == PAWN_CODE:
                    pawns.append(piece)
        return pawns

    def _is_piece_on_board(self, target_piece):
        """Return whether a piece object is still present on the board."""
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if self.gs.board.get_piece_at(row, col) is target_piece:
                    return True
        return False

    def execute(self):
        """Apply the stun status to every pawn on the board."""
        super().execute()
        self.duration = self.STUN_DURATION
        self.stunned_pawns = self._collect_pawns()
        for pawn in self.stunned_pawns:
            pawn.is_active = False
            pawn.stunned_turns = self.duration
            
        if self.stunned_pawns:
            self.execution_messages.append("[stun] (All) P")
        else:
            self.execution_messages.append("0x")

    def tick(self):
        """Reduce the stun duration and recover pawns when it expires."""
        if not self.stunned_pawns or self.duration == 0:
            return

        self.duration -= 1
        for pawn in self.stunned_pawns:
            if self._is_piece_on_board(pawn):
                pawn.stunned_turns = self.duration

        if self.duration == 0:
            self.cleanup()

    def cleanup(self):
        """Restore movement for stunned pawns that are still on the board."""
        for pawn in self.stunned_pawns:
            if self._is_piece_on_board(pawn):
                pawn.is_active = True
                pawn.stunned_turns = 0

