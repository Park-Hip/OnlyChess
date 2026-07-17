"""Perft against published ground truth.

These are the only tests in the repo that check the engine against something
nobody here wrote. Everything else — the other 182 tests, and the differential
oracle until Wave 3 — ultimately grades our own homework.

Depth 3 costs ~17s across the suite, so it is gated behind ORACLE_SLOW=1:

    ORACLE_SLOW=1 python -m pytest tests/oracle

Depths 1 and 2 stay in the default suite. Depth 1 alone would be far too weak —
it never plays a move, so it cannot catch a broken `apply`, and `apply` is half
the adapter.
"""

import os
import unittest

from .adapters import OldEngine
from .perft import POSITIONS, perft, perft_divided

SLOW = os.environ.get("ORACLE_SLOW") == "1"


class PublishedPerftTests(unittest.TestCase):
    """The old engine vs https://www.chessprogramming.org/Perft_Results.

    A failure here is unambiguous: either the harness is lying about the position
    or the engine is wrong about chess. Both are worth stopping for.
    """

    def setUp(self):
        self.engine = OldEngine()

    def _check(self, name, depth):
        fen, expected = POSITIONS[name]
        got = perft(self.engine, fen, depth)
        self.assertEqual(
            got,
            expected[depth],
            f"\nperft({name}, depth={depth}) = {got}, published = {expected[depth]}"
            f"\n  {fen}"
            f"\n  Localise it with perft_divided() and diff against any reference"
            f"\n  engine's divided output — the first move whose count differs is"
            f"\n  the bug.",
        )

    def test_depth_1(self):
        for name in POSITIONS:
            with self.subTest(position=name):
                self._check(name, 1)

    def test_depth_2(self):
        for name in POSITIONS:
            with self.subTest(position=name):
                self._check(name, 2)

    @unittest.skipUnless(SLOW, "slow; set ORACLE_SLOW=1")
    def test_depth_3(self):
        for name in POSITIONS:
            with self.subTest(position=name):
                self._check(name, 3)

    @unittest.skipUnless(SLOW, "slow; set ORACLE_SLOW=1")
    def test_start_depth_4(self):
        self._check("start", 4)


class PromotionExpansionTests(unittest.TestCase):
    """The adapter must speak chess, not old-engine.

    The old engine emits ONE Move for a promotion and takes the piece as a
    parameter, so its raw move list has four fewer entries than chess does per
    promotion. If the adapter forwarded that, perft would undercount — quietly,
    and only in positions most tests never reach.
    """

    def setUp(self):
        self.engine = OldEngine()

    def test_a_promotion_yields_four_moves(self):
        # White pawn on a7, empty a8. Kings placed apart and out of the way.
        moves = self.engine.legal_moves("7k/P7/8/8/8/8/8/7K w - - 0 1")
        promotions = {m for m in moves if m.startswith("a7a8")}
        self.assertEqual(promotions, {"a7a8q", "a7a8r", "a7a8b", "a7a8n"})

    def test_each_promotion_choice_produces_a_different_position(self):
        fen = "7k/P7/8/8/8/8/8/7K w - - 0 1"
        results = {suffix: self.engine.apply(fen, f"a7a8{suffix}") for suffix in "qrbn"}
        self.assertEqual(len(set(results.values())), 4, f"choices collapsed: {results}")
        self.assertTrue(results["q"].startswith("Q6k"), results["q"])
        self.assertTrue(results["n"].startswith("N6k"), results["n"])

    def test_position4_depth_1_counts_promotions(self):
        # position4 has a white pawn on a7 that can promote four ways, plus a
        # capture-promotion. Published depth 1 is 6 — a collapsing engine says 3.
        fen, expected = POSITIONS["position4"]
        self.assertEqual(perft(self.engine, fen, 1), expected[1])


class DividedPerftTests(unittest.TestCase):
    """The debugging tool has to work on the day it is needed, not before."""

    def test_divided_sums_to_the_total(self):
        engine = OldEngine()
        fen, expected = POSITIONS["start"]
        divided = perft_divided(engine, fen, 2)
        self.assertEqual(sum(divided.values()), expected[2])
        self.assertEqual(len(divided), expected[1])
        # Every first move has exactly 20 replies from the start position.
        self.assertEqual(set(divided.values()), {20})
