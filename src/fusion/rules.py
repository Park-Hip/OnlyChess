"""Fusion pair lookup rules."""

from ..constants import (
    ARCHBISHOP_CODE,
    BISHOP_CODE,
    CHANCELLOR_CODE,
    KNIGHT_CODE,
    ROOK_CODE,
    TEMPO_BURST_KEY,
)


FUSION_RESULTS = {
    (KNIGHT_CODE, BISHOP_CODE): ARCHBISHOP_CODE,
    (ROOK_CODE, KNIGHT_CODE): CHANCELLOR_CODE,
    (ROOK_CODE, BISHOP_CODE): TEMPO_BURST_KEY,
}


def get_fusion_result(capturing_code, captured_code):
    """Return the fusion result for a capture pair, or None."""
    return FUSION_RESULTS.get((capturing_code, captured_code))
