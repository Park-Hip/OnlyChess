"""The loader — enough of the nine stages to read a mod, register it, and hand it over.

Wave 1 implements **1 discover, 3 parse, 4 load code, 7 register, 9 activate**. Wave 2 adds
an opt-in **5 validate** and **8 link** path for the three content types its preview consumes.
The remaining work is not stubbed, because a stub that returns success is a lie that passes tests:

- **2 resolve** (graph, cycles, the originator rule) arrives with the first mod that has a
  dependency. Until then, load order is the tie-break rule — mod id, alphabetically.
- **6 patch** arrives with ADR-002's ops.
- Validation/linking for the other seven content types arrive with their engine consumers.

Unsupported content remains registry-only. That is a real gap and it is recorded here rather
than hidden behind a `def validate(): pass`.

**Errors are collected, not fail-fast.** The loader runs every stage over every mod and
reports everything at once. A non-coder with six typos should learn about six typos, not
run the game six times. The exception is a failure that makes later stages meaningless —
stage 4's freeze — where continuing would only manufacture cascade noise.
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable, Optional

from .api import ModApi, ModApiError
from .errors import ContentError, ModLoadError
from .linking import LinkedContent, link_content
from .parse import CONTENT_SUFFIX, ParsedFile, describe_shape, parse_file, read_yaml
from .registries import Registries, is_valid_id
from .validation import validate_content

MANIFEST_NAME = "manifest.yaml"
CODE_DIR = "code"
CODE_ENTRY = "__init__.py"

#: Manifest fields without which a mod cannot be loaded or attributed (mod-package.md).
REQUIRED_MANIFEST_FIELDS = ("id", "name", "version")


@dataclass(frozen=True)
class Manifest:
    """A mod's identity. Read at stage 1, before any content file is opened."""

    mod_id: str
    name: str
    version: str
    root: Path
    ships_code: bool

    @property
    def code_entry(self) -> Path:
        return self.root / CODE_DIR / CODE_ENTRY


@dataclass
class LoadResult:
    """What a load produced: the registries, who loaded, and everything that went wrong."""

    registries: Registries
    mods: tuple[str, ...] = ()
    errors: list[ContentError] = field(default_factory=list)
    linked: Optional[LinkedContent] = None
    mod_roots: dict[str, Path] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def raise_if_failed(self) -> None:
        if self.errors:
            raise ModLoadError(self.errors)


def discover(mods_dir: Path) -> tuple[list[Manifest], list[ContentError]]:
    """Stage 1 — read every `manifest.yaml`, and nothing else.

    No content files yet: we do not know which mods are enabled, and reporting errors from a
    mod that is about to be disabled is noise about a file the modder may not even own.

    **The one silent skip in the loader is here**: a directory with no manifest is not a
    broken mod, it is not a mod. That is what keeps a stray `README/` or `.git/` from being
    an error. Every other skip in this codebase is a bug.
    """
    manifests: list[Manifest] = []
    errors: list[ContentError] = []

    if not mods_dir.is_dir():
        return manifests, errors

    claimed: dict[str, Manifest] = {}
    for folder in sorted(p for p in mods_dir.iterdir() if p.is_dir()):
        manifest_path = folder / MANIFEST_NAME
        if not manifest_path.is_file():
            continue

        manifest, problems = _read_manifest(manifest_path, folder)
        errors.extend(problems)
        if manifest is None:
            continue

        # Two mods with the same id are not a namespace-sharing question — that is stage 2's
        # originator rule, and it is about *different* mods writing into one namespace. This
        # is one identity claimed twice, usually two versions of a mod installed side by
        # side. Left alone it produces "'mymod:thing' is already defined by mymod:x" with
        # the same name on both sides, naming neither folder. Only the folders tell them
        # apart, so the error is written in folders.
        incumbent = claimed.get(manifest.mod_id)
        if incumbent is not None:
            errors.append(
                ContentError(
                    mod_id=manifest.mod_id,
                    file=f"{folder.name}/{MANIFEST_NAME}",
                    problem=(
                        f"the id '{manifest.mod_id}' is already claimed by the mod in "
                        f"'{incumbent.root.name}/'"
                    ),
                    field="id",
                    expected="one mod per id — remove or rename one of the two folders",
                )
            )
            continue

        claimed[manifest.mod_id] = manifest
        manifests.append(manifest)

    # Ties break by mod id, alphabetically (mod-package.md). Until stage 2 exists this is
    # the whole of load order — deterministic, which is the property that actually matters.
    manifests.sort(key=lambda m: m.mod_id)
    return manifests, errors


def _read_manifest(path: Path, folder: Path) -> tuple[Optional[Manifest], list[ContentError]]:
    """Read one manifest.

    Attribution falls back to the **folder name**: the mod's `id` is exactly the thing we
    failed to read, so naming it is not an option. A modder needs to know which directory to
    open, and that is the only identity we have left.
    """
    fallback = f"<{folder.name}>"
    parsed, errors = read_yaml(path, fallback, MANIFEST_NAME)
    if parsed is None:
        return None, errors

    tree = parsed.tree
    missing = [name for name in REQUIRED_MANIFEST_FIELDS if name not in tree]
    if missing:
        return None, [
            parsed.error(
                "the manifest is missing " + ", ".join(f"`{name}`" for name in missing),
                expected="`id:`, `name:` and `version:`, at minimum",
            )
        ]

    mod_id = tree["id"]
    if not isinstance(mod_id, str) or not is_valid_id(mod_id):
        return None, [
            parsed.error(
                f"'{mod_id}' is not a valid mod id",
                field=("id",),
                expected="`namespace:name`, lowercase letters, digits and underscores only",
            )
        ]

    # From here the mod can be named, so errors stop saying <folder>.
    parsed = ParsedFile(mod_id=mod_id, path=parsed.path, display=parsed.display, tree=tree)

    ships_code = tree.get("code", False)
    if not isinstance(ships_code, bool):
        # `bool(ships_code)` would be the obvious line here and it is a trapdoor. Under the
        # YAML 1.2 pin `code: no` is the *string* "no" — correctly, that is what the pin is
        # for — and `bool("no")` is True. So the natural spelling of false would silently
        # mean true, in the one field the trust model rests on, and the resulting error
        # would quote a `code: true` the modder never wrote.
        #
        # The pin does not cause this; it just stops YAML from hiding it. A type check is
        # what actually closes it, which is the general lesson: 1.2 makes `yes`/`no` honest
        # strings, and every field that wanted a boolean has to say so itself.
        return None, [
            parsed.error(
                f"`code:` is a {describe_shape(ships_code)}, not a true/false value",
                field=("code",),
                expected=(
                    "`code: true` or `code: false`. Note that `yes`, `no`, `on` and `off` "
                    "are ordinary words here, not true and false"
                ),
            )
        ]

    has_code_dir = (folder / CODE_DIR).is_dir()

    if has_code_dir and not ships_code:
        # Hard error, not a warning: the manifest's honesty is the whole trust model. A
        # pure-data mod is genuinely safe to install, and that claim is worth exactly as
        # much as this check. Python cannot be meaningfully sandboxed, so the declaration is
        # not a hint about the mod — it is the only security property on offer.
        return None, [
            parsed.error(
                f"the manifest says `code: false` but the mod has a `{CODE_DIR}/` directory",
                field=("code",),
                expected=(
                    "`code: true` for a mod that ships Python, or no code/ directory. "
                    "Players are told which mods run code, and that promise has to be true"
                ),
            )
        ]

    return (
        Manifest(
            mod_id=mod_id,
            name=str(tree["name"]),
            version=str(tree["version"]),
            root=folder,
            ships_code=ships_code,
        ),
        [],
    )


def parse_content(manifest: Manifest) -> tuple[list[ParsedFile], list[ContentError]]:
    """Stage 3 — read every content file of one mod.

    **Parse before load code**, and the reason is free safety: parsing needs no verbs, so
    doing it first costs nothing, and it means a syntactically broken mod is rejected before
    we execute anyone's Python. Under a trusted local install that is the only safety
    available. Take it.

    The `code/` directory is skipped — it is Python, and stage 4 owns it.
    """
    files: list[ParsedFile] = []
    errors: list[ContentError] = []

    for path in sorted(manifest.root.rglob(f"*{CONTENT_SUFFIX}")):
        if path.name == MANIFEST_NAME and path.parent == manifest.root:
            continue
        if CODE_DIR in path.relative_to(manifest.root).parts:
            continue

        display = path.relative_to(manifest.root).as_posix()
        parsed, problems = parse_file(path, manifest.mod_id, display)
        errors.extend(problems)
        if parsed is not None:
            files.append(parsed)

    return files, errors


def load_code(manifests: list[Manifest], registries: Registries) -> list[ContentError]:
    """Stage 4 — let code mods register their verbs. Then the vocabulary freezes.

    **This is the stage that makes or breaks the dogfooding claim.** `base:chess` registers
    `castle` and `enpassant` here, through exactly the path a third-party mod uses. There is
    no earlier hook and no privileged pre-registration. If core ever registers a verb outside
    this stage, gate G1 fails — which is the point of writing G1.

    Mods live outside `sys.path`, so `code/__init__.py` is loaded from its path rather than
    imported by name. `loader-lifecycle.md` leaves "imported or exec'd?" open; injection made
    the question cosmetic, because the module never reaches back toward `src` either way.
    """
    errors: list[ContentError] = []
    issued: list[ModApi] = []

    for manifest in manifests:
        if not manifest.ships_code:
            continue

        api = ModApi(manifest.mod_id, registries)
        issued.append(api)
        errors.extend(_run_register(manifest, api))

    # The freeze is the end of the stage, not the end of each mod: mods register in order,
    # and a mod may legitimately call api during its own register(). What must not happen is
    # a verb appearing after validation has started.
    for api in issued:
        api._retire()

    return errors


def _run_register(manifest: Manifest, api: ModApi) -> list[ContentError]:
    entry = manifest.code_entry
    if not entry.is_file():
        return [
            ContentError(
                mod_id=manifest.mod_id,
                file=f"{CODE_DIR}/{CODE_ENTRY}",
                problem=f"the manifest says `code: true` but there is no {CODE_DIR}/{CODE_ENTRY}",
                expected=f"a {CODE_DIR}/{CODE_ENTRY} defining `def register(api):`",
            )
        ]

    # Loaded as a *package*, not a lone module. Without `submodule_search_locations` the
    # entry file is not a package, `__path__` is unset, and `from .castle import castle_fn`
    # dies with "attempted relative import with no known parent package" — which would force
    # every code mod into a single file. base:chess hits that at Wave 4, where `castle` and
    # `enpassant` are not one-liners.
    module_name = _module_name(manifest.mod_id)
    spec = importlib.util.spec_from_file_location(
        module_name, entry, submodule_search_locations=[str(entry.parent)]
    )
    if spec is None or spec.loader is None:
        return [
            ContentError(
                mod_id=manifest.mod_id,
                file=f"{CODE_DIR}/{CODE_ENTRY}",
                problem="Python could not load this file",
            )
        ]

    module = importlib.util.module_from_spec(spec)
    # Relative imports resolve through sys.modules, so the package has to be there *before*
    # its own body runs. Removed again on failure: a half-executed module left behind would
    # be found by the next mod's import and silently reused.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        _forget_module(module_name)
        return [_traceback_error(manifest, "importing")]

    register = getattr(module, "register", None)
    if not callable(register):
        return [
            ContentError(
                mod_id=manifest.mod_id,
                file=f"{CODE_DIR}/{CODE_ENTRY}",
                problem="the file does not define a `register` function",
                expected="`def register(api):` — the loader calls it with the mod api",
            )
        ]

    try:
        register(api)
    except ModApiError as misuse:
        # The api knows the mod but not the file; this function knows both. Re-point the
        # error at the source, exactly as register_content does for content — otherwise a
        # verb collision reports "<registration>" while the loader is holding the path.
        return [replace(misuse.error, file=f"{CODE_DIR}/{CODE_ENTRY}")]
    except Exception:
        return [_traceback_error(manifest, "registering")]

    return []


def _module_name(mod_id: str) -> str:
    """A module name for a mod's code, derived from its id rather than its folder.

    The id is the thing guaranteed unique across a load; two folders could share a name in
    different mod directories, and a collision here would mean one mod's code silently
    standing in for another's.
    """
    return "onlychess_mod_" + mod_id.replace(":", "_")


def _forget_module(module_name: str) -> None:
    """Drop a failed mod's module and any submodules it managed to import."""
    for name in [n for n in sys.modules if n == module_name or n.startswith(module_name + ".")]:
        del sys.modules[name]


def _traceback_error(manifest: Manifest, during: str) -> ContentError:
    """Report a code mod's exception with its traceback.

    The no-stack-traces rule in the error contract is about *audience*, not about tracebacks
    being distasteful. This reader writes Python — stage 4's failure table says so outright.
    Withholding the traceback here would be the contract's letter defeating its purpose.
    """
    return ContentError(
        mod_id=manifest.mod_id,
        file=f"{CODE_DIR}/{CODE_ENTRY}",
        problem=f"the mod raised an error while {during}:\n\n" + traceback.format_exc().rstrip(),
    )


def register_content(files: list[ParsedFile], registries: Registries) -> list[ContentError]:
    """Stage 7 — populate the registries.

    **This is where `CLAUDE.md`'s "registries are populated by the loader at runtime"
    becomes real**, and where `@register_event` + an `__init__.py` import list dies.

    Two things stage 7 owes and does not yet do, both waiting on stage 5:

    - **Normalization** (`limit: 3` -> internal `4`; unqualified ids -> qualified). It is
      defined over the *vocabulary*, not over one content type, so it lands when there is a
      vocabulary to define it over.
    - The `id` check below belongs to validate. It is here because registration needs a key
      and the honest alternative is a `KeyError`.
    """
    errors: list[ContentError] = []

    for parsed in files:
        if "id" not in parsed.tree:
            errors.append(
                parsed.error(
                    "the file does not have an id",
                    expected="an `id:` line, in the form `namespace:name`",
                )
            )
            continue

        entry_id = parsed.tree["id"]
        if not isinstance(entry_id, str):
            errors.append(
                parsed.error(
                    f"the id is a {describe_shape(entry_id)}, not text",
                    field=("id",),
                    expected="an `id:` line, in the form `namespace:name`",
                )
            )
            continue

        error = registries.content[parsed.content_type].add(entry_id, parsed, parsed.mod_id)
        if error is not None:
            # The registry does not know where the id came from; the file does. Re-point the
            # error at the source line so the modder gets a place to stand.
            errors.append(
                parsed.error(error.problem, field=("id",), expected=error.expected)
            )

    return errors


def load(
    mods_dir: Path,
    *,
    enabled_mod_ids: Optional[Iterable[str]] = None,
    validate: bool = False,
    link: bool = False,
) -> LoadResult:
    """Run the loader over enabled mods, optionally including Wave 2 validation/linking.

    Returns a result rather than raising, so a caller can report every error at once. See
    `activate` for the check that decides whether the game can start. `validate` and `link`
    are explicit until every registered content type has an engine consumer; the walking
    skeleton enables both and the Wave 1 registry-contract tests leave both disabled.
    """
    registries = Registries()
    manifests, errors = discover(mods_dir)
    requested = set(enabled_mod_ids) if enabled_mod_ids is not None else None
    if requested is not None:
        found = {manifest.mod_id for manifest in manifests}
        for mod_id in sorted(requested - found):
            errors.append(
                ContentError(
                    mod_id="<engine>",
                    file="<startup>",
                    problem=f"enabled mod '{mod_id}' is not installed",
                    expected="an id from a discovered mod manifest",
                )
            )
        manifests = [manifest for manifest in manifests if manifest.mod_id in requested]

    files: list[ParsedFile] = []
    for manifest in manifests:
        parsed, problems = parse_content(manifest)
        files.extend(parsed)
        errors.extend(problems)

    errors.extend(load_code(manifests, registries))

    # Wave 2 is the first consumer of content schemas.  The legacy Wave 1 loader contract
    # intentionally remains raw until a caller asks for a linked playable slice; otherwise
    # its registry-only tests would start claiming unsupported types were playable.
    if validate:
        errors.extend(validate_content(files))

    # A mod with any error is disabled whole, so its content never reaches the registries in
    # the first place — but a mod can only be known to be broken once every stage before
    # this one has run, which is why the filter is here and not at each stage.
    broken = {error.mod_id for error in errors}
    errors.extend(register_content([f for f in files if f.mod_id not in broken], registries))

    # Registration itself can break a previously clean mod (a duplicate id), and a code mod
    # may have registered verbs before raising. Both mean the survivor set shrank after the
    # filter above, so take back what a now-broken mod already got in.
    for mod_id in {error.mod_id for error in errors}:
        registries.drop(mod_id)

    linked = None
    if link:
        linked, link_errors = link_content(registries)
        errors.extend(link_errors)
        for mod_id in {error.mod_id for error in link_errors}:
            registries.drop(mod_id)

    loaded = tuple(m.mod_id for m in manifests if m.mod_id not in {e.mod_id for e in errors})
    return LoadResult(
        registries=registries,
        mods=loaded,
        errors=errors,
        linked=linked,
        mod_roots={manifest.mod_id: manifest.root for manifest in manifests},
    )


def activate(result: LoadResult) -> Registries:
    """Stage 9 — hand the populated registries to the game, or refuse to start.

    **The engine's only structural requirement: at least one `game_mode` is registered.** A
    game with no mode cannot start, and a mode names a board, so this subsumes the older
    "at least one board layout" rule rather than replacing it.

    Note what this deliberately is *not*: a requirement that `base:chess` loaded. Core may
    never name a mod, so "the base game is missing" is not a sentence this engine can say —
    nor should it, since a total conversion replaces `base:chess` outright and must still
    boot. The engine requires *a* mode, not a *specific* one.
    """
    result.raise_if_failed()

    if not result.registries.content["game_mode"]:
        raise ModLoadError(
            [
                ContentError(
                    mod_id="<engine>",
                    file="<startup>",
                    problem="no game mode is available, so there is nothing to play",
                    expected=(
                        "at least one enabled mod defining `type: game_mode`, which names "
                        "the board and event pools to play with"
                    ),
                )
            ]
        )

    return result.registries
