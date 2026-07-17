"""Tests for the divergence list, and for the divergences we can already pin.

Two jobs. First, enforce migration-plan §4's cap, so the list cannot quietly
grow into an excuse generator. Second, nail the one divergence that is already
observable in the old engine — the castling bug — to a regression test, so that
when the new engine fixes it we can prove the fix rather than believe it.
"""

import unittest

from .adapters import OldEngine
from .divergences import CAP, DIVERGENCES, by_id
from .perft import POSITIONS, perft


class DivergenceListTests(unittest.TestCase):

    def test_the_list_is_capped(self):
        # migration-plan §4: "Cap it. Four entries are known. A fifth needs a
        # written argument." This test is where that argument gets demanded, so
        # the cap must have NO headroom — a cap that permits the next entry is
        # not a cap, and this assertion would then wave through the first case it
        # was written for.
        self.assertLessEqual(
            len(DIVERGENCES),
            CAP,
            f"\nThe divergence list has grown to {len(DIVERGENCES)}, past its cap of {CAP}."
            f"\nmigration-plan §4 names this exact failure mode: the list growing"
            f"\nuntil it explains every difference and the oracle stops meaning"
            f"\nanything. Adding one needs a written argument, not a shrug —"
            f"\nraise CAP deliberately, in a commit that says why.",
        )

    def test_the_cap_has_no_headroom(self):
        # Guards the guard. If CAP drifts above the real count, the test above
        # silently stops testing anything.
        self.assertEqual(
            CAP,
            len(DIVERGENCES),
            "CAP must equal the current number of divergences, or the next one "
            "lands without anyone arguing for it.",
        )

    def test_every_divergence_cites_a_source(self):
        # A divergence without a document behind it is an excuse.
        for divergence in DIVERGENCES:
            with self.subTest(divergence=divergence.id):
                self.assertTrue(divergence.source.strip())
                self.assertTrue(divergence.detection.strip())

    def test_ids_are_unique(self):
        ids = [d.id for d in DIVERGENCES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_lookup_rejects_unknown_ids(self):
        with self.assertRaises(KeyError):
            by_id("no_such_divergence")


class CastlingBugTests(unittest.TestCase):
    """The one divergence observable in the old engine today.

    migration-plan §1 claims: "the engine offers e1g1 while a black pawn on e2
    attacks f1". §6.3 decided to FIX it rather than preserve it, which makes it
    divergence `castling_through_attack`.

    The root cause is worth restating, because it is the finding that shapes the
    whole rebuild: `square_under_attack` asks *"does any enemy MOVE end here?"*
    when it should ask *"does any enemy piece THREATEN here?"*. For a pawn those
    differ in both directions — it moves forward without threatening, and
    threatens diagonally without being able to move there unless occupied. f1 is
    empty during castling, so the pawn generates no move to f1, so the square
    looks safe.
    """

    def setUp(self):
        self.engine = OldEngine()
        # White: Ke1, Rh1, kingside rights. Black: Ke8, pawn e2.
        # The pawn attacks d1 and f1 but NOT e1 — so white is not in check, and
        # castling kingside crosses f1, which is attacked.
        self.fen = "4k3/8/8/8/8/8/4p3/4K2R w K - 0 1"

    def test_the_bug_is_real_and_still_present(self):
        self.assertIn(
            "e1g1",
            self.engine.legal_moves(self.fen),
            "The old engine no longer offers e1g1 here. If someone fixed the "
            "castling bug in the old engine, divergence `castling_through_attack` "
            "is obsolete and should be removed from the list.",
        )

    def test_white_is_not_in_check_so_this_is_purely_about_the_transit_square(self):
        # Guards the fixture, not the engine: if white were in check, castling
        # would be illegal for an unrelated reason and the test above would pass
        # while proving nothing.
        moves = self.engine.legal_moves(self.fen)
        self.assertIn("e1d2", moves, "king should have quiet moves; it is not in check")
        self.assertIn("e1e2", moves, "the king can capture the e2 pawn, so it is not attacking e1")

    def test_the_new_engine_must_not_offer_it(self):
        # The assertion Wave 4 has to make pass. Skipped until there is a second
        # engine to make it — an xfail would rot silently into a pass.
        self.skipTest("no new engine yet — this is the Wave 4 gate for castling_through_attack")

    def test_perft_does_not_catch_this_and_that_is_why_the_list_exists(self):
        # Kiwipete is THE standard castling torture position and the old engine
        # matches it exactly at depth 3 (97862). The published suite simply does
        # not contain a pawn attacking a castling transit square, so ground truth
        # is necessary and NOT sufficient. A divergence needs its own position.
        fen, expected = POSITIONS["kiwipete"]
        self.assertEqual(perft(self.engine, fen, 2), expected[2])
        self.assertIn("e1g1", self.engine.legal_moves(self.fen))


class DivergenceMetadataTests(unittest.TestCase):

    def test_the_castling_divergence_is_recorded_against_wave_4(self):
        divergence = by_id("castling_through_attack")
        self.assertEqual(divergence.wave, 4)
        self.assertIn("§6.3", divergence.source)
