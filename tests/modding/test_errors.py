"""Tests for the error contract.

The contract is a promise to a person who does not write Python, and a promise nobody checks
is a wish. These tests are the check.
"""

from __future__ import annotations

import unittest

from src.modding.errors import ContentError, ModLoadError, did_you_mean, levenshtein, one_of


class LevenshteinTests(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(levenshtein("limit", "limit"), 0)

    def test_dropped_letter(self):
        self.assertEqual(levenshtein("limt", "limit"), 1)

    def test_substitution(self):
        self.assertEqual(levenshtein("qeen", "queen"), 1)

    def test_empty_against_word(self):
        self.assertEqual(levenshtein("", "queen"), 5)

    def test_is_symmetric(self):
        self.assertEqual(levenshtein("not_stat", "not_status"), levenshtein("not_status", "not_stat"))


class DidYouMeanTests(unittest.TestCase):
    KEYS = ("is", "not", "color", "friendly", "tag_any", "primary", "has_status", "not_status", "empty")

    def test_the_error_contracts_own_example(self):
        # loader-lifecycle.md's sample report: unknown key 'not_stat' -> 'not_status'.
        self.assertEqual(did_you_mean("not_stat", self.KEYS), "not_status")

    def test_far_enough_away_gets_no_suggestion(self):
        # A wrong suggestion is worse than none: it sends someone to fix the wrong thing.
        self.assertIsNone(did_you_mean("banana", self.KEYS))

    def test_distance_two_is_included(self):
        self.assertEqual(did_you_mean("frendl", self.KEYS), "friendly")

    def test_no_candidates(self):
        self.assertIsNone(did_you_mean("anything", ()))

    def test_ties_break_deterministically(self):
        # Both are distance 1. A suggestion that changes between runs would make every
        # message untrustworthy, which costs more than the suggestion is worth.
        first = did_you_mean("cat", ("bat", "cot"))
        self.assertEqual(first, did_you_mean("cat", ("cot", "bat")))
        self.assertEqual(first, "bat")


class FormatTests(unittest.TestCase):
    def full_error(self) -> ContentError:
        return ContentError(
            mod_id="base:events",
            file="events/tai_xiu.yaml",
            line=12,
            col=5,
            field="execute[0].filter.not_stat",
            problem="unknown key 'not_stat'",
            expected=one_of(
                ["is", "not", "color", "friendly", "tag_any", "primary", "has_status", "not_status", "empty"]
            ),
            suggestion="not_status",
        )

    def test_reproduces_the_specs_sample_report(self):
        report = self.full_error().format()
        self.assertIn("ERROR  base:events  events/tai_xiu.yaml:12:5", report)
        self.assertIn("field:     execute[0].filter.not_stat", report)
        self.assertIn("problem:   unknown key 'not_stat'", report)
        self.assertIn("expected:  one of", report)
        self.assertIn("did you mean 'not_status'?", report)

    def test_every_contract_field_appears(self):
        # "an error missing any of these is a bug in the loader" — mod id, file, line:col,
        # field, problem, expected.
        report = self.full_error().format()
        for required in ("base:events", "events/tai_xiu.yaml", "12:5", "execute[0]", "not_stat", "expected"):
            self.assertIn(required, report)

    def test_long_expected_wraps_into_a_column(self):
        lines = self.full_error().format().splitlines()
        wrapped = [line for line in lines if line.startswith(" " * 13) and "expected" not in line]
        self.assertTrue(wrapped, "a long option list should wrap rather than run off the terminal")

    def test_location_degrades_when_there_is_no_position(self):
        # A manifest we could not parse has no position. Inventing 0:0 would send someone to
        # look at a line that has nothing wrong with it.
        error = ContentError(mod_id="<mymod>", file="manifest.yaml", problem="not valid YAML")
        self.assertEqual(error.location, "manifest.yaml")
        self.assertNotIn(":0", error.format())

    def test_column_alone_is_omitted_when_the_line_is_unknown(self):
        error = ContentError(mod_id="a:b", file="f.yaml", problem="x", line=4)
        self.assertEqual(error.location, "f.yaml:4")

    def test_optional_lines_are_omitted_not_blank(self):
        report = ContentError(mod_id="a:b", file="f.yaml", problem="x").format()
        self.assertNotIn("field:", report)
        self.assertNotIn("expected:", report)
        self.assertNotIn("did you mean", report)


class OneOfTests(unittest.TestCase):
    def test_sorts_so_the_list_is_stable(self):
        self.assertEqual(one_of(["piece", "board", "ability"]), "one of ability, board, piece")


class ModLoadErrorTests(unittest.TestCase):
    def test_carries_every_error_not_just_the_first(self):
        # The whole point of collect-don't-fail-fast: six typos, one run.
        errors = [ContentError(mod_id="a:b", file=f"{i}.yaml", problem=f"problem {i}") for i in range(6)]
        raised = ModLoadError(errors)
        self.assertEqual(len(raised.errors), 6)
        for i in range(6):
            self.assertIn(f"problem {i}", raised.report())

    def test_the_message_is_the_report(self):
        raised = ModLoadError([ContentError(mod_id="a:b", file="f.yaml", problem="the thing broke")])
        self.assertIn("the thing broke", str(raised))


if __name__ == "__main__":
    unittest.main()
