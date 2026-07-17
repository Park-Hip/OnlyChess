"""Dogfood the public code-mod path with the shipped base chess mod."""

from pathlib import Path
import importlib.util
import unittest

from src.modding.loader import load


ROOT = Path(__file__).resolve().parents[2]


class BaseChessCodeTests(unittest.TestCase):
    def test_base_chess_loads_and_registers_only_the_declared_move_verbs(self):
        result = load(ROOT / "mods", enabled_mod_ids=("base:chess",))
        self.assertTrue(result.ok, [error.format() for error in result.errors])
        self.assertEqual(result.registries.verbs["move_type"].ids(), ("base:castle", "base:enpassant"))

    def test_base_chess_register_uses_the_same_public_api_shape(self):
        entry = ROOT / "mods" / "base-chess" / "code" / "__init__.py"
        spec = importlib.util.spec_from_file_location("base_chess_registration_test", entry, submodule_search_locations=[str(entry.parent)])
        module = importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        class RecordingApi:
            def __init__(self): self.calls = []
            def move_type(self, name, generate, *, threatens=True): self.calls.append((name, threatens, callable(generate)))

        api = RecordingApi()
        module.register(api)
        self.assertEqual(api.calls, [("castle", False, True), ("enpassant", True, True)])

    def test_fusion_and_event_references_link_when_enabled(self):
        result = load(ROOT / "mods", enabled_mod_ids=("base:chess", "base:fusion", "base:events"), validate=True, link=True)
        self.assertTrue(result.ok, [error.format() for error in result.errors])
