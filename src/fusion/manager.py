"""Fusion capture resolution."""

from ..constants import MIN_FUSION_HALF_TURNS, TEMPO_BURST_KEY
from ..pieces import create_piece
from .rules import get_fusion_result


class FusionManager:
    """Apply capture-based fusion rules after real moves."""

    def __init__(self, game_state):
        self.gs = game_state

    def handle_move(self, move):
        """Apply fusion effects for a real standard capture when eligible."""
        if not self._can_attempt_fusion(move):
            return None

        capturing_piece = move.piece_moved
        captured_piece = move.piece_captured
        capturing_code = capturing_piece.get_piece_code()
        captured_code = getattr(captured_piece, "primary_component_code", captured_piece.get_piece_code())
        fusion_result = get_fusion_result(capturing_code, captured_code)
        if fusion_result is None:
            return None

        capturing_piece.has_fused = True
        if fusion_result == TEMPO_BURST_KEY:
            self._start_tempo_burst(capturing_piece)
            return fusion_result

        self._replace_with_fused_piece(move, fusion_result, capturing_code, captured_code)
        return fusion_result

    def _can_attempt_fusion(self, move):
        """Return whether a move meets basic fusion requirements."""
        if not getattr(move, "is_real_move", False):
            return False
        if move.piece_captured is None:
            return False
        if self.gs.get_half_turn_count() < MIN_FUSION_HALF_TURNS:
            return False
        return move.piece_moved.can_fuse()

    def _replace_with_fused_piece(self, move, fused_piece_code, capturing_code, captured_code):
        """Replace the capturing piece with the fused result."""
        fused_piece = create_piece(fused_piece_code, move.piece_moved.color, (move.end_row, move.end_col))
        fused_piece.has_moved = True
        fused_piece.fusion_components = [capturing_code, captured_code]
        fused_piece.primary_component_code = capturing_code
        self.gs.board.replace_piece_at(move.end_row, move.end_col, fused_piece)
        move.fused_to_piece = fused_piece

    def _start_tempo_burst(self, rook):
        """Grant one immediate extra move to the capturing rook."""
        self.gs.tempo_burst_state.start(rook)
