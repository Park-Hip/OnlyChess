"""Tests for the parse chokepoint.

Two properties here are architecture rather than behaviour, and both fail silently if they
regress — which is exactly why they are tested directly rather than through the loader.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.modding.parse import parse_file, read_yaml, render_path


def _write(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def parse(self, body: str, name: str = "thing.yaml"):
        return parse_file(_write(self.dir, name, body), "test:mod", name)


class Yaml12Tests(TempDirTest):
    """ADR-001's pin, tested on the exact tokens that break under YAML 1.1.

    The Norway problem is not hypothetical for this project: `base:chess`'s own pawn writes
    an `on:` block and `dirs: forward`. Under 1.1 `on` is `True`, and a piece definition
    would grow a `True` key that no schema mentions and no error names.
    """

    def test_on_stays_a_string_key(self):
        parsed, errors = self.parse("type: piece\nid: test:x\non:\n  - trigger: moved\n")
        self.assertEqual(errors, [])
        self.assertIn("on", parsed.tree)
        self.assertNotIn(True, parsed.tree)

    def test_norway_and_friends_stay_strings(self):
        # `no` is Norway's country code; `yes`/`off`/`on` are the same 1.1 booleans.
        parsed, _ = self.parse("type: piece\nid: test:x\ncountries: [no, yes, on, off]\n")
        self.assertEqual(list(parsed.tree["countries"]), ["no", "yes", "on", "off"])

    def test_real_booleans_are_still_booleans(self):
        # The pin must not overshoot: `capture: false` in pawn.yaml has to stay a bool.
        parsed, _ = self.parse("type: piece\nid: test:x\ncapture: false\nlimit: 2\n")
        self.assertIs(parsed.tree["capture"], False)
        self.assertEqual(parsed.tree["limit"], 2)


class PositionTests(TempDirTest):
    """`.lc` survives, and a field path resolves against it.

    S1 spiked this against ruamel; these tests are what stop it regressing once code starts
    touching the tree. A resolver that returns None everywhere would pass every test that
    only checks error *text*.
    """

    def setUp(self):
        super().setUp()
        self.parsed, _ = self.parse(
            "type: piece\n"          # line 1
            "id: test:pawn\n"        # line 2
            "moves:\n"               # line 3
            "  - type: slide\n"      # line 4
            "    limit: 2\n"         # line 5
            "on:\n"                  # line 6
            "  - trigger: moved\n"   # line 7
            "    effect:\n"          # line 8
            "      into: test:queen\n"  # line 9
        )

    def test_top_level_key(self):
        self.assertEqual(self.parsed.position(("id",)), (2, 1))

    def test_position_points_at_the_key_not_the_value(self):
        # An error about `limit` must underline `limit`, not `2`.
        line, col = self.parsed.position(("moves", 0, "limit"))
        self.assertEqual((line, col), (5, 5))

    def test_resolves_three_levels_down_through_a_sequence_index(self):
        # The shape the error contract's own sample uses: execute[0].filter.not_stat.
        self.assertEqual(self.parsed.position(("on", 0, "effect", "into")), (9, 7))

    def test_a_sequence_item_has_a_position(self):
        self.assertEqual(self.parsed.position(("moves", 0)), (4, 5))

    def test_unknown_key_has_a_position(self):
        # The case that decides the design: a schema violation is by definition a key the
        # schema cannot describe, so the resolver must walk the *parsed tree*, not the
        # schema. If this returns None, every unknown-key error loses its line number —
        # which is the single most common non-coder mistake.
        parsed, _ = self.parse("type: piece\nid: test:x\nlimt: 3\n", name="typo.yaml")
        self.assertEqual(parsed.position(("limt",)), (3, 1))

    def test_missing_key_resolves_to_none_rather_than_raising(self):
        # ruamel raises KeyError for a key it has no position for. Uncaught, that would
        # crash the loader on its own error path — while reporting someone else's typo.
        self.assertIsNone(self.parsed.position(("nope",)))

    def test_walking_through_a_missing_parent_is_none_not_a_crash(self):
        self.assertIsNone(self.parsed.position(("nope", 4, "deeper")))

    def test_index_past_the_end_is_none_not_a_crash(self):
        self.assertIsNone(self.parsed.position(("moves", 9, "limit")))


class FieldPathRenderingTests(unittest.TestCase):
    def test_renders_the_error_contracts_own_example(self):
        self.assertEqual(
            render_path(("execute", 0, "filter", "not_stat")),
            "execute[0].filter.not_stat",
        )

    def test_leading_index(self):
        self.assertEqual(render_path((0, "type")), "[0].type")

    def test_single_key(self):
        self.assertEqual(render_path(("id",)), "id")


class ParseFailureTests(TempDirTest):
    def test_syntax_error_reports_a_position(self):
        parsed, errors = self.parse("type: piece\nid: [unclosed\n")
        self.assertIsNone(parsed)
        self.assertEqual(len(errors), 1)
        self.assertIsNotNone(errors[0].line)

    def test_empty_file(self):
        parsed, errors = self.parse("")
        self.assertIsNone(parsed)
        self.assertIn("empty", errors[0].problem)

    def test_a_list_file_is_rejected_in_words_not_type_names(self):
        parsed, errors = self.parse("- one\n- two\n")
        self.assertIsNone(parsed)
        self.assertIn("list", errors[0].problem)
        # The reader does not write Python: no type names in the message.
        self.assertNotIn("CommentedSeq", errors[0].format())
        self.assertNotIn("dict", errors[0].format())

    def test_missing_type_says_what_to_write(self):
        parsed, errors = self.parse("id: test:x\n")
        self.assertIsNone(parsed)
        self.assertIn("type:", errors[0].expected)

    def test_an_error_about_an_absent_field_claims_no_position(self):
        # There is no line to point at — the defect is a line that is not there. Answering
        # 1:1 would name the first line of the file, which in every base mod is a comment,
        # and send the reader to look at something that is not wrong.
        parsed, errors = self.parse("# a comment\nid: test:x\n")
        self.assertIsNone(errors[0].line)
        self.assertEqual(errors[0].location, "thing.yaml")
        self.assertNotIn(":1:1", errors[0].format())

    def test_unknown_type_lists_the_known_ones_and_suggests(self):
        parsed, errors = self.parse("type: peice\nid: test:x\n")
        self.assertIsNone(parsed)
        error = errors[0]
        self.assertEqual(error.suggestion, "piece")
        self.assertIn("piece", error.expected)
        self.assertIn("game_mode", error.expected)
        self.assertEqual(error.field, "type")
        self.assertEqual((error.line, error.col), (1, 1))


class EncodingTests(TempDirTest):
    """A file that is not UTF-8 must be an error, not a crash.

    UnicodeDecodeError is a ValueError, so it escapes the obvious `except OSError` and takes
    the whole load down with a stack trace naming no mod and no file. It is also the single
    likeliest way a real modder's file fails to open: a Windows editor saving as cp1252, and
    one accented character in a `name:` field. The audience it hits is exactly the loader's
    target reader.
    """

    def test_a_non_utf8_file_is_reported_not_raised(self):
        path = self.dir / "latin.yaml"
        path.write_bytes("type: piece\nid: test:x\nname: caf\xe9\n".encode("latin-1"))
        parsed, errors = parse_file(path, "test:mod", "latin.yaml")
        self.assertIsNone(parsed)
        self.assertEqual(len(errors), 1)
        self.assertIn("UTF-8", errors[0].problem)
        self.assertIn("Save As", errors[0].expected)

    def test_a_non_utf8_file_does_not_stop_the_rest_of_the_load(self):
        good = _write(self.dir, "good.yaml", "type: piece\nid: test:ok\n")
        bad = self.dir / "bad.yaml"
        bad.write_bytes("type: piece\nname: caf\xe9\n".encode("latin-1"))
        for path in (bad, good):
            parsed, errors = parse_file(path, "test:mod", path.name)
            self.assertIsInstance(errors, list)

    def test_utf8_content_is_read_correctly(self):
        parsed, errors = self.parse("type: piece\nid: test:x\nname: café ♞\n", name="utf8.yaml")
        self.assertEqual(errors, [])
        self.assertEqual(parsed.tree["name"], "café ♞")


class ReadYamlTests(TempDirTest):
    def test_read_yaml_does_not_require_a_type(self):
        # The manifest is YAML but is not content. It goes through the same reader, which is
        # what stops a second YAML() appearing somewhere and drifting back to 1.1.
        parsed, errors = read_yaml(
            _write(self.dir, "manifest.yaml", "id: test:mod\nname: X\nversion: 1.0.0\n"),
            "test:mod",
            "manifest.yaml",
        )
        self.assertEqual(errors, [])
        self.assertEqual(parsed.tree["id"], "test:mod")


class ErrorBuildingTests(TempDirTest):
    def test_error_from_a_file_carries_the_whole_contract(self):
        parsed, _ = self.parse("type: piece\nid: test:x\nlimt: 3\n")
        error = parsed.error(
            "unknown key 'limt'", field=("limt",), expected="one of limit, dirs", suggestion="limit"
        )
        self.assertEqual(error.mod_id, "test:mod")
        self.assertEqual(error.file, "thing.yaml")
        self.assertEqual((error.line, error.col), (3, 1))
        self.assertEqual(error.field, "limt")
        self.assertIsNotNone(error.expected)


if __name__ == "__main__":
    unittest.main()
