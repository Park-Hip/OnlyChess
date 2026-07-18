"""Presentation data derived from state rather than stored alongside it.

Each field below could have been kept as its own counter, updated on every move. Deriving them
instead means they cannot drift out of step with the state they describe, and undo needs to know
nothing about them — reversing the move reverses the readout for free.
"""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src.engine.actions import Relocate, Remove
from src.engine.move import Move
from src.runtime import ApplicationContext, EngineSession


class SnapshotFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = ApplicationContext.load()

    def session(self, mode_id="base:advanced"):
        return EngineSession(self.context.load_result, mode_id)

    def test_material_starts_level_and_totals_the_declared_values(self):
        snapshot = self.session().presentation_snapshot()

        totals = dict(snapshot.material)
        self.assertEqual(2, len(totals))
        # 8 pawns + 2 rooks + 2 knights + 2 bishops + a queen, with a king worth nothing.
        self.assertEqual({39}, set(totals.values()))

    def test_losing_a_piece_to_anything_lowers_that_sides_material(self):
        """Totalled from the board, so a piece removed by an event counts exactly like a capture."""
        session = self.session()
        victim = next(piece for piece in session.state.board.pieces() if piece.definition.id == "base:queen")
        before = dict(session.presentation_snapshot().material)[session.state.board.sides[victim.side].name]

        Remove(victim).apply(session.state)

        after = dict(session.presentation_snapshot().material)[session.state.board.sides[victim.side].name]
        self.assertEqual(before - 9, after)

    def test_a_fused_piece_keeps_the_capturers_worth_rather_than_summing(self):
        """Summing would count a capture twice: once as the loser's loss, once as the winner's
        gain. The difference between the two sides is the whole point of the readout."""
        session = self.session()
        rook, knight = session.state.board.at((7, 0)), session.state.board.at((0, 1))
        for piece in list(session.state.board.pieces()):
            if piece not in (rook, knight) and not piece.definition.royal:
                session.state.board.remove(piece.pos)
        session.pipeline.apply(Move(rook, rook.pos, knight.pos, [Remove(knight), Relocate(rook, knight.pos)], knight))

        fused = session.state.board.at((0, 1))
        self.assertEqual(("base:rook", "base:knight"), fused.definition.components)
        self.assertEqual(5, fused.definition.material)

    def test_last_move_is_absent_before_the_first_move_and_reverses_with_undo(self):
        session = self.session()
        self.assertIsNone(session.presentation_snapshot().last_move)

        move = session.legal_moves[0]
        session.move(move.start, move.end)
        self.assertEqual((move.start, move.end), session.presentation_snapshot().last_move)

        session.undo()
        self.assertIsNone(session.presentation_snapshot().last_move)

    def test_the_event_countdown_falls_as_moves_are_played(self):
        session = self.session()
        first = session.presentation_snapshot().event_countdown
        self.assertIsNotNone(first)

        move = session.legal_moves[0]
        session.move(move.start, move.end)

        self.assertEqual(first - 1, session.presentation_snapshot().event_countdown)

    def test_the_countdown_reverses_with_undo(self):
        session = self.session()
        before = session.presentation_snapshot().event_countdown
        move = session.legal_moves[0]
        session.move(move.start, move.end)

        session.undo()

        self.assertEqual(before, session.presentation_snapshot().event_countdown)

    def test_a_mode_with_no_pool_has_no_countdown(self):
        self.assertIsNone(self.session("base:vanilla").presentation_snapshot().event_countdown)


if __name__ == "__main__":
    unittest.main()
