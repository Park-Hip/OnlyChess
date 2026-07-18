"""S4 — the standing gates. `CLAUDE.md`'s invariants, made executable.

`migration-plan.md` §7 is blunt about why these exist:

> **`CLAUDE.md`'s invariants are architectural, not behavioural, so no test in this plan
> checks them.** Every one of these passes the full suite *and* the oracle:
>
> - `if piece_id == "base:queen"` in core
> - core registering `castle` itself instead of `base:chess` registering it
> - a verb added on speculation that no content earns
> - the `api` object bypassed by reaching into a registry directly
>
> That is the entire point of the project, invisible to every check planned so far. **The
> fix is not a reviewer — it is to make the invariants executable.**

That is this project's own philosophy applied to itself: we don't police the prime
directive, we make the prime directive checkable. The measured case for it is that Gate 3
was a review pass, it found nine defects, and **none of the three that mattered** — review
catches consistency, only contact with reality catches correspondence.

They are written now, while the seam is one wave old, because a retrofitted check finds
violations after they are load-bearing.
"""

from __future__ import annotations

import ast
import re
import tempfile
import unittest
from pathlib import Path

from src.modding.loader import load
from src.modding.registries import Registries

from .builders import write_mod

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The directories that must never name content. `src/engine/` does not exist yet — it
#: arrives in Wave 3 — and is listed now so the gate covers it the day it appears rather
#: than the day someone remembers to add it.
CORE_DIRS = ("src/modding", "src/engine")


def core_files() -> list[Path]:
    return sorted(
        path
        for directory in CORE_DIRS
        for path in (REPO_ROOT / directory).rglob("*.py")
        if "__pycache__" not in path.parts
    )


class G1DogfoodingTests(unittest.TestCase):
    """**Disable a code mod → its verbs are gone.** *The base game is a mod.*

    The claim under test is `CLAUDE.md`'s: *"The base mod gets no privileges, no private
    APIs, no shortcuts."* Today that is a promise nobody can check. This makes it a test.

    **This gate is deliberately half-armed, and saying so is the point.** Wave 4 is where
    `base:chess` registers `castle` and `enpassant`, so the specific check §7 names —
    *disable `base:chess`, assert `castle` is not a registered move type* — cannot be
    written yet. What is written here is the two halves that can be:

    1. Core, loading nothing, registers no verbs at all. That is the *stronger* form of the
       gate and it is armed right now: if core ever registers `castle` itself, this fails.
    2. The disable mechanism works, proven against a fixture code mod.

    Wave 4 adds the third leg and points leg 2 at `base:chess`. Until then, a green G1 does
    not yet prove the dogfooding claim — it proves core is not cheating.
    """

    def test_core_alone_registers_no_verbs(self):
        # The strong form. Every verb must come from a mod's register(api); there is no
        # engine-side default vocabulary that content cannot also reach.
        with tempfile.TemporaryDirectory() as empty:
            result = load(Path(empty))
        self.assertEqual(result.registries.verb_ids(), ())

    def test_a_fresh_registry_has_no_verbs(self):
        # Import-time registration would show up here. @register_event fired on import;
        # that is the anti-pattern the loader replaces, and this is the tripwire.
        self.assertEqual(Registries().verb_ids(), ())

    def test_disabling_the_mod_that_owns_a_verb_removes_the_verb(self):
        # The mechanism §7's G1 depends on. Wave 4 re-points this at base:chess/castle.
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp)
            write_mod(
                mods,
                "verbmod",
                manifest="id: verbmod:x\nname: V\nversion: 1.0.0\ncode: true\n",
                code="def register(api):\n    api.move_type('special', lambda: [])\n",
            )
            with_mod = load(mods)
            self.assertIn("verbmod:special", with_mod.registries.verbs["move_type"])

            (mods / "verbmod" / "manifest.yaml").unlink()  # disable it
            without_mod = load(mods)
            self.assertNotIn("verbmod:special", without_mod.registries.verbs["move_type"])

    def test_disabling_base_chess_removes_its_castle_verb(self):
        with_base = load(REPO_ROOT / "mods", enabled_mod_ids=("base:chess",))
        without_base = load(REPO_ROOT / "tests" / "fixtures", enabled_mod_ids=("skeleton:demo",))
        self.assertIn("base:castle", with_base.registries.verbs["move_type"])
        self.assertNotIn("base:castle", without_base.registries.verbs["move_type"])


class G2CoreNamesNoContentTests(unittest.TestCase):
    """**No content ID literal in core.** *Core may never name specific content.*

    `CLAUDE.md`: core may never `name specific content (if piece_code == "Q", if event_key
    == "tai_xiu")`. §7 calls this gate "brutal, mechanical" — it is, and that is the value.

    **Why an AST walk rather than a grep.** Comments and docstrings in core are full of
    `base:chess` and they should be: explaining *why* a rule exists is not the same as
    *acting* on a piece's identity. A grep cannot tell those apart and would either fail on
    prose or force the prose out, and the prose is how the next person learns why any of
    this is shaped the way it is. So the gate reads executable string literals only —
    exactly where the violation would live.
    """

    #: The spec allows "a narrow allowlist for error-message examples". Narrow means this
    #: narrow: the ID *grammar*, which names no real content, and which the error contract
    #: has to be able to quote — a modder who cannot look up a registry needs to be told the
    #: shape. Adding a real id here would be the violation, not an exemption from it.
    ALLOWED = frozenset({"namespace:name"})

    ID_LITERAL = re.compile(r"\b[a-z0-9_]+:[a-z0-9_]+\b")

    def string_literals(self, tree: ast.AST) -> list[tuple[int, str]]:
        """Every string constant that is not a docstring."""
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                body = getattr(node, "body", [])
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    if isinstance(body[0].value.value, str):
                        docstrings.add(id(body[0].value))

        return [
            (node.lineno, node.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ]

    def test_core_contains_no_content_id_literal(self):
        violations = []
        for path in core_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for line, text in self.string_literals(tree):
                for found in self.ID_LITERAL.findall(text):
                    if found not in self.ALLOWED:
                        violations.append(f"{path.relative_to(REPO_ROOT)}:{line} names '{found}'")

        self.assertEqual(
            violations,
            [],
            "core may never name content — that is the signal a capability is missing from "
            "the engine:\n  " + "\n  ".join(violations),
        )

    def test_the_gate_would_catch_the_violation_it_exists_for(self):
        # A gate nobody has seen fail is a hope. This is the exact line CLAUDE.md names.
        tree = ast.parse('def f(piece_id):\n    return piece_id == "base:queen"\n')
        found = [
            match
            for _, text in self.string_literals(tree)
            for match in self.ID_LITERAL.findall(text)
        ]
        self.assertEqual(found, ["base:queen"])

    def test_the_gate_does_not_fire_on_prose(self):
        # If it did, the pressure would be to delete the explanation rather than the
        # violation — and the explanations are the most valuable thing in these files.
        tree = ast.parse('"""base:chess registers castle through the public path."""\n')
        self.assertEqual(self.string_literals(tree), [])


class G3VocabularyIsEarnedTests(unittest.TestCase):
    """**A golden list of registered verbs.** *Vocabulary is earned.*

    `CLAUDE.md`: *"Add a verb when real content cannot be expressed without it — never on
    speculation. Generality no content exercises is dead weight that constrains every future
    refactor."*

    This gate cannot decide whether a verb is earned — only a human can. What it does is put
    the question **in the diff**, where it cannot be skipped: adding a verb means editing
    this list, and editing this list means someone has to type the justification next to it.
    """

    #: Every verb the base game registers, and what earned it. Empty is the correct value
    #: today: `base:chess` declares `code: true` and will register `castle` and `enpassant`
    #: at Wave 4, but has not written them yet. The first entries land with that wave.
    GOLDEN: tuple[str, ...] = ("move_type:base:castle", "move_type:base:enpassant")

    def test_the_registered_vocabulary_matches_the_golden_list(self):
        result = load(REPO_ROOT / "mods")
        self.assertEqual(
            result.registries.verb_ids(),
            self.GOLDEN,
            "a verb was added or removed. If added: what content could not be expressed "
            "without it? Answer that here, then update GOLDEN.",
        )

    def test_the_verb_kinds_are_not_speculative(self):
        # Same rule, one level up. `move_type` is earned by base:chess needing castle and
        # enpassant. Effects, conditions, selectors and triggers are named by the specs but
        # have no registrant until Wave 5 — and a kind is additive, so deferring costs
        # nothing while speculating constrains every later refactor.
        from src.modding.registries import VERB_KINDS

        self.assertEqual(VERB_KINDS, ("move_type",))


class YamlChokepointTests(unittest.TestCase):
    """**Core imports no YAML library except through the chokepoint.**

    `loader-lifecycle.md` asks the parse stage to "actively reject stock PyYAML". ADR-003
    records why it cannot: `import yaml` succeeds and always will, since PyYAML is installed
    as a transitive dependency, so a runtime guard would be checking a condition that is
    never false.

    The intent is real, though — ADR-001 says someone will eventually `import yaml` out of
    habit and silently reintroduce YAML 1.1's Norway problem, and `base:chess`'s own pawn
    has an `on:` block that would break. So the check is static, over what core imports, and
    it lands here rather than nowhere.
    """

    CHOKEPOINT = "src/modding/parse.py"

    def imported_modules(self, path: Path) -> set[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(node.module.split(".")[0])
        return names

    def test_nothing_in_core_imports_stock_pyyaml(self):
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path in core_files()
            if "yaml" in self.imported_modules(path)
        ]
        self.assertEqual(
            offenders,
            [],
            "stock PyYAML is YAML 1.1: bare `on`/`no`/`yes` become booleans, and the base "
            "pawn has an `on:` block. Use src/modding/parse.py.",
        )

    def test_only_the_chokepoint_imports_ruamel(self):
        # One reader, one place. A second YAML() elsewhere is how the 1.2 pin gets lost —
        # not by anyone deciding against it, but by nobody knowing it was a decision.
        offenders = [
            str(path.relative_to(REPO_ROOT))
            for path in core_files()
            if "ruamel" in self.imported_modules(path)
            and path.relative_to(REPO_ROOT).as_posix() != self.CHOKEPOINT
        ]
        self.assertEqual(offenders, [])

    def test_the_chokepoint_pins_yaml_12(self):
        # The pin is load-bearing and invisible: without it everything still parses, and one
        # key in one file quietly becomes a boolean.
        source = (REPO_ROOT / self.CHOKEPOINT).read_text(encoding="utf-8")
        self.assertIn("yaml.version = (1, 2)", source)


if __name__ == "__main__":
    unittest.main()
