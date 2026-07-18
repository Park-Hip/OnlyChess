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

    def test_captures_are_credited_to_the_taker_and_reverse_with_undo(self):
        """The one piece of presentation data that is stored rather than derived: a board cannot
        say whether a missing piece was captured or destroyed, and only the capture path knows."""
        session = self.session()
        for start, end in (((6, 4), (4, 4)), ((1, 3), (3, 3))):
            session.move(start, end)
        taker = session.state.current_side

        session.move((4, 4), (3, 3))

        credited = dict(session.presentation_snapshot().captures)[session.state.board.sides[taker].name]
        self.assertEqual(("base:pawn",), credited)

        session.undo()

        self.assertEqual((), dict(session.presentation_snapshot().captures)[session.state.board.sides[taker].name])

    def test_a_piece_destroyed_by_an_event_is_not_credited_as_a_capture(self):
        session = self.session()
        victim = next(piece for piece in session.state.board.pieces() if piece.definition.id == "base:queen")

        Remove(victim).apply(session.state)

        self.assertEqual({()}, {taken for _, taken in session.presentation_snapshot().captures})

    def test_a_warned_event_names_itself_and_the_squares_it_committed_to(self):
        """A zone bound at warning time is a promise those squares will be hit, so it can be shown
        and the player can move out of the way — the only reason a warning phase exists."""
        session = self.session()
        session.state.pending_events["base:main_pool"] = "base:my_danh_iran"
        session.state.pending_bindings["base:main_pool"] = {"zone": (3, 2, 2, 2)}

        warning = session.presentation_snapshot().warning

        self.assertIsNotNone(warning)
        self.assertEqual(((3, 2), (3, 3), (4, 2), (4, 3)), warning.squares)

    def test_an_event_that_picks_at_execution_promises_no_squares(self):
        """Most events select their victims when they fire. Naming the event without pointing at a
        square is the honest answer; a guessed rectangle would be worse than none."""
        session = self.session()
        session.state.pending_events["base:main_pool"] = "base:umamusume"
        session.state.pending_bindings["base:main_pool"] = {}

        warning = session.presentation_snapshot().warning

        self.assertEqual((), warning.squares)
        self.assertTrue(warning.name)

    def test_nothing_is_warned_before_a_pool_announces_anything(self):
        self.assertIsNone(self.session().presentation_snapshot().warning)

    def test_a_mode_with_no_pool_has_no_countdown(self):
        self.assertIsNone(self.session("base:vanilla").presentation_snapshot().event_countdown)


if __name__ == "__main__":
    unittest.main()
