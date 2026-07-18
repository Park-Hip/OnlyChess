"""Stage 6 replacement and field-patch operations.

Patches work on the author-facing YAML tree, before any runtime normalization.  Keeping the
operations here rather than in registries preserves ADR-002's rule that field names are public API
and lets invalid patched values be blamed on the patch that wrote them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .errors import ContentError
from .parse import FieldPath, ParsedFile, Provenance
from .registries import qualify


_PATH_PART = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)(?:\[(\d+)\])?")


@dataclass
class PatchResult:
    """The definitions surviving stage 6 and the aliases replacements introduce."""

    files: list[ParsedFile]
    aliases: dict[str, str] = field(default_factory=dict)
    errors: list[ContentError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def apply_patches(files: list[ParsedFile]) -> PatchResult:
    """Apply replacements first, then field patches in resolved mod/file order."""
    definitions = [parsed for parsed in files if parsed.content_type != "patch"]
    patches = [parsed for parsed in files if parsed.content_type == "patch"]
    result = PatchResult(files=[])
    by_id: dict[str, ParsedFile] = {}
    for parsed in definitions:
        entry_id = parsed.tree.get("id")
        if isinstance(entry_id, str) and entry_id not in by_id:
            by_id[entry_id] = parsed

    aliases: dict[str, str] = {}
    replaced: set[int] = set()
    for parsed in definitions:
        target = parsed.tree.get("replaces")
        if target is None:
            continue
        if not isinstance(target, str):
            result.errors.append(parsed.error("must name the definition to replace", field=("replaces",), expected="a content id"))
            continue
        target_id = _resolve_alias(qualify(target, parsed.mod_id), aliases)
        incumbent = by_id.get(target_id)
        if incumbent is None:
            result.errors.append(parsed.error(f"replacement target '{target_id}' does not exist", field=("replaces",), expected="an enabled content id"))
            continue
        if incumbent.content_type != parsed.content_type:
            result.errors.append(parsed.error(f"cannot replace {incumbent.content_type} '{target_id}' with {parsed.content_type} content", field=("replaces",), expected=f"a {parsed.content_type} id"))
            continue
        if target_id in aliases:
            result.warnings.append(f"{parsed.mod_id} replaces '{target_id}' after an earlier replacement; the later definition wins")
        replaced.add(id(incumbent))
        by_id[parsed.tree["id"]] = parsed
        aliases[target_id] = parsed.tree["id"]

    # Collapse chains so every old reference points at the surviving definition.
    for key in tuple(aliases):
        aliases[key] = _resolve_alias(aliases[key], aliases)

    effective = [parsed for parsed in definitions if id(parsed) not in replaced]
    effective_by_id = {parsed.tree["id"]: parsed for parsed in effective if isinstance(parsed.tree.get("id"), str)}

    touched: dict[tuple[str, tuple[object, ...]], ParsedFile] = {}
    for patch_file in patches:
        declarations = patch_file.tree.get("patches")
        if not isinstance(declarations, list):
            continue  # Stage 5 reports the shape error with the better message.
        for index, declaration in enumerate(declarations):
            if not isinstance(declaration, dict):
                continue
            target = declaration.get("target")
            path_text = declaration.get("path")
            operation = declaration.get("op")
            if not isinstance(target, str) or not isinstance(path_text, str) or not isinstance(operation, str):
                continue
            target_id = _resolve_alias(qualify(target, patch_file.mod_id), aliases)
            target_file = effective_by_id.get(target_id)
            if target_file is None:
                result.errors.append(patch_file.error(f"patch target '{target_id}' does not exist", field=("patches", index, "target"), expected="an enabled content id after replacements"))
                continue
            path = _parse_path(path_text)
            if path is None:
                result.errors.append(patch_file.error("is not a valid patch path", field=("patches", index, "path"), expected="field names with optional [index], for example `moves[0].limit`"))
                continue
            key = (target_id, path)
            earlier = touched.get(key)
            if earlier is not None:
                result.warnings.append(f"{patch_file.mod_id} patches '{target_id}' at '{path_text}' after {earlier.mod_id}; the later value wins")
            touched[key] = patch_file
            error = _apply_one(target_file, patch_file, index, operation, path, declaration.get("value"))
            if error is not None:
                result.errors.append(error)

    result.files = effective
    result.aliases = aliases
    return result


def _resolve_alias(value: str, aliases: dict[str, str]) -> str:
    seen: set[str] = set()
    while value in aliases and value not in seen:
        seen.add(value)
        value = aliases[value]
    return value


def _parse_path(text: str) -> tuple[object, ...] | None:
    if not text:
        return None
    parts: list[object] = []
    for segment in text.split("."):
        match = _PATH_PART.fullmatch(segment)
        if match is None:
            return None
        parts.append(match.group(1))
        if match.group(2) is not None:
            parts.append(int(match.group(2)))
    return tuple(parts)


def _apply_one(target: ParsedFile, patch: ParsedFile, index: int, operation: str, path: FieldPath, value: Any) -> ContentError | None:
    parent, final, error = _parent_at(target, patch, index, path)
    if error is not None:
        return error
    source = _source_for(patch, index)
    if operation == "set":
        if isinstance(parent, dict):
            parent[final] = value
        elif isinstance(parent, list) and isinstance(final, int) and 0 <= final < len(parent):
            parent[final] = value
        else:
            return patch.error("patch path does not name an existing value", field=("patches", index, "path"), expected="an existing mapping field or list entry")
        _stamp(target, path, value, source)
        return None
    if operation == "add":
        destination = _value_at(parent, final)
        if not isinstance(destination, list):
            return patch.error("`add` requires a list path", field=("patches", index, "path"), expected="a path naming a list")
        destination.append(value)
        _stamp(target, path + (len(destination) - 1,), value, source)
        return None
    if operation == "remove":
        if isinstance(parent, dict) and final in parent:
            del parent[final]
            return None
        if isinstance(parent, list) and isinstance(final, int) and 0 <= final < len(parent):
            del parent[final]
            return None
        return patch.error("patch path does not name a removable value", field=("patches", index, "path"), expected="an existing mapping field or list entry")
    return patch.error(f"unknown patch operation '{operation}'", field=("patches", index, "op"), expected="one of add, remove, set")


def _parent_at(target: ParsedFile, patch: ParsedFile, index: int, path: FieldPath) -> tuple[Any, object, ContentError | None]:
    node = target.tree
    for segment in path[:-1]:
        try:
            node = node[segment]
        except (KeyError, IndexError, TypeError):
            return None, None, patch.error("patch path does not resolve on its target", field=("patches", index, "path"), expected="a field path that exists on the target definition")
    return node, path[-1], None


def _value_at(parent: Any, key: object) -> Any:
    try:
        return parent[key]
    except (KeyError, IndexError, TypeError):
        return None


def _source_for(patch: ParsedFile, index: int) -> Provenance:
    position = patch.position(("patches", index, "value")) or patch.position(("patches", index))
    return Provenance(patch.mod_id, patch.display, position[0] if position else None, position[1] if position else None)


def _stamp(target: ParsedFile, path: FieldPath, value: Any, source: Provenance) -> None:
    target.stamp_provenance(path, source)
    if isinstance(value, dict):
        for key, child in value.items():
            _stamp(target, path + (key,), child, source)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _stamp(target, path + (index,), child, source)
