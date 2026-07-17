"""The error contract — mod id · file · line:col · field · problem · expected.

Every content error carries those six things. `loader-lifecycle.md` states it without
qualification: "an error missing any of these is a bug in the loader."

This module exists before any code that produces an error, on purpose. `file:line:col` is
architecture, not a formatting choice — a loader that parses to plain dicts and bolts
positions on later has to re-parse every file at error time to recover what it threw away.
E1 §3.1 is the standing lesson about deferred verification; this is that lesson applied.

**The reader does not write Python.** That single fact is the whole design brief. It rules
out a stack trace, a type name, a schema fragment, and the word "deserialize". It also rules
out being terse: `expected` lists the valid options, because a modder cannot go read a
registry to find them.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Iterable, Optional

#: Suggest a correction only when the typo is this close. Levenshtein distance 2 is the
#: spec's number: far enough to catch a doubled or dropped letter, near enough that
#: `not_stat` -> `not_status` lands and two unrelated keys never do.
MAX_SUGGESTION_DISTANCE = 2

#: Where the wrapped `expected:` continuation lines line up, so the options read as a
#: column rather than as prose. Matches the sample report in loader-lifecycle.md.
_LABEL_WIDTH = len("  expected:  ")
_REPORT_WIDTH = 78


def levenshtein(a: str, b: str) -> int:
    """Edit distance between two strings.

    Iterative two-row DP. Content key sets are tens of entries at most, so the naive
    version is not worth optimising past this.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    previous = list(range(len(b) + 1))
    for i, a_char in enumerate(a, start=1):
        current = [i]
        for j, b_char in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,  # deletion
                    current[j - 1] + 1,  # insertion
                    previous[j - 1] + (a_char != b_char),  # substitution
                )
            )
        previous = current
    return previous[-1]


def did_you_mean(word: str, candidates: Iterable[str]) -> Optional[str]:
    """The nearest candidate within `MAX_SUGGESTION_DISTANCE`, or None.

    `loader-lifecycle.md` calls this "a requirement, not a nicety", and plausibly the
    highest-value feature in the loader: the dominant non-coder error is a misspelling, and
    the difference between "unknown key 'not_stat'" and "did you mean 'not_status'?" is the
    difference between a fixed file and a closed tab.

    Ties break alphabetically so the suggestion is deterministic. A suggestion that changes
    between runs would be worse than none — it would make the message untrustworthy.
    """
    ranked = sorted(
        ((levenshtein(word, candidate), candidate) for candidate in candidates),
        key=lambda pair: (pair[0], pair[1]),
    )
    if not ranked:
        return None
    distance, best = ranked[0]
    return best if distance <= MAX_SUGGESTION_DISTANCE else None


def one_of(options: Iterable[str]) -> str:
    """Render a choice set the way the error contract's `expected:` line does."""
    return "one of " + ", ".join(sorted(options))


@dataclass(frozen=True)
class ContentError:
    """One thing wrong with one mod's content, told to someone who does not write Python.

    Three fields are `Optional`, and each absence is a specific, defensible case rather than
    laziness:

    - `line`/`col` — a manifest we could not parse at all has no position to report, and a
      value patched in by another mod has no position *in this file*. ADR-003 closes the
      second case by having the patch stage stamp provenance; until stage 6 exists, the
      honest answer for a positionless error is to omit the position, not to invent 0:0.
    - `field` — a YAML syntax error happens below the level at which fields exist. There is
      no field path because the parser never got far enough to build one.
    - `expected` — only meaningful where a closed set of valid values exists. "The file is
      not a mapping" has no option list, and padding one in would be noise.

    `suggestion` is not in the contract's six; it is the did-you-mean line, which is additive.
    """

    mod_id: str
    file: str
    problem: str
    line: Optional[int] = None
    col: Optional[int] = None
    field: Optional[str] = None
    expected: Optional[str] = None
    suggestion: Optional[str] = None

    @property
    def location(self) -> str:
        """`file:line:col`, degrading to `file:line` or `file` when a position is unknown."""
        if self.line is None:
            return self.file
        if self.col is None:
            return f"{self.file}:{self.line}"
        return f"{self.file}:{self.line}:{self.col}"

    def format(self) -> str:
        """The report block for this error, in the shape loader-lifecycle.md specifies."""
        lines = [f"ERROR  {self.mod_id}  {self.location}"]
        if self.field is not None:
            lines.append(f"  field:     {self.field}")
        lines.append(f"  problem:   {self.problem}")
        if self.expected is not None:
            lines.append(
                textwrap.fill(
                    self.expected,
                    width=_REPORT_WIDTH,
                    initial_indent="  expected:  ",
                    subsequent_indent=" " * _LABEL_WIDTH,
                )
            )
        if self.suggestion is not None:
            lines.append(f"  did you mean '{self.suggestion}'?")
        return "\n".join(lines)


class ModLoadError(Exception):
    """Raised when loading finished with errors. Carries every one of them.

    Not fail-fast, and that is an ergonomics requirement rather than a nicety: fail-fast
    means a non-coder with six typos runs the game six times and each run tells them about
    one. That loop is the difference between a modding system someone uses and one they
    abandon.

    The exceptions the spec allows are the stages that make later stages meaningless — a
    dependency cycle (stage 2) or a frozen-vocabulary failure (stage 4) — because everything
    after them would be cascade noise rather than information.
    """

    def __init__(self, errors: list[ContentError]):
        self.errors = list(errors)
        super().__init__(self.report())

    def report(self) -> str:
        """Every error, in one pass, separated by a blank line."""
        return "\n\n".join(error.format() for error in self.errors)
