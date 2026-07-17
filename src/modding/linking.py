"""Stage 8 links for the walking skeleton's board, piece, and mode references."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ContentError
from .parse import ParsedFile
from .registries import Registries


@dataclass(frozen=True)
class Placement:
    """One render-only piece placement; movement belongs to Wave 3."""

    row: int
    col: int
    piece_id: str
    side_id: str


@dataclass(frozen=True)
class LinkedBoard:
    """A board layout whose piece references are known to exist."""

    id: str
    rows: int
    columns: int
    placements: tuple[Placement, ...]


@dataclass(frozen=True)
class LinkedMode:
    """The minimal playable selection for Wave 2's renderer."""

    id: str
    board: LinkedBoard


@dataclass(frozen=True)
class LinkedContent:
    """References proven safe for the content types currently understood by the engine."""

    modes: dict[str, LinkedMode]


def link_content(registries: Registries) -> tuple[LinkedContent, list[ContentError]]:
    """Link game modes to boards and board placements to registered pieces."""
    errors: list[ContentError] = []
    boards: dict[str, LinkedBoard] = {}
    for entry in registries.content["board"]:
        parsed: ParsedFile = entry.value
        placements: list[Placement] = []
        valid = True
        for row_index, row in enumerate(parsed.tree["rows"]):
            pieces = row.get("pieces") or [row["fill"]] * parsed.tree["size"][1]
            for col, piece_id in enumerate(pieces):
                if registries.content["piece"].get(piece_id) is None:
                    errors.append(parsed.error(f"piece '{piece_id}' is not registered", field=("rows", row_index, "pieces", col), expected="a piece id supplied by an enabled mod"))
                    valid = False
                else:
                    placements.append(Placement(row=row["row"], col=col, piece_id=piece_id, side_id=row["side"]))
        if valid:
            size = parsed.tree["size"]
            boards[entry.id] = LinkedBoard(id=entry.id, rows=size[0], columns=size[1], placements=tuple(placements))

    modes: dict[str, LinkedMode] = {}
    for entry in registries.content["game_mode"]:
        parsed = entry.value
        board_id = parsed.tree["board"]
        board = boards.get(board_id)
        if board is None:
            errors.append(parsed.error(f"board '{board_id}' is not registered", field=("board",), expected="a board id supplied by an enabled mod"))
        else:
            modes[entry.id] = LinkedMode(id=entry.id, board=board)

    for entry in registries.content["event_pool"]:
        parsed = entry.value
        for index, event_id in enumerate(parsed.tree.get("members", ())):
            if registries.content["event"].get(event_id) is None:
                errors.append(parsed.error(f"event '{event_id}' is not registered", field=("members", index), expected="an enabled event id"))

    for entry in registries.content["fusion"]:
        parsed = entry.value
        for index, rule in enumerate(parsed.tree.get("rules", ())):
            for field in ("capturer", "captured", "into"):
                piece_id = rule.get(field)
                if registries.content["piece"].get(piece_id) is None:
                    errors.append(parsed.error(f"piece '{piece_id}' is not registered", field=("rules", index, field), expected="an enabled piece id"))
    for entry in registries.content["event"]:
        parsed = entry.value
        for index, step in enumerate(parsed.tree.get("execute", ())):
            effect = step.get("effect", {})
            for field, registry_name in (("into", "piece"), ("status", "status")):
                target = effect.get(field)
                if target is not None and registries.content[registry_name].get(target) is None:
                    errors.append(parsed.error(f"{registry_name} '{target}' is not registered", field=("execute", index, "effect", field), expected=f"an enabled {registry_name} id"))
    return LinkedContent(modes=modes), errors
