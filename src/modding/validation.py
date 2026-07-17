"""Stage 5 validation for the content types exercised by the walking skeleton.

The validator deliberately knows only the fields Wave 2 consumes.  It is not a second,
half-finished schema language: later waves extend this registry-driven walk when they add
their vocabulary.
"""

from __future__ import annotations

from typing import Any

from .errors import ContentError
from .parse import ParsedFile


WALKING_SKELETON_TYPES = frozenset({"piece", "board", "game_mode"})


def validate_content(files: list[ParsedFile]) -> list[ContentError]:
    """Validate the three content kinds Wave 2 can actually consume."""
    errors: list[ContentError] = []
    for parsed in files:
        validator = _VALIDATORS.get(parsed.content_type)
        if validator is not None:
            errors.extend(validator(parsed))
    return errors


def _require_text(parsed: ParsedFile, field: str) -> list[ContentError]:
    value = parsed.tree.get(field)
    if not isinstance(value, str) or not value:
        return [parsed.error("must be a non-empty line of text", field=(field,), expected=f"`{field}: ...`")]
    return []


def _validate_piece(parsed: ParsedFile) -> list[ContentError]:
    errors = _require_text(parsed, "id")
    if "sprite" in parsed.tree:
        errors.extend(_require_text(parsed, "sprite"))
    moves = parsed.tree.get("moves")
    if not isinstance(moves, list):
        errors.append(parsed.error("must be a list", field=("moves",), expected="`moves: []` for an inert preview piece"))
    return errors


def _validate_board(parsed: ParsedFile) -> list[ContentError]:
    errors: list[ContentError] = []
    size = parsed.tree.get("size")
    if not (isinstance(size, list) and len(size) == 2 and all(isinstance(value, int) and value > 0 for value in size)):
        errors.append(parsed.error("must be two positive whole numbers", field=("size",), expected="`size: [rows, columns]`"))
        return errors

    rows, columns = size
    sides = parsed.tree.get("sides")
    if not isinstance(sides, list) or not sides:
        errors.append(parsed.error("must name at least one side", field=("sides",), expected="a list of side settings"))
        side_ids: set[str] = set()
    else:
        side_ids = set()
        for index, side in enumerate(sides):
            if not isinstance(side, dict) or not isinstance(side.get("id"), str):
                errors.append(parsed.error("must contain an `id`", field=("sides", index), expected="`- { id: namespace:name, ... }`"))
                continue
            side_ids.add(side["id"])

    board_rows = parsed.tree.get("rows")
    if not isinstance(board_rows, list):
        errors.append(parsed.error("must be a list", field=("rows",), expected="a list of placed rows"))
        return errors

    seen_rows: set[int] = set()
    for index, row in enumerate(board_rows):
        path = ("rows", index)
        if not isinstance(row, dict):
            errors.append(parsed.error("must be a block of settings", field=path, expected="`- { row: 0, side: ..., pieces: [...] }`"))
            continue
        number = row.get("row")
        if not isinstance(number, int) or not 0 <= number < rows:
            errors.append(parsed.error("is outside this board", field=path + ("row",), expected=f"a row from 0 through {rows - 1}"))
        elif number in seen_rows:
            errors.append(parsed.error("is declared more than once", field=path + ("row",), expected="one placement rule per row"))
        else:
            seen_rows.add(number)
        if row.get("side") not in side_ids:
            errors.append(parsed.error("does not name a declared side", field=path + ("side",), expected="one of this board's side ids"))
        pieces = row.get("pieces")
        fill = row.get("fill")
        if pieces is not None:
            if not (isinstance(pieces, list) and len(pieces) == columns and all(isinstance(piece, str) for piece in pieces)):
                errors.append(parsed.error("must name one piece id for every column", field=path + ("pieces",), expected=f"a list of {columns} piece ids"))
        elif not isinstance(fill, str):
            errors.append(parsed.error("must use `pieces` or `fill`", field=path, expected=f"a list of {columns} piece ids or one fill id"))
    return errors


def _validate_game_mode(parsed: ParsedFile) -> list[ContentError]:
    errors = _require_text(parsed, "board")
    pools = parsed.tree.get("pools")
    if not isinstance(pools, list) or not all(isinstance(pool, str) for pool in pools):
        errors.append(parsed.error("must be a list of pool ids", field=("pools",), expected="`pools: []` for a mode without events"))
    return errors


def _validate_fusion(parsed: ParsedFile) -> list[ContentError]:
    rules = parsed.tree.get("rules")
    if not isinstance(rules, list):
        return [parsed.error("must be a list", field=("rules",), expected="ordered fusion rules")]
    return [] if parsed.tree.get("fuses_on") == "displacing_captures" else [parsed.error("must declare the supported capture trigger", field=("fuses_on",), expected="`displacing_captures`")]


def _validate_event_pool(parsed: ParsedFile) -> list[ContentError]:
    if not isinstance(parsed.tree.get("members"), list) or not parsed.tree["members"]:
        return [parsed.error("must name at least one event", field=("members",), expected="a list of event ids")]
    return []


def _validate_event(parsed: ParsedFile) -> list[ContentError]:
    execute = parsed.tree.get("execute")
    if not isinstance(execute, list):
        return [parsed.error("must be a list of select/effect steps", field=("execute",), expected="`execute: []`")]
    errors = []
    for index, step in enumerate(execute):
        if not isinstance(step, dict) or not isinstance(step.get("select"), dict) or not isinstance(step.get("effect"), dict):
            errors.append(parsed.error("must contain `select` and `effect` maps", field=("execute", index), expected="a selector followed by an effect"))
    return errors


_VALIDATORS: dict[str, Any] = {
    "piece": _validate_piece,
    "board": _validate_board,
    "game_mode": _validate_game_mode,
    "fusion": _validate_fusion,
    "event_pool": _validate_event_pool,
    "event": _validate_event,
}
