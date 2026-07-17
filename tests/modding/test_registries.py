"""Tests for the registries and the ID grammar."""

from __future__ import annotations

import unittest

from src.modding.registries import (
    CONTENT_TYPES,
    Registries,
    Registry,
    is_valid_id,
    namespace_of,
    qualify,
)


class IdGrammarTests(unittest.TestCase):
    def test_accepts_the_specs_examples(self):
        for good in ("base:queen", "mymod:dragon", "base:chess", "a1:b2", "my_mod:my_piece"):
            self.assertTrue(is_valid_id(good), good)

    def test_rejects_unnamespaced(self):
        # The whole reason the grammar exists: two authors will both invent a "Dragon".
        self.assertFalse(is_valid_id("dragon"))

    def test_rejects_uppercase(self):
        self.assertFalse(is_valid_id("Base:Queen"))

    def test_rejects_two_colons(self):
        self.assertFalse(is_valid_id("base:sub:queen"))

    def test_rejects_hyphens_and_spaces(self):
        self.assertFalse(is_valid_id("base:my-piece"))
        self.assertFalse(is_valid_id("base:my piece"))

    def test_rejects_empty_parts(self):
        self.assertFalse(is_valid_id(":queen"))
        self.assertFalse(is_valid_id("base:"))


class NamespaceTests(unittest.TestCase):
    def test_a_mod_id_and_a_content_id_use_the_same_rule(self):
        # The model closes over itself: base:chess claims `base`, so base:queen is inside it.
        self.assertEqual(namespace_of("base:chess"), "base")
        self.assertEqual(namespace_of("base:queen"), "base")

    def test_qualify_resolves_a_bare_name_into_the_mods_namespace(self):
        self.assertEqual(qualify("queen", "base:chess"), "base:queen")

    def test_qualify_leaves_an_already_qualified_id_alone(self):
        self.assertEqual(qualify("other:thing", "base:chess"), "other:thing")

    def test_the_pawns_bare_verb_and_the_apis_bare_name_agree(self):
        # pawn.yaml writes `type: enpassant`; code/ calls api.move_type("enpassant").
        # Both resolve through this one rule, which is why neither has to spell `base:`.
        self.assertEqual(qualify("enpassant", "base:chess"), qualify("enpassant", "base:chess"))


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = Registry("piece")

    def test_add_then_get(self):
        self.assertIsNone(self.registry.add("base:queen", "Q", "base:chess"))
        self.assertEqual(self.registry.get("base:queen").value, "Q")
        self.assertIn("base:queen", self.registry)

    def test_a_collision_names_both_mods(self):
        self.registry.add("base:queen", "Q", "base:chess")
        error = self.registry.add("base:queen", "Q2", "base:fusion")
        self.assertIsNotNone(error)
        self.assertIn("base:fusion", error.mod_id)
        self.assertIn("base:chess", error.problem)

    def test_a_collision_does_not_overwrite(self):
        # Whoever loaded second would win invisibly, and load order would become something
        # modders have to reason about.
        self.registry.add("base:queen", "first", "base:chess")
        self.registry.add("base:queen", "second", "base:fusion")
        self.assertEqual(self.registry.get("base:queen").value, "first")

    def test_a_mod_cannot_define_into_someone_elses_namespace(self):
        # Without this, mymod defines base:queen and the breakage looks like a base-game bug.
        error = self.registry.add("base:queen", "Q", "mymod:dragons")
        self.assertIsNotNone(error)
        self.assertIn("does not own", error.problem)
        self.assertIn("mymod:", error.expected)

    def test_sibling_mods_may_share_a_namespace(self):
        # base:chess, base:fusion and base:events all define base:* ids. Under one-namespace-
        # per-mod the base game's own split would be illegal. The originator rule (stage 2)
        # is what permits it; this registry only checks the namespace matches.
        self.assertIsNone(self.registry.add("base:queen", "Q", "base:chess"))
        self.assertIsNone(self.registry.add("base:warden", "W", "base:fusion"))

    def test_a_malformed_id_is_rejected_with_the_grammar_spelled_out(self):
        error = self.registry.add("Dragon", "D", "mymod:dragons")
        self.assertIsNotNone(error)
        self.assertIn("namespace:name", error.expected)

    def test_ids_are_sorted_so_output_is_stable(self):
        for entry_id in ("base:rook", "base:queen", "base:bishop"):
            self.registry.add(entry_id, entry_id, "base:chess")
        self.assertEqual(self.registry.ids(), ("base:bishop", "base:queen", "base:rook"))

    def test_get_of_an_unknown_id_is_none(self):
        self.assertIsNone(self.registry.get("base:nothing"))


class RegistriesTests(unittest.TestCase):
    def test_there_is_a_registry_for_each_of_the_ten_content_types(self):
        registries = Registries()
        self.assertEqual(len(CONTENT_TYPES), 10)
        self.assertEqual(set(registries.content), set(CONTENT_TYPES))

    def test_registries_are_instances_not_globals(self):
        # Global registries make "load these mods but not that one" impossible — which is
        # exactly what gate G1 must do to prove castle comes from base:chess. A design where
        # the dogfooding test cannot be written cannot support the dogfooding claim.
        first, second = Registries(), Registries()
        first.content["piece"].add("base:queen", "Q", "base:chess")
        self.assertNotIn("base:queen", second.content["piece"])

    def test_nothing_is_registered_by_importing_this_module(self):
        # CLAUDE.md: registries are populated by the loader at runtime, never by import side
        # effects. A fresh Registries() must be empty, or @register_event has come back.
        registries = Registries()
        for registry in list(registries.content.values()) + list(registries.verbs.values()):
            self.assertEqual(len(registry), 0)


if __name__ == "__main__":
    unittest.main()
