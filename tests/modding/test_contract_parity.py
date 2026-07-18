"""Milestone 1 integration checks for the complete loader contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.modding.loader import ENGINE_VERSION, load

from .builders import write_mod


class LoaderContractParityTests(unittest.TestCase):
    def test_dependency_order_patch_and_replacement_use_one_public_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_mod(
                root, "foundation",
                manifest="""id: proof:foundation
name: Foundation
version: 1.0.0
code: false
""",
                files={"runner.yaml": """type: piece
id: proof:runner
name: Runner
moves: []
"""},
            )
            write_mod(
                root, "extension",
                manifest="""id: proof:extension
name: Extension
version: 1.0.0
code: false
dependencies:
  required: { proof:foundation: '^1.0' }
""",
                files={
                    "replacement.yaml": """type: piece
id: proof:swift_runner
replaces: proof:runner
name: Swift Runner
moves: []
""",
                    "patch.yaml": """type: patch
id: proof:tuning
patches:
  - { target: proof:runner, op: set, path: name, value: Tuned Runner }
""",
                },
            )

            result = load(root, validate=True, link=True)

            self.assertTrue(result.ok, [error.format() for error in result.errors])
            self.assertEqual(result.mods, ("proof:foundation", "proof:extension"))
            self.assertNotIn("proof:runner", result.registries.content["piece"])
            replacement = result.registries.content["piece"].get("proof:swift_runner")
            self.assertEqual(replacement.value.tree["name"], "Tuned Runner")

    def test_missing_required_dependency_disables_only_the_dependent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_mod(root, "broken", manifest="""id: proof:broken
name: Broken
version: 1.0.0
code: false
dependencies:
  required: { absent:mod: '^1.0' }
""")
            write_mod(root, "healthy", manifest="""id: healthy:demo
name: Healthy
version: 1.0.0
code: false
""", files={"piece.yaml": "type: piece\nid: healthy:token\nname: Token\nmoves: []\n"})

            result = load(root, validate=True)

            self.assertFalse(result.ok)
            self.assertEqual(result.mods, ("healthy:demo",))
            self.assertIn("healthy:token", result.registries.content["piece"])
            self.assertIn("required dependency 'absent:mod'", result.errors[0].problem)


class RoyalPieceRequirementTests(unittest.TestCase):
    """A side with no royal piece is rejected at link, not discovered by crashing mid-frame.

    `movegen.legal_moves` filters on `threatened()`, which resolves a royal piece by name, and
    `EngineSession.outcome` reports checkmate or stalemate. Both require royalty, so a board
    that omits it is content the engine cannot play — and the error contract says that has to
    be said at load time, with attribution, rather than as a ValueError while drawing.
    """

    def _mod(self, root, *, royal: bool):
        properties = "properties: { royal: true }\n" if royal else ""
        write_mod(root, "kingless", manifest="""id: kingless:mod
name: Kingless
version: 1.0.0
code: false
""", files={
            "piece.yaml": f"type: piece\nid: kingless:token\nname: Token\n{properties}moves: []\n",
            "board.yaml": """type: board
id: kingless:board
size: [1, 2]
sides:
  - { id: kingless:blue, name: Blue, forward: down, promotes_at: 0, moves_first: true }
rows:
  - { row: 0, side: kingless:blue, pieces: [kingless:token, kingless:token] }
""",
            "mode.yaml": "type: game_mode\nid: kingless:mode\nname: Kingless\nboard: kingless:board\npools: []\n",
        })

    def test_a_side_without_a_royal_piece_is_an_attributed_link_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._mod(root, royal=False)

            result = load(root, validate=True, link=True)

            self.assertFalse(result.ok)
            error = result.errors[0]
            self.assertEqual(error.mod_id, "kingless:mod")
            self.assertEqual(error.field, "sides[0]")
            self.assertIn("kingless:blue", error.problem)
            self.assertIn("royal", error.problem)
            self.assertIn("royal: true", error.expected)

    def test_the_same_board_links_once_a_placed_piece_is_royal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._mod(root, royal=True)

            result = load(root, validate=True, link=True)

            self.assertTrue(result.ok, [error.format() for error in result.errors])
            self.assertIn("kingless:mode", result.linked.modes)

    def test_an_unplayable_board_does_not_reach_the_mode_catalog(self):
        """The crash this replaces happened on the first drawn frame, so the gate has to be
        early enough that no session can be built from the board at all."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._mod(root, royal=False)

            result = load(root, validate=True, link=True)

            self.assertNotIn("kingless:mode", result.linked.modes)


class EngineCompatibilityTests(unittest.TestCase):
    """`engine:` gates a mod against ENGINE_VERSION, not just against its own grammar.

    A mod written for an engine this one is not names verbs and fields that may have been
    renamed or removed. Loading it anyway turns a manifest that stated the incompatibility
    into a pile of unknown-key errors blaming the modder for the engine's version drift.
    """

    def test_a_mod_built_for_another_engine_major_is_disabled_with_attribution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_mod(root, "future", manifest="""id: future:mod
name: Future
version: 1.0.0
code: false
engine: "^2.0"
""", files={"piece.yaml": "type: piece\nid: future:token\nname: Token\nmoves: []\n"})

            result = load(root, validate=True)

            self.assertFalse(result.ok)
            self.assertEqual(result.mods, ())
            self.assertNotIn("future:token", result.registries.content["piece"])
            error = result.errors[0]
            self.assertEqual(error.mod_id, "future:mod")
            self.assertEqual(error.file, "manifest.yaml")
            self.assertEqual(error.field, "engine")
            self.assertIn("^2.0", error.problem)
            self.assertIn(ENGINE_VERSION, error.problem)

    def test_a_compatible_range_loads_and_an_absent_one_is_not_a_constraint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_mod(root, "declared", manifest=f"""id: declared:mod
name: Declared
version: 1.0.0
code: false
engine: "^{ENGINE_VERSION}"
""", files={"piece.yaml": "type: piece\nid: declared:token\nname: Token\nmoves: []\n"})
            write_mod(root, "silent", manifest="""id: silent:mod
name: Silent
version: 1.0.0
code: false
""", files={"piece.yaml": "type: piece\nid: silent:token\nname: Token\nmoves: []\n"})

            result = load(root, validate=True)

            self.assertTrue(result.ok, [error.format() for error in result.errors])
            self.assertIn("declared:token", result.registries.content["piece"])
            self.assertIn("silent:token", result.registries.content["piece"])

    def test_an_incompatible_mod_disables_the_mods_that_depend_on_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_mod(root, "future", manifest="""id: future:mod
name: Future
version: 1.0.0
code: false
engine: "^2.0"
""")
            write_mod(root, "dependent", manifest="""id: dependent:mod
name: Dependent
version: 1.0.0
code: false
dependencies:
  required: { future:mod: '^1.0' }
""", files={"piece.yaml": "type: piece\nid: dependent:token\nname: Token\nmoves: []\n"})

            result = load(root, validate=True)

            self.assertFalse(result.ok)
            self.assertEqual(result.mods, ())
            self.assertNotIn("dependent:token", result.registries.content["piece"])
            problems = [error.problem for error in result.errors]
            self.assertTrue(any("this engine is" in problem for problem in problems), problems)
            self.assertTrue(any("disabled because required dependency" in problem for problem in problems), problems)

    def test_a_range_that_is_not_a_caret_range_is_rejected_as_a_manifest_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_mod(root, "vague", manifest="""id: vague:mod
name: Vague
version: 1.0.0
code: false
engine: ">=1.0"
""")

            result = load(root, validate=True)

            self.assertFalse(result.ok)
            self.assertEqual(result.errors[0].field, "engine")
            self.assertIn("^1.0", result.errors[0].expected)


if __name__ == "__main__":
    unittest.main()
