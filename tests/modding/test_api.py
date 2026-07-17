"""Tests for the injected verb path.

§2.1 calls this "the most important structural decision in this document, because the
dogfooding claim rests entirely on it." So it gets the most direct tests in the wave.
"""

from __future__ import annotations

import unittest

from src.modding.api import ModApi, ModApiError
from src.modding.registries import Registries


def _noop(*args, **kwargs):
    return None


class RegisteringTests(unittest.TestCase):
    def setUp(self):
        self.registries = Registries()
        self.api = ModApi("base:chess", self.registries)

    def test_a_bare_name_lands_in_the_mods_namespace(self):
        # api.move_type("castle") from base:chess is base:castle — the same id the pawn's
        # bare `type: enpassant` resolves to. One rule, both sides.
        self.assertEqual(self.api.move_type("castle", _noop), "base:castle")
        self.assertIn("base:castle", self.registries.verbs["move_type"])

    def test_the_registered_verb_keeps_its_function(self):
        def generate():
            return "moves"

        self.api.move_type("castle", generate)
        self.assertIs(self.registries.verbs["move_type"].get("base:castle").value.generate, generate)

    def test_threatens_defaults_true_and_is_settable(self):
        # castle is the move that threatens nothing — the distinction §1 traces a live chess
        # bug to. A verb that could not express it would leave include_castle's hack in place.
        self.api.move_type("enpassant", _noop)
        self.api.move_type("castle", _noop, threatens=False)
        self.assertTrue(self.registries.verbs["move_type"].get("base:enpassant").value.threatens)
        self.assertFalse(self.registries.verbs["move_type"].get("base:castle").value.threatens)

    def test_the_api_records_who_registered(self):
        self.api.move_type("castle", _noop)
        self.assertEqual(self.registries.verbs["move_type"].get("base:castle").mod_id, "base:chess")

    def test_a_mod_cannot_register_into_another_namespace(self):
        api = ModApi("mymod:dragons", self.registries)
        with self.assertRaises(ModApiError) as caught:
            api.move_type("base:castle", _noop)
        self.assertIn("does not own", caught.exception.error.problem)

    def test_a_verb_collision_names_both_mods_and_the_verb(self):
        self.api.move_type("castle", _noop)
        sibling = ModApi("base:fusion", self.registries)
        with self.assertRaises(ModApiError) as caught:
            sibling.move_type("castle", _noop)
        message = caught.exception.error.format()
        self.assertIn("base:fusion", message)
        self.assertIn("base:chess", message)
        self.assertIn("castle", message)

    def test_api_misuse_raises_rather_than_collecting(self):
        # The audience changed. Collect-don't-fail-fast exists for a non-coder with six
        # typos; stage 4's own table says this reader writes Python and gets a traceback.
        with self.assertRaises(ModApiError):
            ModApi("mymod:x", self.registries).move_type("NotAnId!", _noop)


class FreezeTests(unittest.TestCase):
    """The vocabulary freeze, enforced by the object rather than by discipline."""

    def setUp(self):
        self.registries = Registries()
        self.api = ModApi("mymod:x", self.registries)

    def test_registration_works_before_the_freeze(self):
        self.assertEqual(self.api.move_type("drop", _noop), "mymod:drop")

    def test_the_api_goes_dead_after_stage_four(self):
        # A mod that stashes its api and calls it from a later hook gets a clear error
        # naming the verb, rather than a half-registration nobody notices.
        self.api._retire()
        with self.assertRaises(ModApiError) as caught:
            self.api.move_type("drop", _noop)
        self.assertIn("after loading finished", caught.exception.error.problem)

    def test_a_retired_api_registers_nothing(self):
        # A verb appearing after validation would mean content was checked against an
        # incomplete vocabulary — the KeyError-at-turn-20 failure wearing a hat.
        self.api._retire()
        with self.assertRaises(ModApiError):
            self.api.move_type("drop", _noop)
        self.assertEqual(len(self.registries.verbs["move_type"]), 0)


class RecordingFake:
    """The dogfooding test's instrument: an api that records instead of registering.

    §2.1: *"Pass a recording fake `api` to `base:chess`'s `register` and assert exactly what
    it registers. That is the dogfooding claim as an executable test, and it does not exist
    in any other design."* This class is the proof that claim is true — a mod that imported
    from `src` could not be intercepted this way.
    """

    def __init__(self):
        self.calls: list[tuple] = []

    def move_type(self, name, generate, *, threatens=True):
        self.calls.append(("move_type", name, threatens))
        return name


class InjectionTests(unittest.TestCase):
    def test_a_mod_can_be_handed_a_fake_and_never_notice(self):
        # If mods imported from src, this test could not be written: there would be no seam
        # to substitute at, and "no privileged path" would be a convention rather than a
        # property.
        def register(api):
            api.move_type("castle", _noop, threatens=False)
            api.move_type("enpassant", _noop)

        fake = RecordingFake()
        register(fake)

        self.assertEqual(
            fake.calls,
            [("move_type", "castle", False), ("move_type", "enpassant", True)],
        )

    def test_the_api_object_is_the_whole_surface(self):
        # If base:chess ever needs something this object lacks, it must become a visibly
        # different object — which is what makes privilege impossible to hide rather than
        # merely discouraged.
        public = {name for name in dir(ModApi) if not name.startswith("_")}
        self.assertEqual(public, {"mod_id", "move_type"})


if __name__ == "__main__":
    unittest.main()
