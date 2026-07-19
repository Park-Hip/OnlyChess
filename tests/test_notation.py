"""History is derived from the action log and named by content, never by chess.

Standard algebraic notation cannot be reused as written: `Nf3` assumes knights are called N and
pawns are called nothing, and both are facts about chess rather than about this engine. These tests
pin that the log reads correctly for base chess *and* for a mod whose pieces have no letters at all.
"""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src.engine.actions import AdjustResource
from src.engine.piece import Piece
from src.notation import square_name
from src.runtime import ApplicationContext, EngineSession


def glyph_of(session):
    """Resolve a piece id to the glyph its own content declared."""
    registry = session.load_result.registries.content["piece"]
    return lambda piece_id: registry.get(piece_id).value.tree.get("presentation", {}).get("glyph", "?")


class SquareNameTests(unittest.TestCase):
    def test_squares_are_lettered_and_numbered_from_the_boards_own_size(self):
        self.assertEqual("a8", square_name((0, 0), rows=8))
        self.assertEqual("h1", square_name((7, 7), rows=8))
        # A 6-row board numbers its own ranks rather than borrowing chess's eight.
        self.assertEqual("a6", square_name((0, 0), rows=6))
        self.assertEqual("c1", square_name((5, 2), rows=6))


class HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = ApplicationContext.load()

    def session(self, mode_id="base:advanced"):
        return EngineSession(self.context.load_result, mode_id)

    def entries(self, session):
        return session.presentation_snapshot(glyph=glyph_of(session)).history

    def history(self, session):
        """Just the readable text, which is what most of these assertions are about."""
        return tuple(text for _, text, _ in self.entries(session))

    def test_a_move_reads_as_glyph_origin_destination(self):
        session = self.session()
        session.move((6, 4), (4, 4))

        self.assertEqual(("Pe2-e4",), self.history(session))

    def test_a_capture_is_marked_with_x(self):
        session = self.session()
        for start, end in (((6, 4), (4, 4)), ((1, 3), (3, 3)), ((4, 4), (3, 3))):
            session.move(start, end)

        self.assertEqual("Pe4xd5", self.history(session)[-1])

    def test_castling_is_recognised_by_shape_not_by_name(self):
        """Two pieces relocating in one move is castling in any game that has such a thing, so a
        mod's own two-piece move reads correctly without core knowing it exists."""
        session = self.session()
        for piece in list(session.state.board.pieces()):
            if piece.definition.id not in ("base:king", "base:rook"):
                session.state.board.remove(piece.pos)

        session.move((7, 4), (7, 6))

        self.assertIn("(castle)", self.history(session)[-1])

    def test_a_promotion_names_the_piece_chosen(self):
        session = self.session()
        state = session.state
        for piece in list(state.board.pieces()):
            if not piece.definition.royal:
                state.board.remove(piece.pos)
        state.board.place(Piece(99, state.piece_defs["base:pawn"], "base:white", (1, 0)), (1, 0))

        session.move((1, 0), (0, 0), choice="base:queen")

        self.assertEqual("Pa7-a8=Q", self.history(session)[-1])

    def test_an_ability_reads_as_owner_verb_target_and_cost(self):
        """The operator comes from the effect verb, which is engine vocabulary, so a mod's ability
        is written correctly without core learning its name."""
        session = self.session()
        AdjustResource("base:white", "base:ap", 3).apply(session.state)

        session.use_ability((7, 1), "base:knight_swap", target=(7, 0))

        self.assertEqual("~Nb1<>a1 [-2AP]", self.history(session)[-1])

    def test_an_ability_is_recorded_where_it_began_not_where_it_ended(self):
        """Pawn sprint moves its own owner. Read after the actions were applied, the log said the
        pawn started on the square it had just arrived at."""
        session = self.session()
        AdjustResource("base:white", "base:ap", 3).apply(session.state)

        session.use_ability((6, 0), "base:pawn_sprint", target=(3, 0))

        self.assertEqual("~Pa2>>a5 [-1AP]", self.history(session)[-1])

    def test_an_ability_acting_only_on_itself_needs_no_target(self):
        """`~Ra1[]a1` says the same thing twice; the operator alone already means "on itself"."""
        session = self.session()
        AdjustResource("base:white", "base:ap", 3).apply(session.state)
        for piece in list(session.state.board.pieces()):
            if piece.pos != (7, 0) and not piece.definition.royal:
                session.state.board.remove(piece.pos)

        session.use_ability((7, 0), "base:rook_shield")

        self.assertEqual("~Ra1[] [-3AP]", self.history(session)[-1])

    def test_an_ability_reaching_several_squares_reports_how_many(self):
        session = self.session()
        AdjustResource("base:white", "base:ap", 3).apply(session.state)
        state = session.state
        for piece in list(state.board.pieces()):
            if not piece.definition.royal:
                state.board.remove(piece.pos)
        state.board.place(Piece(90, state.piece_defs["base:pawn"], "base:white", (4, 4)), (4, 4))
        for index, square in enumerate(((3, 3), (3, 4), (5, 5))):
            state.board.place(Piece(91 + index, state.piece_defs["base:knight"], "base:black", square), square)

        session.use_ability((4, 4), "base:pawn_kamikaze")

        self.assertEqual("~Pe4x3 [-3AP]", self.history(session)[-1])

    def test_undo_shortens_the_history(self):
        """Derived from the log, so it needs no separate bookkeeping to stay in step."""
        session = self.session()
        session.move((6, 4), (4, 4))
        session.move((1, 3), (3, 3))
        self.assertEqual(2, len(self.history(session)))

        session.undo()

        self.assertEqual(1, len(self.history(session)))

    def test_a_mods_pieces_are_named_by_their_own_glyphs(self):
        """The proof mod's piece is `◆`, which no chess notation could have produced."""
        session = self.session("proof:arena_mode")
        move = session.legal_moves[0]

        session.move(move.start, move.end)

        self.assertTrue(self.history(session)[-1].startswith("◆"), self.history(session))


    def test_each_entry_carries_the_side_that_made_it(self):
        """A move list is read in columns, one player each, so the log has to say whose move it is."""
        session = self.session()
        session.move((6, 4), (4, 4))
        session.move((1, 3), (3, 3))

        sides = [side for side, _, _ in self.entries(session)]

        self.assertEqual(2, len(set(sides)), sides)
        self.assertEqual(session.state.board.sides.__iter__().__next__(), sides[0])

    def test_messages_travel_with_the_action_that_produced_them(self):
        """An event belongs between the moves it happened between, not in a separate list with no
        ordering against them."""
        session = self.session()
        for _ in range(9):
            move = session.legal_moves[0]
            session.move(move.start, move.end)

        with_messages = [messages for _, _, messages in self.entries(session) if messages]

        self.assertTrue(with_messages, "the ninth move warns of an event and should carry its text")


if __name__ == "__main__":
    unittest.main()
