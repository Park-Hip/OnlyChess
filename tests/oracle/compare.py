"""The differential comparison, and the positions to run it over.

This is the part migration-plan §0 calls worth more than the 182 tests:

    "generate 10,000 random positions and assert both engines produce the same
     move list" -- that test only exists while both engines do.
"""

import random
from dataclasses import dataclass

from .adapters import OldEngine
from .position import STARTING_FEN


@dataclass(frozen=True)
class Difference:
    """One position where two engines disagree about the move set."""

    fen: str
    only_in_a: frozenset
    only_in_b: frozenset

    def __str__(self):
        lines = [f"  {self.fen}"]
        if self.only_in_a:
            lines.append(f"    only in A: {sorted(self.only_in_a)}")
        if self.only_in_b:
            lines.append(f"    only in B: {sorted(self.only_in_b)}")
        return "\n".join(lines)


def compare(engine_a, engine_b, fens):
    """Return every position where the two engines' move sets differ.

    Collects rather than fails fast, for the same reason the loader does
    (loader-lifecycle: "a non-coder with six typos should not run the game six
    times"): one bug usually shows up in many positions, and the shape of the
    set is the diagnosis.
    """
    differences = []
    for fen in fens:
        moves_a = engine_a.legal_moves(fen)
        moves_b = engine_b.legal_moves(fen)
        if moves_a != moves_b:
            differences.append(
                Difference(fen, frozenset(moves_a - moves_b), frozenset(moves_b - moves_a))
            )
    return differences


def random_positions(count, seed=0, max_plies=40, engine=None):
    """Yield `count` FENs reached by random LEGAL PLAY from the start.

    **Legal play, not scattered pieces, and the distinction is load-bearing.**
    Random placement would manufacture positions no game can reach — a white pawn
    on rank 1, kings adjacent, a side in check on the opponent's turn — and the
    engines would then be compared on inputs neither is specified for. Worse, it
    would fire the `pawn_double_step` divergence artificially (see
    position.py), and the oracle would report a bug that is not one.

    Playing forward guarantees every position is legal and reachable, which is
    the population we actually care about being right on.
    """
    engine = engine or OldEngine()
    rng = random.Random(seed)
    produced = 0
    attempts = 0
    # A walk that ends in mate or stalemate is discarded, so `produced` can stall
    # while the loop spins. Bounded so that a pathological seed fails loudly
    # instead of hanging a test run with no output.
    budget = 10 * count + 20

    while produced < count:
        attempts += 1
        if attempts > budget:
            raise RuntimeError(
                f"random_positions(count={count}, seed={seed}, max_plies={max_plies}) "
                f"gave up after {attempts} attempts with only {produced} positions: "
                f"every walk ended in checkmate or stalemate before max_plies."
            )
        fen = STARTING_FEN
        for _ in range(rng.randint(1, max_plies)):
            moves = engine.legal_moves(fen)
            if not moves:  # checkmate or stalemate — discard and retry
                break
            fen = engine.apply(fen, rng.choice(sorted(moves)))
        else:
            yield fen
            produced += 1
