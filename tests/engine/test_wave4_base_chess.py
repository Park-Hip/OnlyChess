"""Wave 4's base mod is consumed by generic engine capabilities."""

from pathlib import Path
import unittest

from src.engine.actions import AdjustResource
from src.engine.factory import build_state
from src.engine.pipeline import Pipeline
from src.modding.loader import load


ROOT = Path(__file__).resolve().parents[2]


class BaseChessAbilityTests(unittest.TestCase):
    def setUp(self):
        result = load(ROOT / "mods", enabled_mod_ids=("base:chess",), validate=True, link=True)
        result.raise_if_failed()
        self.state = build_state(result.registries, "base:vanilla")
        self.pipeline = Pipeline(self.state)

    def test_shield_spends_a_namespaced_resource_and_undoes(self):
        grant = AdjustResource("base:white", "base:ap", 3)
        grant.apply(self.state)
        rook = self.state.board.at((7, 0))

        self.pipeline.use_ability(rook, "base:rook_shield")

        self.assertEqual(self.state.resources["base:white"]["base:ap"], 0)
        self.assertIn("base:shield", self.state.board.at((6, 0)).statuses)
        self.assertEqual(self.state.current_side, "base:black")
        self.pipeline.undo_last()
        self.assertEqual(self.state.resources["base:white"]["base:ap"], 3)
        self.assertNotIn("base:shield", self.state.board.at((6, 0)).statuses)
        self.assertEqual(self.state.current_side, "base:white")

    def test_ability_use_is_a_turn_action(self):
        grant = AdjustResource("base:white", "base:ap", 3)
        grant.apply(self.state)
        rook = self.state.board.at((7, 0))
        self.pipeline.use_ability(rook, "base:rook_shield")
        with self.assertRaises(ValueError):
            self.pipeline.use_ability(rook, "base:rook_shield")

    def test_resource_gain_uses_the_declared_per_side_move_interval(self):
        for _ in range(2):
            self.pipeline.apply(self.pipeline.legal_moves()[0])
            self.pipeline.apply(self.pipeline.legal_moves()[0])

        self.assertEqual(self.state.resources["base:white"]["base:ap"], 1)
        self.assertEqual(self.state.resources["base:black"]["base:ap"], 1)


if __name__ == "__main__":
    unittest.main()
