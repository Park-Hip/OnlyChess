"""The engine-agnostic interface, and the old engine behind it.

This is the seam the whole strangler rests on. At Wave 3 the new engine arrives
as a second implementation of `EngineAdapter` and everything else here — the
comparison, perft, the divergence list — works unchanged. **Nothing above this
module may import from `src`**; if it does, the oracle has quietly become a test
of the old engine only.
"""

from src.constants import BISHOP_CODE, KNIGHT_CODE, QUEEN_CODE, ROOK_CODE

from .position import fen_from_game_state, game_state_from_fen

# UCI's promotion suffixes. The engine's own codes differ in case (and the pawn's
# differs entirely), so the two vocabularies are mapped explicitly rather than
# lowercased into each other.
PROMOTION_SUFFIX_TO_CODE = {
    "q": QUEEN_CODE,
    "r": ROOK_CODE,
    "b": BISHOP_CODE,
    "n": KNIGHT_CODE,
}


class EngineAdapter:
    """What the oracle needs from an engine. Two methods, deliberately.

    A move is a **UCI string** — `e2e4`, or `e7e8q` for a promotion. Engine move
    objects never cross this boundary: the old engine's `Move` and the new
    engine's list-of-actions have nothing in common, and a comparison written
    against either one is a comparison of representations rather than of chess.
    """

    name = "abstract"

    def legal_moves(self, fen):
        """Return the set of legal moves in `fen`, as UCI strings."""
        raise NotImplementedError

    def apply(self, fen, uci):
        """Return the FEN after playing `uci` in `fen`."""
        raise NotImplementedError


class OldEngine(EngineAdapter):
    """`src/game/board.py` behind the oracle's interface.

    **Promotions are expanded, and that is not a detail.** The old engine emits
    *one* `Move` for a promotion and takes the chosen piece as a parameter to
    `make_move` — so its move list is not the chess move set: `e7e8` is one entry
    where chess has four. Perft would silently undercount every promotion, which
    is exactly the sort of near-miss the oracle exists to catch rather than
    reproduce.

    Expanding here makes the adapter speak chess instead of speaking old-engine.
    It also happens to model what the spec already decided the *new* engine will
    do — `into: [base:queen, …]` + `choose: mover` (content-schemas finding 2) —
    so the two engines will meet at this interface rather than at a translation.
    """

    name = "old"

    def legal_moves(self, fen):
        state = game_state_from_fen(fen)
        moves = set()
        for move in state.get_valid_moves():
            uci = move.get_chess_notation()
            if move.is_pawn_promotion:
                moves.update(uci + suffix for suffix in PROMOTION_SUFFIX_TO_CODE)
            else:
                moves.add(uci)
        return moves

    def apply(self, fen, uci):
        state = game_state_from_fen(fen)
        move, choice = self._find_move(state, uci)
        # is_real_move stays False, and that default is load-bearing rather than
        # incidental: it is what keeps `run_post_move_systems` from firing. With
        # it True, a capture here would trigger FUSION mid-perft — replacing
        # pieces on the board — and every published count would break. The oracle
        # compares move mechanics; events and fusion get structural tests
        # instead (migration-plan §0).
        state.make_move(move, promotion_choice=choice, is_real_move=False)
        return fen_from_game_state(state)

    def _find_move(self, state, uci):
        """Resolve a UCI string back to the engine's own Move object."""
        squares, suffix = uci[:4], uci[4:]
        for move in state.get_valid_moves():
            if move.get_chess_notation() != squares:
                continue
            if move.is_pawn_promotion:
                if not suffix:
                    raise ValueError(f"{uci!r} is a promotion and needs a suffix")
                return move, PROMOTION_SUFFIX_TO_CODE[suffix]
            return move, QUEEN_CODE
        raise ValueError(f"{uci!r} is not legal in this position")
