"""A save is a state snapshot, and it refuses to load against a mod set it was not played on."""

import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from src import savegame
from src.engine.actions import AdjustResource
from src.runtime import ApplicationContext, EngineSession


class SaveGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = ApplicationContext.load()

    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.root = Path(self._directory.name)
        self.addCleanup(self._directory.cleanup)

    def session(self, **kwargs):
        return EngineSession(self.context.load_result, "base:advanced", **kwargs)

    def played(self):
        session = self.session(time_limit=300)
        for start, end in (((6, 4), (4, 4)), ((1, 3), (3, 3)), ((4, 4), (3, 3))):
            session.move(start, end)
        session.tick(37.0)
        return session

    def round_trip(self, session):
        savegame.write(session, self.root)
        return savegame.restore(self.context.load_result, savegame.read(self.root))

    def test_the_board_comes_back_exactly(self):
        session = self.played()

        restored = self.round_trip(session)

        self.assertEqual(
            sorted((piece.pos, piece.definition.id, piece.side) for piece in session.state.board.pieces()),
            sorted((piece.pos, piece.definition.id, piece.side) for piece in restored.state.board.pieces()),
        )
        self.assertEqual(session.state.current_side, restored.state.current_side)

    def test_the_game_is_playable_after_loading(self):
        restored = self.round_trip(self.played())

        move = restored.legal_moves[0]
        restored.move(move.start, move.end)

        self.assertEqual(1, len(restored.state.action_log))

    def test_clocks_captures_and_resources_survive(self):
        session = self.played()
        AdjustResource("base:white", "base:ap", 3).apply(session.state)

        restored = self.round_trip(session)

        self.assertEqual(session.clocks, restored.clocks)
        self.assertEqual(session.state.captures, restored.state.captures)
        self.assertEqual(session.state.resources, restored.state.resources)

    def test_statuses_survive_with_their_remaining_duration(self):
        session = self.session()
        AdjustResource("base:white", "base:ap", 3).apply(session.state)
        session.use_ability((7, 0), "base:rook_shield")
        shielded = {piece.pos for piece in session.state.board.pieces() if "base:shield" in piece.statuses}
        self.assertTrue(shielded)

        restored = self.round_trip(session)

        self.assertEqual(shielded, {piece.pos for piece in restored.state.board.pieces() if "base:shield" in piece.statuses})

    def test_a_fused_piece_comes_back_composed(self):
        """A fused definition is made at runtime, not registered, so there is nothing for a save to
        look up by id — the component list is what gets restored."""
        session = self.session()
        for start, end in (((6, 4), (4, 4)), ((1, 3), (3, 3)), ((4, 4), (3, 3))):
            session.move(start, end)
        rook, bishop = session.state.board.at((7, 0)), session.state.board.at((0, 2))
        session.state.board.remove(bishop.pos)
        session.state.board.remove(rook.pos)
        session.state.board.place(rook, (4, 0))
        session.state.board.place(bishop, (3, 0))
        session.state.current_side = "base:white"
        session.move((4, 0), (3, 0))
        fused = session.state.board.at((3, 0))
        self.assertEqual(("base:rook", "base:bishop"), fused.definition.components)

        restored = self.round_trip(session)

        recovered = restored.state.board.at((3, 0))
        self.assertEqual(("base:rook", "base:bishop"), recovered.definition.components)
        self.assertEqual(fused.definition.moves, recovered.definition.moves)

    def test_a_pending_event_and_its_bound_zone_survive(self):
        session = self.session()
        session.state.pending_events["base:main_pool"] = "base:my_danh_iran"
        session.state.pending_bindings["base:main_pool"] = {"zone": (3, 2, 2, 2)}

        restored = self.round_trip(session)

        self.assertEqual("base:my_danh_iran", restored.state.pending_events["base:main_pool"])
        self.assertEqual((3, 2, 2, 2), restored.state.pending_bindings["base:main_pool"]["zone"])
        self.assertEqual(((3, 2), (3, 3), (4, 2), (4, 3)), restored.presentation_snapshot().warning.squares)

    def test_a_save_from_a_different_mod_set_is_refused_by_name(self):
        """Content is data: a piece can gain a move, a fusion table can change shape. Restoring a
        board into changed rules would produce a game that looks fine and is not the one saved."""
        savegame.write(self.played(), self.root)
        data = savegame.read(self.root)
        data["mods"] = [["base:chess", "0.9.0"]]

        with self.assertRaises(savegame.SaveError) as raised:
            savegame.restore(self.context.load_result, data)

        self.assertIn("different mod set", str(raised.exception))
        self.assertIn("base:chess 0.9.0", str(raised.exception))

    def test_an_unreadable_save_is_refused_rather_than_crashing(self):
        (self.root / savegame.SAVE_FILE).write_text("{not json", encoding="utf-8")

        with self.assertRaises(savegame.SaveError):
            savegame.read(self.root)

    def test_a_save_from_a_future_format_is_refused(self):
        (self.root / savegame.SAVE_FILE).write_text(json.dumps({"format": savegame.FORMAT_VERSION + 1}), encoding="utf-8")

        with self.assertRaises(savegame.SaveError):
            savegame.read(self.root)

    def test_no_save_file_is_reported_without_reading_one(self):
        self.assertFalse(savegame.exists(self.root))
        savegame.write(self.played(), self.root)
        self.assertTrue(savegame.exists(self.root))


if __name__ == "__main__":
    unittest.main()
