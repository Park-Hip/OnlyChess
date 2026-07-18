"""Stage 5: structural validation before content enters a registry.

Validation is intentionally about the public YAML contract, not about individual base-game
objects.  A malformed third-party definition therefore fails at startup with its own file and
field, rather than becoming a KeyError in a later turn.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ContentError, did_you_mean, one_of
from .parse import ParsedFile
from .registries import CONTENT_TYPES, Registries, is_valid_id, qualify


_COMMON = {"type", "id", "replaces"}
_FIELDS = {
    "ability": _COMMON | {"name", "owner", "cost", "target", "effect", "when"},
    "board": _COMMON | {"size", "sides", "rows"},
    "event": _COMMON | {"name", "warning", "execute", "empty_message"},
    "event_pool": _COMMON | {"name", "every", "warn_before", "pick", "members"},
    "fusion": _COMMON | {"name", "match", "fuses_on", "rules", "compose"},
    "game_mode": _COMMON | {"name", "board", "pools", "presentation"},
    "patch": _COMMON | {"patches"},
    "piece": _COMMON | {"name", "material", "components", "moves", "on", "properties", "sprite", "presentation"},
    "resource": _COMMON | {"name", "starting", "max", "gain"},
    "status": _COMMON | {"name", "expiry", "modifies", "on_expire", "presentation"},
    "theme": _COMMON | {"name", "palette", "typography"},
    "hud_layout": _COMMON | {"name", "widgets"},
    "sound": _COMMON | {"name", "cues"},
}


def validate_content(files: list[ParsedFile], registries: Registries | None = None) -> list[ContentError]:
    """Collect schema errors for every parsed file; never silently ignore a field."""
    errors: list[ContentError] = []
    for parsed in files:
        allowed = _FIELDS[parsed.content_type]
        for key in parsed.tree:
            if key not in allowed:
                errors.append(parsed.error(
                    f"unknown key '{key}'", field=(key,), expected=one_of(sorted(allowed)),
                    suggestion=did_you_mean(str(key), allowed),
                ))
        entry_id = parsed.tree.get("id")
        if not isinstance(entry_id, str) or not is_valid_id(entry_id):
            errors.append(parsed.error("must be a namespaced id", field=("id",), expected="`namespace:name`, lowercase letters, digits and underscores only"))
        if "replaces" in parsed.tree and not isinstance(parsed.tree["replaces"], str):
            errors.append(parsed.error("must name one definition", field=("replaces",), expected="a content id"))
        presentation = parsed.tree.get("presentation")
        if presentation is not None and not isinstance(presentation, dict):
            errors.append(parsed.error("must be a settings block", field=("presentation",), expected="presentation fields"))
        elif isinstance(presentation, dict):
            if parsed.content_type == "piece" and (not isinstance(presentation.get("glyph"), str) or not presentation["glyph"]):
                errors.append(parsed.error("requires an explicit glyph", field=("presentation", "glyph"), expected="one visible fallback character"))
            if parsed.content_type == "game_mode" and set(presentation) != {"theme", "hud_layout", "sound"}:
                errors.append(parsed.error("must reference theme, hud_layout, and sound", field=("presentation",), expected="three presentation ids"))
        validator = _VALIDATORS[parsed.content_type]
        errors.extend(validator(parsed, registries))
    return errors


def validate_assets(files: list[ParsedFile], mod_roots: dict[str, Path]) -> list[ContentError]:
    """Verify declared presentation assets stay owned by their defining mod."""
    errors: list[ContentError] = []
    def check(parsed: ParsedFile, path: str, field, extensions: set[str]):
        candidate = Path(path)
        root = mod_roots[parsed.mod_id]
        if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts or candidate.parts[0] != "assets":
            errors.append(parsed.error("must be a relative path beneath assets/", field=field, expected="an owned asset path such as `assets/icons/shield.png`")); return
        if candidate.suffix.lower() not in extensions:
            errors.append(parsed.error("has an unsupported asset format", field=field, expected="one of " + ", ".join(sorted(extensions)))); return
        if not (root / candidate).is_file(): errors.append(parsed.error("asset file is missing", field=field, expected="an existing mod-owned asset"))
    for parsed in files:
        presentation = parsed.tree.get("presentation", {})
        if isinstance(presentation, dict):
            for key in ("sprite", "icon"):
                if isinstance(presentation.get(key), str): check(parsed, presentation[key], ("presentation", key), {".png"})
        if parsed.content_type == "sound":
            for cue, path in parsed.tree.get("cues", {}).items():
                if isinstance(path, str): check(parsed, path, ("cues", cue), {".wav", ".ogg"})
    return errors


def _text(parsed: ParsedFile, name: str, required: bool = True) -> list[ContentError]:
    value = parsed.tree.get(name)
    if value is None and not required:
        return []
    return [] if isinstance(value, str) and value else [parsed.error("must be non-empty text", field=(name,), expected=f"`{name}: ...`")]


def _piece(parsed: ParsedFile, registries: Registries | None) -> list[ContentError]:
    errors = _text(parsed, "name") + _text(parsed, "sprite", required=False)
    if not isinstance(parsed.tree.get("moves"), list):
        return errors + [parsed.error("must be a list", field=("moves",), expected="`moves: []`")]
    for index, move in enumerate(parsed.tree["moves"]):
        path = ("moves", index)
        if not isinstance(move, dict) or not isinstance(move.get("type"), str):
            errors.append(parsed.error("must declare a move `type`", field=path, expected="a move settings block"))
            continue
        kind = move["type"]
        builtins = {"slide", "leap"}
        registered = registries and registries.verbs["move_type"].get(qualify(kind, parsed.mod_id))
        if kind not in builtins and registered is None:
            errors.append(parsed.error(f"unknown move type '{kind}'", field=path + ("type",), expected="`slide`, `leap`, or a move type registered by an enabled code mod"))
        if kind == "slide" and not isinstance(move.get("dirs"), (str, list)):
            errors.append(parsed.error("slide requires `dirs`", field=path + ("dirs",), expected="a direction name or list"))
        if kind == "leap" and not isinstance(move.get("offsets"), list):
            errors.append(parsed.error("leap requires `offsets`", field=path + ("offsets",), expected="a list of [forward, right] offsets"))
    return errors


def _board(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    errors: list[ContentError] = []
    size = parsed.tree.get("size")
    if not (isinstance(size, list) and len(size) == 2 and all(isinstance(x, int) and x > 0 for x in size)):
        return [parsed.error("must be two positive whole numbers", field=("size",), expected="`size: [rows, columns]`")]
    sides = parsed.tree.get("sides")
    side_ids = set()
    if not isinstance(sides, list) or not sides:
        errors.append(parsed.error("must declare at least one side", field=("sides",), expected="a list of side settings"))
    else:
        for i, side in enumerate(sides):
            if not isinstance(side, dict) or not isinstance(side.get("id"), str) or not isinstance(side.get("name"), str) or not side["name"]:
                errors.append(parsed.error("must declare non-empty `id` and `name`", field=("sides", i), expected="`- { id: ..., name: ... }`"))
            else:
                side_ids.add(side["id"])
    rows = parsed.tree.get("rows")
    if not isinstance(rows, list):
        return errors + [parsed.error("must be a list", field=("rows",), expected="placed rows")]
    for i, row in enumerate(rows):
        path = ("rows", i)
        if not isinstance(row, dict):
            errors.append(parsed.error("must be a settings block", field=path, expected="`row`, `side`, and `pieces` or `fill`")); continue
        if not isinstance(row.get("row"), int) or not 0 <= row["row"] < size[0]:
            errors.append(parsed.error("is outside this board", field=path + ("row",), expected=f"0 through {size[0] - 1}"))
        if row.get("side") not in side_ids:
            errors.append(parsed.error("does not name a declared side", field=path + ("side",), expected="one of this board's sides"))
        pieces, fill = row.get("pieces"), row.get("fill")
        if pieces is None and not isinstance(fill, str):
            errors.append(parsed.error("must use `pieces` or `fill`", field=path, expected="one piece id or one id per column"))
        if pieces is not None and (not isinstance(pieces, list) or len(pieces) != size[1] or not all(isinstance(x, str) for x in pieces)):
            errors.append(parsed.error("must name one piece id per column", field=path + ("pieces",), expected=f"a list of {size[1]} ids"))
    return errors


def _mode(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    errors = _text(parsed, "name") + _text(parsed, "board")
    if not isinstance(parsed.tree.get("pools"), list) or not all(isinstance(x, str) for x in parsed.tree.get("pools", ())):
        errors.append(parsed.error("must be a list of event-pool ids", field=("pools",), expected="`pools: []`"))
    return errors


def _event(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    errors = _text(parsed, "name")
    if not isinstance(parsed.tree.get("execute"), list):
        errors.append(parsed.error("must be a list", field=("execute",), expected="`execute: []`"))
    return errors


def _pool(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    members = parsed.tree.get("members")
    return [] if isinstance(members, list) and members and all(isinstance(x, str) for x in members) else [parsed.error("must name at least one event", field=("members",), expected="a list of event ids")]


def _fusion(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    errors = []
    if parsed.tree.get("fuses_on") != "displacing_captures": errors.append(parsed.error("must declare the supported capture trigger", field=("fuses_on",), expected="`displacing_captures`"))
    compose = parsed.tree.get("compose")
    if compose is not None and compose != "union":
        errors.append(parsed.error("is not a supported composition mode", field=("compose",), expected="`union`, or omit it and declare `rules`"))
    # A table declares how a pair resolves; `compose: union` derives it instead. One or the other:
    # a table with neither says a capture fuses without saying into what.
    if compose is None and not isinstance(parsed.tree.get("rules"), list):
        errors.append(parsed.error("must be a list", field=("rules",), expected="ordered fusion rules, or `compose: union`"))
    return errors


def _patch(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    patches = parsed.tree.get("patches")
    if not isinstance(patches, list): return [parsed.error("must be a list", field=("patches",), expected="patch declarations")]
    errors = []
    for i, patch in enumerate(patches):
        if not isinstance(patch, dict) or not all(isinstance(patch.get(key), str) for key in ("target", "op", "path")):
            errors.append(parsed.error("must have text `target`, `op`, and `path`", field=("patches", i), expected="a patch declaration"))
    return errors


def _generic(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    return _text(parsed, "name", required=False)


_PALETTE = {"background", "panel", "board_light", "board_dark", "text", "accent", "warning", "selection", "target"}
_WIDGETS = {"turn", "resources", "log", "prompt", "clock", "material", "countdown", "captures"}
_SLOTS = {"top", "side", "bottom"}
_CUES = {"move_completed", "capture_completed", "ability_used", "promotion_chosen", "event_warning", "event_executed", "status_applied", "status_expired", "outcome_reached", "undo_completed"}


def _theme(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    errors = _text(parsed, "name")
    palette = parsed.tree.get("palette")
    if not isinstance(palette, dict) or set(palette) != _PALETTE or not all(isinstance(value, str) and value.startswith("#") for value in (palette or {}).values()):
        errors.append(parsed.error("must define every named palette token as a hex colour", field=("palette",), expected=one_of(sorted(_PALETTE))))
    return errors


def _hud(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    errors = _text(parsed, "name")
    widgets = parsed.tree.get("widgets")
    if not isinstance(widgets, list): return errors + [parsed.error("must be an ordered list", field=("widgets",), expected="HUD widget settings")]
    seen = set()
    for index, widget in enumerate(widgets):
        if not isinstance(widget, dict) or widget.get("type") not in _WIDGETS or widget.get("slot") not in _SLOTS:
            errors.append(parsed.error("must use a known widget type and slot", field=("widgets", index), expected="type: turn/resources/log/prompt/clock/material/countdown/captures and slot: top/side/bottom")); continue
        if widget["type"] in seen: errors.append(parsed.error("may appear only once", field=("widgets", index, "type"), expected="one declaration per widget type"))
        seen.add(widget["type"])
    return errors


def _sound(parsed: ParsedFile, _registries: Registries | None) -> list[ContentError]:
    errors = _text(parsed, "name")
    cues = parsed.tree.get("cues")
    if not isinstance(cues, dict): return errors + [parsed.error("must map notifications to audio paths", field=("cues",), expected=one_of(sorted(_CUES)))]
    for cue, path in cues.items():
        if cue not in _CUES or not isinstance(path, str): errors.append(parsed.error("uses an unknown notification or non-text path", field=("cues", cue), expected=one_of(sorted(_CUES))))
    return errors


_VALIDATORS: dict[str, Any] = {"piece": _piece, "board": _board, "game_mode": _mode, "event": _event, "event_pool": _pool, "fusion": _fusion, "patch": _patch, "ability": _generic, "resource": _generic, "status": _generic, "theme": _theme, "hud_layout": _hud, "sound": _sound}
