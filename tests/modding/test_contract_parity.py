"""Milestone 1 integration checks for the complete loader contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.modding.loader import load

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


if __name__ == "__main__":
    unittest.main()
