"""The differential comparison — the harness the strangler rests on.

**These tests are tautological today, and that is the point of building them
now.** Both sides are the old engine, so they cannot fail for a chess reason.
What they prove is that the *plumbing* works: the comparison, the position
generator, and the adapter interface are exercised end to end while the answer is
known, so that at Wave 3 the only new variable is the new engine.

What stops this from being self-congratulatory is `test_perft.py`, which checks
the same adapter against ground truth from outside the project. The two are a
pair: perft says the harness is honest, this says the harness is wired up.
"""

import os
import unittest

from .adapters import OldEngine
from .compare import compare, random_positions
from .perft import POSITIONS
from .position import STARTING_FEN

SLOW = os.environ.get("ORACLE_SLOW") == "1"


class ComparisonTests(unittest.TestCase):
    """The comparison itself, checked against engines that are known to differ.

    A comparison that has never reported a difference is not known to be able to.
    Old-vs-old can never demonstrate that, so the detection tests below use a
    deliberately broken adapter — the cheapest possible stand-in for a wrong new
    engine.
    """

    def test_identical_engines_agree_everywhere(self):
        fens = [fen for fen, _ in POSITIONS.values()]
        self.assertEqual(compare(OldEngine(), OldEngine(), fens), [])

    def test_a_difference_is_reported_with_both_sides(self):
        class DropsCastling(OldEngine):
            """Stands in for a new engine that forgot to register `castle`."""

            name = "broken"

            def legal_moves(self, fen):
                return {m for m in super().legal_moves(fen) if m not in ("e1g1", "e1c1")}

        fen, _ = POSITIONS["kiwipete"]
        differences = compare(OldEngine(), DropsCastling(), [fen])

        self.assertEqual(len(differences), 1)
        self.assertEqual(differences[0].only_in_a, frozenset({"e1g1", "e1c1"}))
        self.assertEqual(differences[0].only_in_b, frozenset())
        self.assertIn("only in A", str(differences[0]))

    def test_differences_are_collected_not_failed_fast(self):
        class DropsOneMove(OldEngine):
            """Differs in every position that has a move — so two in, two out."""

            def legal_moves(self, fen):
                moves = super().legal_moves(fen)
                return moves - {min(moves)} if moves else moves

        fens = [STARTING_FEN, POSITIONS["kiwipete"][0]]
        differences = compare(OldEngine(), DropsOneMove(), fens)
        self.assertEqual(len(differences), 2, "both positions should be reported, not just the first")
        self.assertEqual([d.fen for d in differences], fens)


class RandomPositionTests(unittest.TestCase):

    def test_positions_are_reachable_by_legal_play(self):
        # Every generated position must be one the old engine can stand in and
        # answer from. Scattered-piece generation could not promise this.
        engine = OldEngine()
        for fen in random_positions(5, seed=1, max_plies=10):
            with self.subTest(fen=fen):
                self.assertIsInstance(engine.legal_moves(fen), set)

    def test_generation_is_deterministic_for_a_seed(self):
        # A failing oracle run must be reproducible from its seed alone,
        # otherwise the report is a story rather than a bug.
        first = list(random_positions(5, seed=7, max_plies=10))
        second = list(random_positions(5, seed=7, max_plies=10))
        self.assertEqual(first, second)

    def test_different_seeds_explore_different_positions(self):
        a = list(random_positions(5, seed=1, max_plies=10))
        b = list(random_positions(5, seed=2, max_plies=10))
        self.assertNotEqual(a, b)


class DifferentialSweepTests(unittest.TestCase):
    """The real thing, at the size it will run at from Wave 3.

    migration-plan §0 wants 10,000 positions. That is a Wave 3 number — against
    the old engine alone it costs minutes to prove an identity. The default runs
    a handful to keep the suite honest and fast; ORACLE_SLOW=1 runs a real sweep.
    """

    def test_sweep(self):
        count = 300 if SLOW else 8
        fens = list(random_positions(count, seed=0, max_plies=30 if SLOW else 12))
        differences = compare(OldEngine(), OldEngine(), fens)
        self.assertEqual(
            differences,
            [],
            "\n".join(str(d) for d in differences[:5]),
        )
