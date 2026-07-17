"""Extensibility probe: code grows vocabulary, data consumes it."""

import tempfile
import unittest
from pathlib import Path

from src.modding.loader import load


class WaveFiveProbeTests(unittest.TestCase):
    def test_code_mod_verb_is_available_to_a_separate_data_mod(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            code = root / "language"; code.mkdir()
            (code / "manifest.yaml").write_text("id: probe:language\nname: Language\nversion: 1\ncode: true\n", encoding="utf-8")
            (code / "code").mkdir()
            (code / "code" / "__init__.py").write_text("def register(api):\n    api.move_type('dash', lambda context, piece, part, threat: [])\n", encoding="utf-8")
            data = root / "content"; data.mkdir()
            (data / "manifest.yaml").write_text("id: probe:content\nname: Content\nversion: 1\ncode: false\n", encoding="utf-8")
            (data / "piece.yaml").write_text("type: piece\nid: probe:runner\nmoves: [{type: dash}]\n", encoding="utf-8")
            result = load(root)
            self.assertTrue(result.ok, [error.format() for error in result.errors])
            self.assertIn("probe:dash", result.registries.verbs["move_type"])
            self.assertEqual(result.registries.content["piece"].get("probe:runner").value.tree["moves"][0]["type"], "dash")


if __name__ == "__main__":
    unittest.main()
