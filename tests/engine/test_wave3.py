"""Core Wave 3 contracts: generic moves, actions, turn lifecycle, and undo."""

from pathlib import Path
import unittest

from src.engine.factory import build_state
from src.engine.pipeline import Pipeline
from src.engine.actions import Replace, SetStatus
from src.engine.piece import Piece, StatusDef, StatusInstance
from src.modding.loader import load

ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "wave3_mods"


class WaveThreeEngineTests(unittest.TestCase):
    def setUp(self):
        self.state = build_state(load(ROOT, enabled_mod_ids=("fixture:standard",)).registries, "fixture:standard")
        self.pipeline = Pipeline(self.state)

    def test_start_position_has_twenty_legal_moves(self):
        self.assertEqual(len(self.pipeline.legal_moves()), 20)

    def test_apply_and_undo_restore_the_starting_position(self):
        move = next(move for move in self.pipeline.legal_moves() if move.start == (6, 4) and move.end == (4, 4))
        self.pipeline.apply(move)
        self.pipeline.undo_last()
        self.assertEqual(self.state.current_side, "fixture:white")
        self.assertEqual(self.state.board.at((6, 4)).definition.id, "fixture:pawn")
        self.assertFalse(self.state.board.at((6, 4)).has_moved)

    def test_simulation_leaves_state_unchanged(self):
        move = self.pipeline.legal_moves()[0]
        self.pipeline.simulate(move)
        self.assertEqual(self.state.current_side, "fixture:white")
        self.assertEqual(self.state.board.at(move.start).uid, move.piece.uid)

    def test_replace_is_reversible(self):
        original = self.state.board.at((6, 0))
        replacement = Piece(999, original.definition, original.side, original.pos)
        action = Replace(original, replacement)
        action.apply(self.state)
        self.assertIs(self.state.board.at((6, 0)), replacement)
        action.undo(self.state)
        self.assertIs(self.state.board.at((6, 0)), original)

    def test_status_expiry_is_recorded_and_undone_with_the_turn(self):
        definition = StatusDef("fixture:waiting", "after_opponent_turn", {})
        piece = self.state.board.at((6, 0))
        SetStatus(piece, StatusInstance(definition, None)).apply(self.state)
        self.state.current_side = "fixture:black"

        self.pipeline.apply(self.pipeline.legal_moves()[0])
        self.assertNotIn("fixture:waiting", piece.statuses)
        self.pipeline.undo_last()
        self.assertIn("fixture:waiting", piece.statuses)


if __name__ == "__main__": unittest.main()
