"""End-to-end proof that a data ability can apply a visible status."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from src.runtime import ApplicationContext, EngineSession


class ProofAbilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = ApplicationContext.load()

    def test_glow_up_applies_glow_and_emits_ability_notification(self):
        session = EngineSession(self.context.load_result, "proof:arena_mode")
        square = (5, 0)

        self.assertIn("proof:glow_up", session.abilities_for(square))
        session.use_ability(square, "proof:glow_up")

        piece = session.state.board.at(square)
        self.assertIn("proof:glow", piece.statuses)
        self.assertIn("ability_used", [notice.kind for notice in session.drain_notifications()])


if __name__ == "__main__":
    unittest.main()
