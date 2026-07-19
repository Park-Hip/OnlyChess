"""The nine-stage, data-first mod loader.

The loader is the enforcement point for the public mod contract: dependency order precedes code
registration, vocabulary freezes before validation, patches land before normalization, and nothing
reaches the engine with an unresolved content reference.
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
from .patching import apply_patches
from .parse import CONTENT_SUFFIX, ParsedFile, describe_shape, parse_file, read_yaml
from .registries import Registries, is_valid_id, qualify
from .validation import validate_assets, validate_content

MANIFEST_NAME = "manifest.yaml"
CODE_DIR = "code"
CODE_ENTRY = "__init__.py"

#: Manifest fields without which a mod cannot be loaded or attributed (mod-package.md).
REQUIRED_MANIFEST_FIELDS = ("id", "name", "version")
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class Manifest:
    """A mod's identity. Read at stage 1, before any content file is opened."""

    mod_id: str
    name: str
    version: str
    root: Path
    ships_code: bool
    engine: str | None = None
    required_dependencies: dict[str, str] = field(default_factory=dict)
    optional_dependencies: dict[str, str] = field(default_factory=dict)

    @property
    def code_entry(self) -> Path:
        return self.root / CODE_DIR / CODE_ENTRY


@dataclass(frozen=True)
class ModInfo:
    """Read-only installed-mod metadata safe to expose to presentation code."""

    mod_id: str
    name: str
    ships_code: bool
    #: The manifest's declared version. Exposed because a saved game has to record what it was
    #: played against, and "which mods" is not enough — the same mod at a different version can
    #: describe a different game.
    version: str = ""


@dataclass
class LoadResult:
    """What a load produced: the registries, who loaded, and everything that went wrong."""

    registries: Registries
    mods: tuple[str, ...] = ()
    installed: tuple[ModInfo, ...] = ()
    errors: list[ContentError] = field(default_factory=list)
    linked: Optional[LinkedContent] = None
    mod_roots: dict[str, Path] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

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
    parsed = ParsedFile(
        mod_id=mod_id,
        path=parsed.path,
        display=parsed.display,
        tree=tree,
        provenance=parsed.provenance,
    )

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

    dependencies, dependency_errors = _read_dependencies(parsed)
    if dependency_errors:
        return None, dependency_errors

    engine = tree.get("engine")
    if engine is not None and (not isinstance(engine, str) or not _valid_range(engine)):
        return None, [
            parsed.error("must be a version range", field=("engine",), expected="a caret range such as `^1.0`")
        ]

    return (
        Manifest(
            mod_id=mod_id,
            name=str(tree["name"]),
            version=str(tree["version"]),
            root=folder,
            ships_code=ships_code,
            engine=engine,
            required_dependencies=dependencies["required"],
            optional_dependencies=dependencies["optional"],
        ),
        [],
    )


def _read_dependencies(parsed: ParsedFile) -> tuple[dict[str, dict[str, str]], list[ContentError]]:
    """Validate the manifest's dependency maps before graph resolution needs them."""
    raw = parsed.tree.get("dependencies", {})
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        return {"required": {}, "optional": {}}, [
            parsed.error("must be a block of dependency maps", field=("dependencies",), expected="`dependencies: { required: {}, optional: {} }`")
        ]
    allowed = {"required", "optional"}
    errors: list[ContentError] = []
    for key in raw:
        if key not in allowed:
            errors.append(parsed.error(f"unknown key '{key}'", field=("dependencies", key), expected="one of optional, required"))
    result: dict[str, dict[str, str]] = {"required": {}, "optional": {}}
    for kind in result:
        values = raw.get(kind, {})
        if not isinstance(values, dict):
            errors.append(parsed.error("must be a map of mod ids to version ranges", field=("dependencies", kind), expected="a dependency map whose keys are namespaced mod identifiers"))
            continue
        for mod_id, version_range in values.items():
            if not isinstance(mod_id, str) or not is_valid_id(mod_id):
                errors.append(parsed.error("dependency id is not valid", field=("dependencies", kind), expected="`namespace:name` keys"))
                continue
            if not isinstance(version_range, str) or not _valid_range(version_range):
                errors.append(parsed.error("dependency version is not a supported caret range", field=("dependencies", kind, mod_id), expected="a range such as `^1.0`"))
                continue
            result[kind][mod_id] = version_range
    return result, errors


def _valid_range(value: str) -> bool:
    return value.startswith("^") and _parse_version(value[1:]) is not None


def _parse_version(value: str) -> tuple[int, int, int] | None:
    parts = value.split(".")
    if not 1 <= len(parts) <= 3:
        return None
    try:
        numbers = tuple(int(part) for part in parts)
    except ValueError:
        return None
    if any(number < 0 for number in numbers):
        return None
    return (*numbers, *([0] * (3 - len(numbers))))


def _satisfies(version: str, version_range: str) -> bool:
    """Return whether a semver version is inside the documented caret range."""
    actual = _parse_version(version)
    lower = _parse_version(version_range[1:]) if version_range.startswith("^") else None
    if actual is None or lower is None:
        return False
    if actual < lower:
        return False
    major, minor, patch = lower
    if major > 0:
        return actual[0] == major
    if minor > 0:
        return actual[:2] == (major, minor)
    return actual == (major, minor, patch)


def resolve(manifests: list[Manifest], enabled_mod_ids: Optional[Iterable[str]] = None) -> tuple[list[Manifest], list[ContentError]]:
    """Stage 2 — select compatible mods, report dependency faults, and order survivors.

    Explicitly selected mods pull in their required dependencies.  With no selection every
    discovered mod is a root, which is the normal application-startup behaviour.
    """
    by_id = {manifest.mod_id: manifest for manifest in manifests}
    errors: list[ContentError] = []
    roots = set(by_id) if enabled_mod_ids is None else set(enabled_mod_ids)
    for mod_id in sorted(roots - set(by_id)):
        errors.append(ContentError(mod_id="<engine>", file="<startup>", problem=f"enabled mod '{mod_id}' is not installed", expected="an id from a discovered mod manifest"))
    roots &= set(by_id)

    selected: set[str] = set()
    pending = list(roots)
    while pending:
        mod_id = pending.pop()
        if mod_id in selected or mod_id not in by_id:
            continue
        selected.add(mod_id)
        manifest = by_id[mod_id]
        for dependency in manifest.required_dependencies:
            if dependency in by_id:
                pending.append(dependency)
        # Optional dependencies participate when present in an automatically loaded install.
        if enabled_mod_ids is None:
            for dependency in manifest.optional_dependencies:
                if dependency in by_id:
                    pending.append(dependency)

    broken: set[str] = set()
    edges: dict[str, set[str]] = {mod_id: set() for mod_id in selected}
    for mod_id in sorted(selected):
        manifest = by_id[mod_id]
        # Checked here rather than at manifest read so an incompatible mod disables its
        # dependents through the same propagation path a missing dependency uses. A mod built
        # against an engine that no longer exists is not a content error to be reported later;
        # its content was written against verbs and fields this engine may not have.
        if manifest.engine is not None and not _satisfies(ENGINE_VERSION, manifest.engine):
            broken.add(mod_id)
            errors.append(
                ContentError(
                    mod_id=mod_id,
                    file=MANIFEST_NAME,
                    problem=f"needs engine {manifest.engine}, but this engine is {ENGINE_VERSION}",
                    field="engine",
                    expected=f"a range that includes {ENGINE_VERSION}, or a build of the engine matching {manifest.engine}",
                )
            )
            continue
        for dependency, wanted in manifest.required_dependencies.items():
            candidate = by_id.get(dependency)
            if candidate is None:
                broken.add(mod_id)
                errors.append(ContentError(mod_id=mod_id, file=MANIFEST_NAME, problem=f"required dependency '{dependency}' is not installed", field="dependencies.required", expected=f"{dependency}: {wanted}"))
                continue
            if not _satisfies(candidate.version, wanted):
                broken.add(mod_id)
                errors.append(ContentError(mod_id=mod_id, file=MANIFEST_NAME, problem=f"required dependency '{dependency}' is version {candidate.version}, which is incompatible", field="dependencies.required", expected=f"{dependency}: {wanted}"))
                continue
            if dependency in selected:
                edges[mod_id].add(dependency)
        for dependency, wanted in manifest.optional_dependencies.items():
            candidate = by_id.get(dependency)
            if candidate is not None and dependency in selected:
                if _satisfies(candidate.version, wanted):
                    edges[mod_id].add(dependency)
                else:
                    errors.append(ContentError(mod_id=mod_id, file=MANIFEST_NAME, problem=f"optional dependency '{dependency}' is version {candidate.version}, which is incompatible", field="dependencies.optional", expected=f"{dependency}: {wanted}"))

    cycle = _find_cycle(edges)
    if cycle:
        broken.update(cycle[:-1])
        errors.append(ContentError(mod_id=cycle[0], file=MANIFEST_NAME, problem="dependency cycle: " + " -> ".join(cycle), field="dependencies", expected="an acyclic dependency graph"))

    _propagate_required_failures(broken, edges, errors)
    active = selected - broken
    active_edges = {mod_id: {dependency for dependency in dependencies if dependency in active} for mod_id, dependencies in edges.items() if mod_id in active}
    _validate_namespace_originators(active, active_edges, by_id, errors, broken)
    _propagate_required_failures(broken, edges, errors)
    active = selected - broken
    active_edges = {mod_id: {dependency for dependency in dependencies if dependency in active} for mod_id, dependencies in edges.items() if mod_id in active}
    return _topological_order(active, active_edges, by_id), errors


def _find_cycle(edges: dict[str, set[str]]) -> list[str] | None:
    visiting: set[str] = set()
    visited: set[str] = set()
    trail: list[str] = []

    def walk(node: str) -> list[str] | None:
        if node in visiting:
            start = trail.index(node)
            return trail[start:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        trail.append(node)
        for dependency in sorted(edges.get(node, ())):
            found = walk(dependency)
            if found:
                return found
        trail.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in sorted(edges):
        found = walk(node)
        if found:
            return found
    return None


def _propagate_required_failures(broken: set[str], edges: dict[str, set[str]], errors: list[ContentError]) -> None:
    """Disable required dependents without flooding the report with duplicate chains."""
    changed = True
    while changed:
        changed = False
        for mod_id, dependencies in edges.items():
            if mod_id in broken:
                continue
            failed = sorted(dependency for dependency in dependencies if dependency in broken)
            if failed:
                broken.add(mod_id)
                errors.append(ContentError(mod_id=mod_id, file=MANIFEST_NAME, problem=f"disabled because required dependency '{failed[0]}' is disabled", field="dependencies.required", expected="enable a compatible dependency or remove this dependent mod"))
                changed = True


def _validate_namespace_originators(active: set[str], edges: dict[str, set[str]], by_id: dict[str, Manifest], errors: list[ContentError], broken: set[str]) -> None:
    by_namespace: dict[str, list[str]] = {}
    for mod_id in active:
        namespace = mod_id.split(":", 1)[0]
        by_namespace.setdefault(namespace, []).append(mod_id)

    def depends_on(mod_id: str, candidate: str) -> bool:
        pending = list(edges.get(mod_id, ()))
        seen: set[str] = set()
        while pending:
            item = pending.pop()
            if item == candidate:
                return True
            if item not in seen:
                seen.add(item)
                pending.extend(edges.get(item, ()))
        return False

    for namespace, claimants in by_namespace.items():
        if len(claimants) < 2:
            continue
        origins = [candidate for candidate in claimants if all(other == candidate or depends_on(other, candidate) for other in claimants)]
        if len(origins) != 1:
            broken.update(claimants)
            errors.append(ContentError(mod_id=claimants[0], file=MANIFEST_NAME, problem=f"mods {', '.join(sorted(claimants))} claim namespace '{namespace}' without one dependency originator", field="id", expected="exactly one claimant must be a direct or transitive dependency of every other claimant"))


def _topological_order(active: set[str], edges: dict[str, set[str]], by_id: dict[str, Manifest]) -> list[Manifest]:
    remaining = {mod_id: set(dependencies) for mod_id, dependencies in edges.items()}
    ordered: list[Manifest] = []
    while remaining:
        ready = sorted(mod_id for mod_id, dependencies in remaining.items() if not dependencies)
        if not ready:
            break
        for mod_id in ready:
            ordered.append(by_id[mod_id])
            del remaining[mod_id]
        done = set(ready)
        for dependencies in remaining.values():
            dependencies.difference_update(done)
    return ordered


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

    Patches and post-patch validation have already completed when this stage runs. The load
    pipeline normalizes author-facing references and values before registration, so registries
    receive the effective runtime definitions. The `id` check remains here as a defensive guard
    because registration needs a key and the honest alternative is a `KeyError`.
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
    """Run the nine loader stages and return every attributable failure.

    The two flags are retained for the small registry-only fixtures from the first refactor
    wave.  The application must use the defaults below: content is not loadable game content
    until it has passed both schema validation and reference linking.
    """
    registries = Registries()
    manifests, errors = discover(mods_dir)
    manifests, resolution_errors = resolve(manifests, enabled_mod_ids)
    errors.extend(resolution_errors)

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
        errors.extend(validate_content(files, registries))

    # A mod with any error is disabled whole, so its content never reaches the registries in
    # the first place — but a mod can only be known to be broken once every stage before
    # this one has run, which is why the filter is here and not at each stage.
    broken = {error.mod_id for error in errors}
    survivors = [file for file in files if file.mod_id not in broken]
    warnings: list[str] = []
    if validate:
        patched = apply_patches(survivors)
        errors.extend(patched.errors)
        warnings.extend(patched.warnings)
        broken.update(error.mod_id for error in patched.errors)
        survivors = [file for file in patched.files if file.mod_id not in broken]
        _normalise_references(survivors, patched.aliases)
        # Patches are writes, not a validation bypass.  Run the same schema pass on the
        # effective definitions so a patch that changes a valid value into an invalid one is
        # blamed during startup, before it can reach a registry.
        post_patch_errors = validate_content(survivors, registries)
        post_patch_errors.extend(validate_assets(survivors, {manifest.mod_id: manifest.root for manifest in manifests}))
        errors.extend(post_patch_errors)
        broken.update(error.mod_id for error in post_patch_errors)
        survivors = [file for file in survivors if file.mod_id not in broken]
    else:
        # Registry-only callers deliberately see raw definitions, including patches.  This
        # compatibility path is not used by a game session.
        survivors = [file for file in survivors if file.content_type != "patch"]

    errors.extend(register_content(survivors, registries))

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
        installed=tuple(ModInfo(m.mod_id, m.name, m.ships_code, m.version) for m in manifests),
        errors=errors,
        linked=linked,
        mod_roots={manifest.mod_id: manifest.root for manifest in manifests},
        warnings=warnings,
    )


# These are references in the published data vocabulary, not an engine list of content.  The
# normalizer deliberately runs over field *roles* so an unqualified ``queen`` in a third-party
# board becomes that mod's ``namespace:queen`` without teaching core who a queen is.
_ID_FIELDS = frozenset({
    "board", "pools", "members", "components", "status", "into", "capturer", "captured",
    "owner", "resource", "abilities", "not_status", "has_status", "tag_any", "primary",
    "theme", "hud_layout", "sound",
})


def _normalise_references(files: list[ParsedFile], aliases: dict[str, str]) -> None:
    def resolve(value: str, mod_id: str) -> str:
        if value.startswith("$"):
            return value
        value = qualify(value, mod_id)
        seen: set[str] = set()
        while value in aliases and value not in seen:
            seen.add(value)
            value = aliases[value]
        return value

    def walk(value: object, mod_id: str, role: str | None = None) -> object:
        if isinstance(value, dict):
            for key, child in list(value.items()):
                if key == "id":
                    continue
                if key == "type" and isinstance(child, str) and value is not None:
                    # Move types are the one namespaced vocabulary reference; content type
                    # declarations and effect names are fixed vocabulary words.
                    if isinstance(value, dict) and "moves" not in value:
                        value[key] = child
                    continue
                value[key] = walk(child, mod_id, str(key))
            return value
        if isinstance(value, list):
            return [walk(child, mod_id, role) for child in value]
        if isinstance(value, str) and role in _ID_FIELDS:
            return resolve(value, mod_id)
        return value

    for parsed in files:
        walk(parsed.tree, parsed.mod_id)


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
