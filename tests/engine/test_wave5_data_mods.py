"""Structural proofs that fusion and event data run through generic mechanisms."""

from pathlib import Path
import unittest

from src.engine.actions import Relocate, Remove
from src.engine.events import EventRunner
from src.engine.factory import build_state
from src.engine.move import Move
from src.engine.pipeline import Pipeline
from src.modding.loader import load


ROOT = Path(__file__).resolve().parents[2]


class WaveFiveDataModTests(unittest.TestCase):
    def setUp(self):
        result = load(ROOT / "mods", enabled_mod_ids=("base:chess", "base:fusion", "base:events"))
        result.raise_if_failed()
        self.state = build_state(result.registries, "base:advanced")

    def test_a_displacing_capture_composes_the_captured_pieces_components(self):
        rook = self.state.board.at((7, 0))
        knight = self.state.board.at((0, 1))
        for piece in list(self.state.board.pieces()):
            if piece not in (rook, knight): self.state.board.remove(piece.pos)
        move = Move(rook, rook.pos, knight.pos, [Remove(knight), Relocate(rook, knight.pos)], knight)
        Pipeline(self.state).apply(move)

        fused = self.state.board.at((0, 1))
        self.assertEqual(fused.definition.components, ("base:rook", "base:knight"))
        # Identity follows the capturer: the absorbed piece contributes vocabulary, not a new name.
        self.assertEqual(fused.definition.id, "base:rook")
        self.assertEqual(
            {part["type"] for part in fused.definition.moves},
            {part["type"] for part in self.state.piece_defs["base:rook"].moves}
            | {part["type"] for part in self.state.piece_defs["base:knight"].moves},
        )

    def test_event_transform_is_a_reversible_action_list(self):
        runner = EventRunner(self.state, seed=1)
        actions = runner.execute("base:gia_xang_tang")
        for action in actions: action.apply(self.state)
        self.assertTrue(all(piece.definition.id == "base:knight" for piece in self.state.board.pieces() if piece.definition.components[0] == "base:rook"))
        for action in reversed(actions): action.undo(self.state)
        self.assertEqual(self.state.board.at((7, 0)).definition.id, "base:rook")

    def test_pool_warns_then_executes_the_same_recorded_event(self):
        runner = EventRunner(self.state, seed=3)
        for _ in range(8):
            _, _, actions = runner.advance_pool("base:main_pool")
            for action in actions: action.apply(self.state)
        phase, event_id, actions = runner.advance_pool("base:main_pool")
        for action in actions: action.apply(self.state)
        self.assertEqual(phase, "warning")
        self.assertEqual(self.state.pending_events["base:main_pool"], event_id)
        self.assertTrue(self.state.event_messages)
        phase, executed, actions = runner.advance_pool("base:main_pool")
        self.assertEqual(phase, "execute")
        self.assertEqual(executed, event_id)
        for action in actions: action.apply(self.state)
        self.assertNotIn("base:main_pool", self.state.pending_events)

    def test_warning_binding_limits_a_zone_scoped_event(self):
        runner = EventRunner(self.state, seed=2)
        bindings = {"zone": (5, 0, 2, 2)}
        row, col, height, width = bindings["zone"]
        actions = runner.execute("base:my_danh_iran", bindings)
        self.assertTrue(actions)
        piece_actions = [action for action in actions if hasattr(action, "piece")]
        self.assertTrue(all(row <= action.piece.pos[0] < row + height and col <= action.piece.pos[1] < col + width for action in piece_actions))

    def test_event_move_and_swap_effects_are_reversible(self):
        first = self.state.board.at((7, 0)); second = self.state.board.at((7, 1))
        runner = EventRunner(self.state)
        move = runner._effect({"type": "move", "to": [5, 0]}, [first])[0]
        move.apply(self.state); self.assertIs(self.state.board.at((5, 0)), first); move.undo(self.state)
        swap = runner._effect({"type": "swap"}, [first, second])[0]
        swap.apply(self.state); self.assertIs(self.state.board.at((7, 0)), second); swap.undo(self.state)

    def test_pipeline_records_pool_schedule_with_its_moves(self):
        pipeline = Pipeline(self.state)
        for _ in range(9):
            pipeline.apply(pipeline.legal_moves()[0])
        self.assertIn("base:main_pool", self.state.pending_events)
        self.assertEqual(self.state.pool_turns["base:main_pool"], 9)
        pipeline.undo_last()
        self.assertNotIn("base:main_pool", self.state.pending_events)
        self.assertEqual(self.state.pool_turns["base:main_pool"], 8)

    def test_pipeline_executes_and_undoes_the_pending_event(self):
        pipeline = Pipeline(self.state)
        for _ in range(9):
            pipeline.apply(pipeline.legal_moves()[0])
        pending = self.state.pending_events["base:main_pool"]
        warning_messages = list(self.state.event_messages)
        pipeline.apply(pipeline.legal_moves()[0])
        self.assertNotIn("base:main_pool", self.state.pending_events)
        self.assertEqual(self.state.pool_turns["base:main_pool"], 10)
        pipeline.undo_last()
        self.assertEqual(self.state.pending_events["base:main_pool"], pending)
        self.assertEqual(self.state.event_messages, warning_messages)

    def test_every_shipped_event_produces_reversible_actions(self):
        runner = EventRunner(self.state, seed=4)
        for event_id, event in self.state.event_defs.items():
            with self.subTest(event=event_id):
                bindings = runner._bind(event.get("warning", {}).get("bind", {}))
                actions = runner.execute(event_id, bindings)
                for action in actions: action.apply(self.state)
                for action in reversed(actions): action.undo(self.state)


if __name__ == "__main__":
    unittest.main()
