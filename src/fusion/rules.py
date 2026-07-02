"""Fusion pair lookup rules."""

from ..constants import (
    ARCHBISHOP_CODE,
    BISHOP_CODE,
    CHANCELLOR_CODE,
    INQUISITOR_CODE,
    KNIGHT_CODE,
    ROOK_CODE,
    WARDEN_CODE,
)


FUSION_RESULTS = {
    (KNIGHT_CODE, BISHOP_CODE): ARCHBISHOP_CODE,
    (BISHOP_CODE, KNIGHT_CODE): ARCHBISHOP_CODE,
    (ROOK_CODE, KNIGHT_CODE): CHANCELLOR_CODE,
    (KNIGHT_CODE, ROOK_CODE): CHANCELLOR_CODE,
    (ROOK_CODE, BISHOP_CODE): WARDEN_CODE,
    (BISHOP_CODE, ROOK_CODE): INQUISITOR_CODE,
}


def get_fusion_result(capturing_code, captured_code):
    """Return the fusion result for a capture pair, or None."""
    return FUSION_RESULTS.get((capturing_code, captured_code))
