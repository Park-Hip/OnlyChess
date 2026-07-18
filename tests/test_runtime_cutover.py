"""The public application session must use loaded mods and the new engine only."""

import unittest

from src.engine.actions import AdjustResource, Relocate, Remove
from src.engine.move import Move
from src.engine.piece import Piece
from src.runtime import ApplicationContext, EngineSession


class RuntimeCutoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = ApplicationContext.load()

    def session(self, mode_id="base:advanced"):
        return EngineSession(self.context.load_result, mode_id)

    def test_vanilla_session_loads_only_chess_and_can_apply_and_undo_a_move(self):
        session = self.session("base:vanilla")

        move = session.legal_moves[0]
        session.move(move.start, move.end)

        self.assertEqual(1, len(session.state.action_log))
        self.assertTrue(session.undo())
        self.assertEqual(0, len(session.state.action_log))

    def test_default_session_activates_the_mod_defined_advanced_mode(self):
        session = self.session()

        self.assertEqual(("base:chess", "proof:mod", "skeleton:demo", "base:events", "base:fusion"), session.loaded_mods)
        self.assertEqual(("base:main_pool",), session.state.active_pools)

    def test_session_exposes_loaded_abilities_without_a_legacy_registry(self):
        session = self.session("base:vanilla")

        self.assertIn("base:rook_shield", session.abilities_for((7, 0)))

    def test_runtime_session_applies_a_player_selected_promotion(self):
        session = self.session("base:vanilla")
        state = session.state
        for piece in list(state.board.pieces()):
            state.board.remove(piece.pos)
        pawn = Piece(1, state.piece_defs["base:pawn"], "base:white", (1, 0), has_moved=True)
        state.board.place(pawn, pawn.pos)
        state.board.place(Piece(2, state.piece_defs["base:king"], "base:white", (7, 4)), (7, 4))
        state.board.place(Piece(3, state.piece_defs["base:king"], "base:black", (0, 4)), (0, 4))

        session.move((1, 0), (0, 0), choice="base:queen")

        self.assertEqual("base:queen", state.board.at((0, 0)).definition.id)

    def test_runtime_session_uses_a_loaded_ability_and_records_undo(self):
        session = self.session("base:vanilla")
        grant = AdjustResource("base:white", "base:ap", 3)
        grant.apply(session.state)

        session.use_ability((7, 0), "base:rook_shield")

        self.assertIn("base:shield", session.state.board.at((6, 0)).statuses)
        self.assertTrue(session.undo())
        self.assertNotIn("base:shield", session.state.board.at((6, 0)).statuses)

    def test_runtime_session_fuses_a_capture_from_loaded_rules(self):
        session = self.session()
        state = session.state
        rook, knight = state.board.at((7, 0)), state.board.at((0, 1))
        for piece in list(state.board.pieces()):
            if piece not in (rook, knight):
                state.board.remove(piece.pos)
        session.pipeline.apply(Move(rook, rook.pos, knight.pos, [Remove(knight), Relocate(rook, knight.pos)], knight))

        self.assertEqual("base:chancellor", state.board.at((0, 1)).definition.id)

    def test_runtime_session_records_event_warning_then_execution_with_moves(self):
        session = self.session()
        for _ in range(9):
            move = session.legal_moves[0]
            session.move(move.start, move.end)
        pending = session.state.pending_events["base:main_pool"]

        move = session.legal_moves[0]
        session.move(move.start, move.end)

        self.assertNotIn("base:main_pool", session.state.pending_events)
        self.assertTrue(session.state.event_messages)
        session.undo()
        self.assertEqual(pending, session.state.pending_events["base:main_pool"])
