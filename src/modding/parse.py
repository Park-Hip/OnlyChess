"""Stage 3 — the one chokepoint every content file is read through.

Two things happen here that cannot happen anywhere else:

**The YAML 1.2 pin (ADR-001).** Under YAML 1.1, bare `on`, `no`, and `yes` parse as booleans
— the Norway problem. `base:chess`'s own pawn writes `dirs: forward` and an `on:` block, so
this is not hypothetical for us. The version is pinned explicitly below rather than left to
ruamel's default, because a default is a thing that can change under you.

**Source positions.** Round-trip mode returns `CommentedMap`/`CommentedSeq` carrying `.lc`
line/column data. Plain-dict parsing discards it irrecoverably, and no validator can give it
back: a `dict` does not know it came from line 12. Everything downstream that wants to say
`file:line:col` depends on this function not throwing that away — which is why `ParsedFile`
holds the position-bearing tree rather than a converted copy.

**On "actively reject stock PyYAML".** `loader-lifecycle.md` asks for that check here. It
cannot live here: S1 confirmed `import yaml` succeeds and always will, since PyYAML is
installed as a transitive dependency, so a runtime guard would be checking a condition that
is never false. ADR-003 moves it to a static check over what `src/` imports —
`tests/modding/test_gates.py`. The intent is enforced; the location the spec guessed was
wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

from ruamel.yaml import YAML
from ruamel.yaml.error import MarkedYAMLError

from .errors import ContentError, did_you_mean, one_of
from .registries import CONTENT_TYPES

#: A field path segment is a mapping key or a sequence index, which is exactly what makes
#: `execute[0].filter.not_stat` expressible as data rather than as string surgery.
Segment = Union[str, int]
FieldPath = tuple[Segment, ...]

#: Content lives in `.yaml` files. `.yml` is not accepted: two spellings for one thing is a
#: question every modder would have to ask, and the answer would never be interesting.
CONTENT_SUFFIX = ".yaml"


def render_path(path: FieldPath) -> str:
    """Render a field path the way the error contract prints it.

    `("execute", 0, "filter", "not_stat")` -> `execute[0].filter.not_stat`
    """
    out = ""
    for segment in path:
        if isinstance(segment, int):
            out += f"[{segment}]"
        elif out:
            out += f".{segment}"
        else:
            out = str(segment)
    return out


def _reader() -> YAML:
    """A round-trip reader pinned to the YAML 1.2 core schema.

    `typ="rt"` is what retains `.lc`; `version` is what keeps `on` a string. Both are
    load-bearing and neither is obvious from the call site, which is why there is exactly
    one of these in the codebase.
    """
    yaml = YAML(typ="rt")
    yaml.version = (1, 2)
    return yaml


@dataclass(frozen=True)
class Provenance:
    """The source location of a field supplied by a patch."""

    mod_id: str
    file: str
    line: Optional[int]
    col: Optional[int]


@dataclass
class ParsedFile:
    """One content file, its position data intact.

    `display` is the path the *modder* sees — relative to the mod root, because an absolute
    path from someone else's machine is noise in an error message. `path` is the real one.
    """

    mod_id: str
    path: Path
    display: str
    tree: Any  # CommentedMap — typed loosely; ruamel's stubs do not describe .lc
    provenance: dict[FieldPath, Provenance] = field(default_factory=dict)

    @property
    def content_type(self) -> str:
        return self.tree["type"]

    def position(self, field: FieldPath = ()) -> Optional[tuple[int, int]]:
        """1-based `(line, col)` of a field in this file, or None if it has none.

        Returns the position of the **key token**, not its value, so an error about
        `not_stat` underlines `not_stat`.

        None is a real answer rather than a failure. A field can be absent from the source
        for a good reason — ADR-003's case is a value written by another mod's patch, which
        has a position, but in the *patch's* file. Stage 6 stamps that provenance; this
        resolver reports what it can see and lets the caller consult provenance second.

        **The empty path has no position, and says so.** An error about the file as a whole
        — a missing `type:`, a manifest with no `name:` — is about a line that is not there.
        Answering `1:1` would name the first line of the file, which in every base mod is a
        comment, and send the reader to look at something that is not wrong. That is the
        rule this module states for itself: the honest answer for a positionless error is to
        omit the position, not to invent one.

        ruamel raises `KeyError` for a key it has no position for, which is a footgun on the
        loader's own error path: the resolver would crash while trying to report someone
        else's typo. Caught here, once, rather than at every call site.
        """
        if not field:
            return None

        node = self.tree
        for segment in field[:-1]:
            try:
                node = node[segment]
            except (KeyError, IndexError, TypeError):
                return None

        lc = getattr(node, "lc", None)
        if lc is None:
            return None

        last = field[-1]
        try:
            raw = lc.item(last) if isinstance(last, int) else lc.key(last)
        except (KeyError, IndexError, TypeError, AttributeError):
            return None
        return _one_based(raw)

    def error(
        self,
        problem: str,
        *,
        field: FieldPath = (),
        expected: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> ContentError:
        """Build a contract-complete error against this file.

        The position is looked up rather than passed in, which is the point: it makes
        "carries `file:line:col`" the path of least resistance instead of a rule someone has
        to remember at every raise site.
        """
        position = self.position(field)
        source = self._provenance_for(field) if position is None else None
        return ContentError(
            mod_id=source.mod_id if source else self.mod_id,
            file=source.file if source else self.display,
            problem=problem,
            line=position[0] if position else (source.line if source else None),
            col=position[1] if position else (source.col if source else None),
            field=render_path(field) if field else None,
            expected=expected,
            suggestion=suggestion,
        )

    def stamp_provenance(self, path: FieldPath, source: Provenance) -> None:
        """Record the patch location for a field that did not exist in this file."""
        self.provenance[path] = source

    def _provenance_for(self, field: FieldPath) -> Optional[Provenance]:
        """Use the closest patched ancestor when a key has no YAML location."""
        for size in range(len(field), -1, -1):
            source = self.provenance.get(field[:size])
            if source is not None:
                return source
        return None


def _one_based(raw: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    """ruamel counts lines and columns from 0; humans and editors count from 1.

    The off-by-one is invisible in testing (line 4 vs 5 both look plausible) and infuriating
    in use, so the conversion happens once, here, rather than at each formatting site.
    """
    if raw is None:
        return None
    line, col = raw
    return line + 1, col + 1


def read_yaml(path: Path, mod_id: str, display: str) -> tuple[Optional[ParsedFile], list[ContentError]]:
    """Read one YAML file into a position-bearing tree. No content rules applied.

    Split out from `parse_file` because the manifest is YAML too, and it needs the same 1.2
    pin and the same positions — but it has no `type:`, since a manifest is not content. One
    reader, two callers, rather than a second `YAML()` somewhere that quietly drifts to 1.1.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Not an OSError — UnicodeDecodeError is a ValueError, so it escapes the obvious
        # `except OSError` and takes the whole load down with a stack trace naming no mod.
        # It is also the single likeliest way a real modder's file fails to open: a Windows
        # editor saving as cp1252, and one accented character in a `name:` field.
        return None, [
            ContentError(
                mod_id=mod_id,
                file=display,
                problem="the file is not saved as UTF-8 text",
                expected=(
                    "the file re-saved with UTF-8 encoding — most editors offer this in "
                    "Save As, next to the file name"
                ),
            )
        ]
    except OSError as unreadable:
        return None, [
            ContentError(
                mod_id=mod_id,
                file=display,
                # strerror is None for some OSErrors; the exception itself always says
                # something, and "cannot read the file: None" says nothing.
                problem=f"cannot read the file: {unreadable.strerror or unreadable}",
            )
        ]

    try:
        tree = _reader().load(text)
    except MarkedYAMLError as broken:
        mark = broken.problem_mark or broken.context_mark
        return None, [
            ContentError(
                mod_id=mod_id,
                file=display,
                problem=(broken.problem or "the file is not valid YAML").strip(),
                # ruamel's marks are 0-based like .lc, and for the same reason.
                line=mark.line + 1 if mark else None,
                col=mark.column + 1 if mark else None,
            )
        ]

    if tree is None:
        return None, [ContentError(mod_id=mod_id, file=display, problem="the file is empty")]

    if not isinstance(tree, dict):
        return None, [
            ContentError(
                mod_id=mod_id,
                file=display,
                problem=f"the file is a {describe_shape(tree)}, not a block of settings",
                expected="a file of `key: value` lines, starting with `type:` and `id:`",
            )
        ]

    return ParsedFile(mod_id=mod_id, path=path, display=display, tree=tree), []


def parse_file(path: Path, mod_id: str, display: str) -> tuple[Optional[ParsedFile], list[ContentError]]:
    """Read one content file and check it declares a known type.

    Returns the file, or the errors that stopped it — never both: a file either parsed into
    something with a known type, or it did not.
    """
    parsed, errors = read_yaml(path, mod_id, display)
    if parsed is None:
        return None, errors

    tree = parsed.tree
    if "type" not in tree:
        return None, [
            parsed.error(
                "the file does not say what kind of content it is",
                expected=f"a `type:` line naming {one_of(CONTENT_TYPES)}",
            )
        ]

    declared = tree["type"]
    if declared not in CONTENT_TYPES:
        return None, [
            parsed.error(
                f"unknown type '{declared}'",
                field=("type",),
                expected=one_of(CONTENT_TYPES),
                suggestion=did_you_mean(str(declared), CONTENT_TYPES),
            )
        ]

    return parsed, []


def describe_shape(value: Any) -> str:
    """Name a YAML shape in words a modder would recognise, never a Python type name.

    `NoneType`, `int`, `CommentedSeq` are the vocabulary of the person who wrote the loader,
    not the person reading the error. The contract rules them out by ruling out the audience
    that would find them useful.
    """
    if isinstance(value, bool):
        return "yes/no value"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "line of text"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "block of settings"
    return "value"
