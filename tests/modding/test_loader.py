"""Tests for the loader stages Wave 1 implements: discover, parse, load code, register, activate."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from src.modding import ModApiError, ModLoadError
from src.modding.loader import activate, discover, load

from .builders import data_mod, playable_mode, write_mod

REPO_ROOT = Path(__file__).resolve().parents[2]


class LoaderTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mods = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def problems(self, result) -> str:
        return "\n\n".join(error.format() for error in result.errors)


class DiscoverTests(LoaderTest):
    def test_a_directory_without_a_manifest_is_not_a_mod(self):
        # The one silent skip in the loader, and it exists so a stray README/ or .git/ is
        # not an error. Every other skip in this codebase is a bug.
        (self.mods / ".git").mkdir()
        (self.mods / "README").mkdir()
        manifests, errors = discover(self.mods)
        self.assertEqual(manifests, [])
        self.assertEqual(errors, [])

    def test_a_loose_file_is_ignored(self):
        (self.mods / "notes.txt").write_text("hello", encoding="utf-8")
        manifests, errors = discover(self.mods)
        self.assertEqual((manifests, errors), ([], []))

    def test_a_missing_mods_directory_is_not_a_crash(self):
        manifests, errors = discover(self.mods / "nope")
        self.assertEqual((manifests, errors), ([], []))

    def test_mods_come_back_in_a_deterministic_order(self):
        for folder, mod_id in (("z", "zeta:m"), ("a", "alpha:m"), ("m", "mid:m")):
            data_mod(self.mods, folder, mod_id)
        manifests, _ = discover(self.mods)
        self.assertEqual([m.mod_id for m in manifests], ["alpha:m", "mid:m", "zeta:m"])

    def test_an_unreadable_manifest_is_attributed_to_the_folder(self):
        # The mod's id is exactly the thing we failed to read, so the folder name is the
        # only identity left — and the modder still needs to know which directory to open.
        write_mod(self.mods, "brokenmod", manifest="id: [unclosed\n")
        _, errors = discover(self.mods)
        self.assertEqual(len(errors), 1)
        self.assertIn("brokenmod", errors[0].mod_id)

    def test_a_manifest_missing_required_fields_names_all_of_them(self):
        write_mod(self.mods, "thin", manifest="id: thin:mod\n")
        _, errors = discover(self.mods)
        self.assertIn("name", errors[0].problem)
        self.assertIn("version", errors[0].problem)

    def test_a_malformed_mod_id_is_rejected_with_the_grammar(self):
        write_mod(self.mods, "shouty", manifest="id: Shouty\nname: X\nversion: 1.0.0\n")
        _, errors = discover(self.mods)
        self.assertIn("namespace:name", errors[0].expected)
        self.assertEqual(errors[0].field, "id")


class TrustModelTests(LoaderTest):
    def test_undeclared_code_is_a_hard_error_not_a_warning(self):
        # The manifest's honesty is the whole trust model. Python cannot be meaningfully
        # sandboxed, so "this mod is pure data" is worth exactly as much as this check —
        # which makes it the one real security property on offer, and it is free.
        write_mod(
            self.mods,
            "sneaky",
            manifest="id: sneaky:mod\nname: Sneaky\nversion: 1.0.0\ncode: false\n",
            code="def register(api):\n    pass\n",
        )
        _, errors = discover(self.mods)
        self.assertEqual(len(errors), 1)
        self.assertIn("code: false", errors[0].problem)
        self.assertEqual(errors[0].field, "code")

    def test_declared_code_that_is_missing_is_reported(self):
        write_mod(self.mods, "promised", manifest="id: promised:mod\nname: P\nversion: 1.0.0\ncode: true\n")
        result = load(self.mods)
        self.assertIn("no code/__init__.py", self.problems(result))

    def test_code_no_is_rejected_rather_than_silently_meaning_true(self):
        # The trapdoor under the YAML 1.2 pin: `code: no` is correctly the *string* "no",
        # and bool("no") is True. Written the obvious way, the natural spelling of false
        # would silently mean true — in the one field the trust model rests on — and the
        # error would quote a `code: true` the modder never wrote.
        write_mod(
            self.mods,
            "norway",
            manifest="id: norway:mod\nname: N\nversion: 1.0.0\ncode: no\n",
            code="def register(api):\n    pass\n",
        )
        _, errors = discover(self.mods)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].field, "code")
        self.assertIn("not a true/false value", errors[0].problem)
        self.assertIn("`yes`, `no`, `on` and `off` are ordinary words", errors[0].expected)

    def test_a_quoted_boolean_is_rejected_too(self):
        write_mod(self.mods, "quoted", manifest='id: q:mod\nname: Q\nversion: 1.0.0\ncode: "false"\n')
        _, errors = discover(self.mods)
        self.assertIn("not a true/false value", errors[0].problem)

    def test_real_booleans_still_work_both_ways(self):
        write_mod(self.mods, "datamod", manifest="id: data:mod\nname: D\nversion: 1.0.0\ncode: false\n")
        write_mod(
            self.mods,
            "codemod",
            manifest="id: code:mod\nname: C\nversion: 1.0.0\ncode: true\n",
            code="def register(api):\n    pass\n",
        )
        manifests, errors = discover(self.mods)
        self.assertEqual(errors, [])
        self.assertEqual({m.mod_id: m.ships_code for m in manifests}, {"code:mod": True, "data:mod": False})

    def test_a_mod_with_no_code_field_is_a_data_mod(self):
        write_mod(self.mods, "plain", manifest="id: plain:mod\nname: P\nversion: 1.0.0\n")
        manifests, errors = discover(self.mods)
        self.assertEqual(errors, [])
        self.assertFalse(manifests[0].ships_code)


class ParseStageTests(LoaderTest):
    def test_content_type_comes_from_the_file_not_the_folder(self):
        # Folders are for humans. A modder who puts a piece in stuff/things.yaml gets a
        # working mod and a tidiness problem, not a load error.
        data_mod(self.mods, "tidy", "tiny:mod", stuff__things="type: piece\nid: tiny:blob\n")
        result = load(self.mods)
        self.assertEqual(result.errors, [])
        self.assertIn("tiny:blob", result.registries.content["piece"])

    def test_the_manifest_is_not_parsed_as_content(self):
        data_mod(self.mods, "m", "tiny:mod")
        result = load(self.mods)
        # The manifest has no `type:`; if it went through the content path it would error.
        self.assertEqual(result.errors, [])

    def test_a_broken_file_is_reported_with_its_position(self):
        data_mod(self.mods, "m", "tiny:mod", pieces__bad="type: piece\nid: [unclosed\n")
        result = load(self.mods)
        self.assertEqual(len(result.errors), 1)
        self.assertIsNotNone(result.errors[0].line)
        self.assertEqual(result.errors[0].file, "pieces/bad.yaml")

    def test_a_files_path_is_reported_relative_to_the_mod(self):
        # An absolute path from someone else's machine is noise in an error message.
        data_mod(self.mods, "m", "tiny:mod", pieces__blob="type: peice\nid: tiny:blob\n")
        result = load(self.mods)
        self.assertEqual(result.errors[0].file, "pieces/blob.yaml")

    def test_python_under_code_is_not_read_as_content(self):
        write_mod(
            self.mods,
            "codemod",
            manifest="id: cm:mod\nname: CM\nversion: 1.0.0\ncode: true\n",
            files={"code/notes.yaml": "this: is not content\n"},
            code="def register(api):\n    pass\n",
        )
        result = load(self.mods)
        self.assertEqual(result.errors, [])


class CollectNotFailFastTests(LoaderTest):
    def test_six_typos_are_reported_in_one_run(self):
        # The ergonomics requirement with teeth: fail-fast means a non-coder with six typos
        # runs the game six times, and each run tells them about one. That loop is the
        # difference between a modding system someone uses and one they abandon.
        files = {f"pieces__p{i}": f"type: peice\nid: tiny:p{i}\n" for i in range(6)}
        data_mod(self.mods, "typos", "tiny:mod", **files)
        result = load(self.mods)
        self.assertEqual(len(result.errors), 6)

    def test_one_broken_mod_does_not_stop_another_from_loading(self):
        data_mod(self.mods, "good", "good:mod", pieces__ok="type: piece\nid: good:blob\n")
        data_mod(self.mods, "bad", "bad:mod", pieces__no="type: piece\nid: [unclosed\n")
        result = load(self.mods)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("good:blob", result.registries.content["piece"])


class DisabledWholeTests(LoaderTest):
    """*"A mod with any error is disabled whole. Never half-loaded."*

    The reason is in the spec and it is not tidiness: a chess mod that loads every piece
    except the queen produces a game that looks fine and is wrong, and the player has no way
    to know. Registration happens before every error is in, so this costs a retraction.
    """

    def test_one_bad_file_disables_the_mods_good_files_too(self):
        data_mod(
            self.mods,
            "m",
            "tiny:mod",
            pieces__a="type: piece\nid: tiny:good1\n",
            pieces__b="type: piece\nid: tiny:good2\n",
            pieces__bad="type: piece\nid: [unclosed\n",
        )
        result = load(self.mods)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.registries.content["piece"].ids(), ())
        self.assertEqual(result.mods, ())

    def test_a_broken_mod_does_not_take_a_healthy_one_with_it(self):
        data_mod(self.mods, "good", "good:mod", pieces__ok="type: piece\nid: good:blob\n")
        data_mod(
            self.mods,
            "bad",
            "bad:mod",
            pieces__ok="type: piece\nid: bad:fine\n",
            pieces__no="type: piece\nid: [unclosed\n",
        )
        result = load(self.mods)
        self.assertEqual(result.registries.content["piece"].ids(), ("good:blob",))
        self.assertEqual(result.mods, ("good:mod",))

    def test_a_code_mods_verbs_go_when_the_mod_fails_after_registering(self):
        # The mod registers a verb, then raises. Without the retraction the verb outlives
        # the mod that defined it, and the vocabulary contains something no loaded mod owns.
        write_mod(
            self.mods,
            "halfway",
            manifest="id: halfway:mod\nname: H\nversion: 1.0.0\ncode: true\n",
            code="""
            def register(api):
                api.move_type("ghost", lambda: [])
                raise RuntimeError("changed my mind")
            """,
        )
        result = load(self.mods)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.registries.verbs["move_type"].ids(), ())

    def test_a_duplicate_id_disables_the_mod_that_lost_not_the_one_that_won(self):
        data_mod(self.mods, "first", "one:mod", pieces__x="type: piece\nid: one:thing\n")
        data_mod(
            self.mods,
            "second",
            "two:mod",
            pieces__x="type: piece\nid: two:thing\n",
            pieces__y="type: piece\nid: two:thing\n",
        )
        result = load(self.mods)
        self.assertEqual(result.registries.content["piece"].ids(), ("one:thing",))


class DuplicateModIdTests(LoaderTest):
    def test_two_folders_claiming_one_id_names_both_folders(self):
        # Usually two versions of a mod installed side by side. The ids are identical, so
        # only the folders tell them apart — an error written in ids would name neither.
        for folder in ("mymod-1.0", "mymod-2.0"):
            data_mod(self.mods, folder, "mymod:x", pieces__p="type: piece\nid: mymod:thing\n")
        _, errors = discover(self.mods)
        self.assertEqual(len(errors), 1)
        self.assertIn("mymod-1.0", errors[0].problem)
        self.assertIn("mymod-2.0", errors[0].file)

    def test_the_duplicate_does_not_also_produce_a_content_collision(self):
        # Without the discover check this reports "'mymod:thing' is already defined by
        # mymod:x" — the same name on both sides, naming neither folder.
        for folder in ("mymod-1.0", "mymod-2.0"):
            data_mod(self.mods, folder, "mymod:x", pieces__p="type: piece\nid: mymod:thing\n")
        result = load(self.mods)
        self.assertEqual(len(result.errors), 1)


class LoadCodeTests(LoaderTest):
    def test_a_code_mod_registers_a_verb_through_the_api(self):
        # This is the shape base:chess uses at Wave 4 for castle and enpassant. If a third-
        # party mod can do this, the "no privileged path" claim has something behind it.
        write_mod(
            self.mods,
            "shogi",
            manifest="id: shogi:drops\nname: Drops\nversion: 1.0.0\ncode: true\n",
            code="""
            def register(api):
                api.move_type("drop", lambda: [])
            """,
        )
        result = load(self.mods)
        self.assertEqual(result.errors, [])
        self.assertIn("shogi:drop", result.registries.verbs["move_type"])

    def test_the_api_a_mod_receives_is_scoped_to_that_mod(self):
        # The mod never says who it is; the api already knows. That is what stops a mod
        # registering into someone else's namespace by forgetting a prefix, and it works
        # only because the object is handed over rather than imported.
        write_mod(
            self.mods,
            "shogi",
            manifest="id: shogi:drops\nname: Drops\nversion: 1.0.0\ncode: true\n",
            code="""
            def register(api):
                api.move_type("drop", lambda: api.mod_id)
            """,
        )
        result = load(self.mods)
        verb = result.registries.verbs["move_type"].get("shogi:drop")
        self.assertEqual(verb.value.generate(), "shogi:drops")

    def test_an_exception_while_registering_reports_a_traceback(self):
        # The no-stack-traces rule is about audience, not taste. Stage 4's own table says
        # this reader writes Python — withholding the traceback would be the contract's
        # letter defeating its purpose.
        write_mod(
            self.mods,
            "boom",
            manifest="id: boom:mod\nname: Boom\nversion: 1.0.0\ncode: true\n",
            code="""
            def register(api):
                raise RuntimeError("the mod author made a mistake")
            """,
        )
        result = load(self.mods)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("the mod author made a mistake", result.errors[0].problem)
        self.assertIn("Traceback", result.errors[0].problem)

    def test_an_exception_at_import_time_is_caught(self):
        write_mod(
            self.mods,
            "boom",
            manifest="id: boom:mod\nname: Boom\nversion: 1.0.0\ncode: true\n",
            code="raise ValueError('broken at import')\n",
        )
        result = load(self.mods)
        self.assertIn("broken at import", result.errors[0].problem)

    def test_a_code_mod_without_a_register_function_says_what_to_write(self):
        write_mod(
            self.mods,
            "empty",
            manifest="id: empty:mod\nname: E\nversion: 1.0.0\ncode: true\n",
            code="x = 1\n",
        )
        result = load(self.mods)
        self.assertIn("register", result.errors[0].expected)

    def test_the_vocabulary_freezes_when_the_stage_ends(self):
        # The freeze is structural, and this is the test that proves the *loader* closes it
        # rather than the api merely being capable of closing. A mod stashes its api and
        # calls it after loading; it gets a clear error naming the verb, and nothing is
        # half-registered.
        write_mod(
            self.mods,
            "late",
            manifest="id: late:mod\nname: Late\nversion: 1.0.0\ncode: true\n",
            code="""
            def register(api):
                # Hand the api back out through the one channel a mod really has: a verb it
                # registered. This stands in for a mod that stashes its api and calls it
                # from a hook later in the game.
                api.move_type("early", lambda: api)
            """,
        )
        result = load(self.mods)
        self.assertEqual(result.errors, [])
        self.assertIn("late:early", result.registries.verbs["move_type"])

        stashed = result.registries.verbs["move_type"].get("late:early").value.generate()
        with self.assertRaises(ModApiError) as caught:
            stashed.move_type("toolate", lambda: [])
        self.assertIn("after loading finished", caught.exception.error.problem)
        self.assertNotIn("late:toolate", result.registries.verbs["move_type"])

    def test_a_code_mod_may_span_several_files(self):
        # Without submodule_search_locations the entry is not a package and this dies with
        # "attempted relative import with no known parent package" — forcing every code mod
        # into one file. base:chess hits this at Wave 4: castle and enpassant are not
        # one-liners, and §2.1's own example implies they live somewhere.
        write_mod(
            self.mods,
            "split",
            manifest="id: split:mod\nname: Split\nversion: 1.0.0\ncode: true\n",
            files={"code/castle.py": "def castle_fn():\n    return ['a move']\n"},
            code="""
            from .castle import castle_fn

            def register(api):
                api.move_type("castle", castle_fn, threatens=False)
            """,
        )
        result = load(self.mods)
        self.assertEqual(result.errors, [], self.problems(result))
        verb = result.registries.verbs["move_type"].get("split:castle")
        self.assertEqual(verb.value.generate(), ["a move"])

    def test_a_failed_mod_leaves_nothing_behind_in_sys_modules(self):
        # A half-executed module left in sys.modules would be found and silently reused by
        # the next import of that name, so a mod could fail once and "work" afterwards.
        write_mod(
            self.mods,
            "boom",
            manifest="id: boom:mod\nname: Boom\nversion: 1.0.0\ncode: true\n",
            code="raise ValueError('broken at import')\n",
        )
        load(self.mods)
        self.assertNotIn("onlychess_mod_boom_mod", sys.modules)

    def test_a_verb_collision_is_reported_against_the_file_that_caused_it(self):
        # The api knows the mod but not the file; the loader knows both. Without the
        # re-point this says "<registration>" while the loader is holding the path.
        for folder, mod_id in (("a", "base:one"), ("b", "base:two")):
            dependencies = "" if mod_id == "base:one" else "dependencies:\n  required:\n    base:one: '^1.0'\n"
            write_mod(
                self.mods,
                folder,
                manifest=f"id: {mod_id}\nname: {folder}\nversion: 1.0.0\n{dependencies}code: true\n",
                code="def register(api):\n    api.move_type('castle', lambda: [])\n",
            )
        result = load(self.mods)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].file, "code/__init__.py")
        self.assertIn("already defined by", result.errors[0].problem)

    def test_a_mod_may_register_several_verbs(self):
        write_mod(
            self.mods,
            "many",
            manifest="id: many:mod\nname: Many\nversion: 1.0.0\ncode: true\n",
            code="""
            def register(api):
                api.move_type("hop", lambda: [])
                api.move_type("skip", lambda: [], threatens=False)
            """,
        )
        result = load(self.mods)
        self.assertEqual(result.registries.verbs["move_type"].ids(), ("many:hop", "many:skip"))


class RegisterTests(LoaderTest):
    def test_content_lands_in_the_registry_for_its_type(self):
        data_mod(
            self.mods,
            "m",
            "tiny:mod",
            pieces__blob="type: piece\nid: tiny:blob\n",
            statuses__hex="type: status\nid: tiny:hex\n",
        )
        result = load(self.mods)
        self.assertIn("tiny:blob", result.registries.content["piece"])
        self.assertIn("tiny:hex", result.registries.content["status"])

    def test_a_file_without_an_id_says_what_to_write(self):
        data_mod(self.mods, "m", "tiny:mod", pieces__blob="type: piece\n")
        result = load(self.mods)
        self.assertIn("id:", result.errors[0].expected)

    def test_a_duplicate_id_is_reported_at_its_source_line(self):
        # The registry does not know where an id came from; the file does. Without the
        # re-point, this error would have no line number.
        data_mod(
            self.mods,
            "m",
            "tiny:mod",
            pieces__one="type: piece\nid: tiny:blob\n",
            pieces__two="type: piece\nid: tiny:blob\n",
        )
        result = load(self.mods)
        self.assertEqual(len(result.errors), 1)
        error = result.errors[0]
        self.assertEqual(error.field, "id")
        self.assertEqual(error.file, "pieces/two.yaml")
        self.assertEqual(error.line, 2)

    def test_the_same_id_in_two_content_types_is_not_a_collision(self):
        # A piece and a status may share a name; the registries are separate.
        data_mod(
            self.mods,
            "m",
            "tiny:mod",
            pieces__blob="type: piece\nid: tiny:thing\n",
            statuses__blob="type: status\nid: tiny:thing\n",
        )
        result = load(self.mods)
        self.assertEqual(result.errors, [])

    def test_a_non_text_id_is_rejected_without_a_python_type_name(self):
        data_mod(self.mods, "m", "tiny:mod", pieces__blob="type: piece\nid: 12\n")
        result = load(self.mods)
        self.assertIn("not text", result.errors[0].problem)


class ActivateTests(LoaderTest):
    def test_a_mod_with_a_game_mode_activates(self):
        data_mod(self.mods, "m", "tiny:mod", modes__only=playable_mode("tiny:mod"))
        registries = activate(load(self.mods))
        self.assertIn("tiny:only_mode", registries.content["game_mode"])

    def test_no_game_mode_refuses_to_start(self):
        # The engine's only structural requirement. A game with no mode cannot start.
        data_mod(self.mods, "m", "tiny:mod", pieces__blob="type: piece\nid: tiny:blob\n")
        with self.assertRaises(ModLoadError) as caught:
            activate(load(self.mods))
        self.assertIn("no game mode", caught.exception.errors[0].problem)

    def test_activate_does_not_require_the_base_game(self):
        # Core may never name a mod. "The base game is missing" is not a sentence this
        # engine can say — nor should it: a total conversion replaces base:chess outright
        # and must still boot. The engine requires *a* mode, not a *specific* one.
        data_mod(self.mods, "total", "conversion:mod", modes__only=playable_mode("conversion:mod"))
        registries = activate(load(self.mods))
        self.assertEqual(len(registries.content["game_mode"]), 1)

    def test_activate_refuses_when_anything_failed(self):
        # A mod with any error is disabled whole. Never half-loaded: a chess mod that loads
        # every piece except the queen produces a game that looks fine and is wrong.
        data_mod(self.mods, "m", "tiny:mod", modes__only=playable_mode("tiny:mod"), pieces__bad="type: peice\nid: tiny:b\n")
        with self.assertRaises(ModLoadError):
            activate(load(self.mods))


class RealBaseModsTests(unittest.TestCase):
    """The loader against the base mods D1 actually wrote.

    Not a fixture: these are the 33 files the spec was validated against on paper. This is
    the first time anything has read them with a machine, and it is the only test in this
    wave that could catch the spec and the loader disagreeing.
    """

    def setUp(self):
        self.result = load(REPO_ROOT / "mods")
        self.manifests, self.discover_errors = discover(REPO_ROOT / "mods")

    def test_only_shipped_mods_are_discovered(self):
        # Both fixtures are deliberately absent. The walking skeleton and the Prism Arena proof mod
        # live under tests/fixtures/, so neither reaches a player's mode catalog; a test that wants
        # one stages it explicitly (tests/support.py).
        self.assertEqual(
            [m.mod_id for m in self.manifests], ["base:chess", "base:events", "base:fusion"]
        )
        self.assertEqual(self.discover_errors, [])

    def test_every_content_file_parses(self):
        # Covers base:chess too: parsing happens before the disabled-whole filter, so a
        # syntax error in any of the 33 files D1 wrote would show up here even though
        # base:chess's content does not reach the registries yet.
        parse_errors = [e for e in self.result.errors if e.line is not None]
        self.assertEqual(parse_errors, [], "\n".join(e.format() for e in parse_errors))

    def test_the_siblings_share_the_base_namespace_without_colliding(self):
        # base:fusion and base:events are different mods both defining base:* ids. If the
        # rule were "one namespace per mod", D2's split — required by UC11 — would be
        # illegal, and this would fail.
        self.assertEqual(self.result.registries.content["piece"].get("base:warden").mod_id, "base:fusion")
        self.assertEqual(self.result.registries.content["status"].get("base:poison").mod_id, "base:events")

    def test_base_chess_loads_through_its_declared_code_entry(self):
        # Wave 4 supplies the promised package; no base-game bypass exists.
        # Its content and opaque verbs arrive through the public loader path.
        # — a chess mod with no king looks fine until someone tries to play.
        #
        # When Wave 4 writes base:chess/code/, this whole test goes; it is a description of
        # a temporary state, not a requirement.
        self.assertEqual(self.result.errors, [])
        self.assertIn("base:chess", self.result.mods)
        self.assertEqual(self.result.registries.verbs["move_type"].ids(), ("base:castle", "base:enpassant"))
        self.assertEqual(self.result.registries.content["resource"].get("base:ap").mod_id, "base:chess")

    def test_the_mods_that_do_not_owe_code_load_their_content(self):
        populated = {name for name, reg in self.result.registries.content.items() if len(reg)}
        self.assertEqual(populated, {"ability", "board", "event", "event_pool", "fusion", "game_mode", "piece", "resource", "status", "theme", "hud_layout", "sound"})
        self.assertEqual(self.result.mods, ("base:chess", "base:events", "base:fusion"))


if __name__ == "__main__":
    unittest.main()
