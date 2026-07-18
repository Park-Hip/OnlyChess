"""Clocks: session-level, and deliberately outside the action log.

`CLAUDE.md` requires every state change to be an action with an inverse. A clock is the exception,
and the reason is a design decision rather than an oversight: undo reverses the log, so a clock
recorded there would refund the time spent on the move being taken back, and undo would become a way
to buy thinking time. Time is the one thing here that cannot be unmade.

The board, pieces, statuses, and resources remain fully action-driven. These tests pin the boundary.
"""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src.runtime import ApplicationContext, EngineSession


class ClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = ApplicationContext.load()

    def session(self, *, time_limit=None):
        return EngineSession(self.context.load_result, "base:vanilla", time_limit=time_limit)

    def test_a_mode_without_a_time_limit_has_no_clocks_and_ticking_is_inert(self):
        session = self.session()

        session.tick(10.0)

        self.assertEqual({}, session.clocks)
        self.assertIsNone(session.outcome)
        self.assertEqual((), session.presentation_snapshot().clocks)

    def test_time_is_charged_only_to_the_side_to_move(self):
        session = self.session(time_limit=60)
        mover = session.state.current_side

        session.tick(5.0)

        self.assertAlmostEqual(55.0, session.clocks[mover])
        for side, remaining in session.clocks.items():
            if side != mover:
                self.assertAlmostEqual(60.0, remaining)

    def test_the_charge_follows_the_turn(self):
        session = self.session(time_limit=60)
        first = session.state.current_side
        session.tick(5.0)

        move = session.legal_moves[0]
        session.move(move.start, move.end)
        second = session.state.current_side
        session.tick(4.0)

        self.assertNotEqual(first, second)
        self.assertAlmostEqual(55.0, session.clocks[first])
        self.assertAlmostEqual(56.0, session.clocks[second])

    def test_undo_does_not_refund_time(self):
        """The decision this whole design follows from."""
        session = self.session(time_limit=60)
        mover = session.state.current_side
        session.tick(5.0)
        move = session.legal_moves[0]
        session.move(move.start, move.end)
        session.tick(4.0)

        self.assertTrue(session.undo())

        self.assertAlmostEqual(55.0, session.clocks[mover])
        self.assertEqual([], session.state.action_log)

    def test_running_out_of_time_ends_the_game_naming_who_flagged(self):
        session = self.session(time_limit=3)
        mover = session.state.current_side
        expected = session.state.board.sides[mover].name

        session.tick(3.0)

        self.assertEqual(0.0, session.clocks[mover])
        self.assertEqual(f"{expected} ran out of time", session.outcome)
        self.assertIn("outcome_reached", [notice.kind for notice in session.drain_notifications()])

    def test_a_clock_never_goes_negative_and_stops_once_it_has_flagged(self):
        session = self.session(time_limit=2)
        mover = session.state.current_side

        session.tick(30.0)
        session.tick(30.0)

        self.assertEqual(0.0, session.clocks[mover])
        self.assertEqual(mover, session.flagged)

    def test_a_flag_beats_the_position(self):
        """Checked before legality: asking for legal moves first would report a player who simply
        ran out of time as stalemated."""
        session = self.session(time_limit=1)
        for piece in list(session.state.board.pieces()):
            if not piece.definition.royal:
                session.state.board.remove(piece.pos)

        session.tick(1.0)

        self.assertIn("ran out of time", session.outcome)

    def test_clocks_reach_presentation_as_side_name_and_seconds(self):
        session = self.session(time_limit=90)
        session.tick(15.0)

        clocks = dict(session.presentation_snapshot().clocks)

        self.assertEqual(len(session.state.board.sides), len(clocks))
        self.assertIn(75.0, clocks.values())


if __name__ == "__main__":
    unittest.main()
