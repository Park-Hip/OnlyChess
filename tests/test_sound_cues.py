"""Milestone 6, slice 2: mods declare notification->clip cues over owned assets, and
the runtime emits the notification kinds those cues map to.

The renderer already dispatches notifications to clips (`PresentationRuntime.play`); these
tests close the two ends that made the game silent: real declared cues over real assets,
and emission of the `promotion_chosen` / `outcome_reached` kinds that nothing fired before."""

import unittest

from src.engine.piece import Piece
from src.runtime import ApplicationContext, EngineSession


class SoundCueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = ApplicationContext.load()

    def _sound(self, sound_id):
        result = self.context.load_result
        entry = result.registries.content["sound"].get(sound_id)
        return entry, result.mod_roots[entry.mod_id]

    def _session(self, mode_id="base:vanilla"):
        return EngineSession(self.context.load_result, mode_id)

    def _kinds(self, session):
        return {notice.kind for notice in session.drain_notifications()}

    def test_base_cues_map_to_owned_assets_that_exist(self):
        entry, root = self._sound("base:classic_sounds")
        cues = entry.value.tree["cues"]
        self.assertTrue(cues, "base ships no cues; the game would be silent")
        for kind, path in cues.items():
            self.assertTrue((root / path).is_file(), f"cue {kind} points at missing asset {path}")

    def test_proof_mod_demonstrates_its_own_cue_asset(self):
        entry, root = self._sound("proof:sound")
        cues = entry.value.tree["cues"]
        self.assertIn("move_completed", cues)
        self.assertTrue((root / cues["move_completed"]).is_file())

    def test_every_declared_base_cue_kind_is_actually_emitted_somewhere(self):
        # Guard against declaring cues for notifications the runtime never fires (dead audio).
        # The four consequence kinds are derived from the action log in EngineSession.move/
        # use_ability (slice 8); that they genuinely fire is proven in
        # tests/test_consequence_notifications.py, so they belong in this allowlist.
        emitted = {
            "move_completed", "capture_completed", "ability_used", "promotion_chosen",
            "undo_completed", "outcome_reached",
            "status_applied", "status_expired", "event_warning", "event_executed",
        }
        entry, _ = self._sound("base:classic_sounds")
        self.assertLessEqual(set(entry.value.tree["cues"]), emitted)

    def test_plain_move_emits_move_completed(self):
        session = self._session()
        move = next(m for m in session.legal_moves if not m.captured and not m.choices)
        session.move(move.start, move.end)
        self.assertIn("move_completed", self._kinds(session))

    def test_promotion_emits_promotion_chosen(self):
        session = self._session()
        state = session.state
        for piece in list(state.board.pieces()):
            state.board.remove(piece.pos)
        state.board.place(Piece(1, state.piece_defs["base:pawn"], "base:white", (1, 0), has_moved=True), (1, 0))
        state.board.place(Piece(2, state.piece_defs["base:king"], "base:white", (7, 4)), (7, 4))
        state.board.place(Piece(3, state.piece_defs["base:king"], "base:black", (0, 4)), (0, 4))

        session.move((1, 0), (0, 0), choice="base:queen")

        kinds = self._kinds(session)
        self.assertIn("promotion_chosen", kinds)
        self.assertNotIn("move_completed", kinds)  # one notification per action: the specific kind wins

    def test_checkmating_move_emits_outcome_reached(self):
        session = self._session()
        state = session.state
        for piece in list(state.board.pieces()):
            state.board.remove(piece.pos)
        state.board.place(Piece(1, state.piece_defs["base:king"], "base:black", (0, 4)), (0, 4))
        state.board.place(Piece(2, state.piece_defs["base:king"], "base:white", (7, 7)), (7, 7))
        state.board.place(Piece(3, state.piece_defs["base:rook"], "base:white", (1, 7)), (1, 7))  # seals rank 1
        state.board.place(Piece(4, state.piece_defs["base:rook"], "base:white", (6, 0)), (6, 0))  # delivers the mate

        session.move((6, 0), (0, 0))  # ladder mate on the back rank

        self.assertIsNotNone(session.outcome)
        self.assertIn("outcome_reached", self._kinds(session))


if __name__ == "__main__":
    unittest.main()
