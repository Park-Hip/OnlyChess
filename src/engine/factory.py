"""Construct Wave 3 state from loader registries without naming chess content in core."""

from __future__ import annotations

from .board import Board, Side
from .piece import AbilityDef, Piece, PieceDef, ResourceDef, StatusDef
from .state import EngineState


def build_state(registries, mode_id: str) -> EngineState:
    """Build pieces and geometry from registered data for one selected game mode."""
    mode = registries.content["game_mode"].get(mode_id).value.tree
    board_data = registries.content["board"].get(mode["board"]).value.tree
    sides = {
        item["id"]: Side(
            item["id"],
            item["name"],
            -1 if item["forward"] == "up" else 1,
            item.get("moves_first", False),
            item.get("promotes_at"),
        )
        for item in board_data["sides"]
    }
    board = Board(*board_data["size"], sides)
    definitions = {}
    for entry in registries.content["piece"]:
        data = entry.value.tree
        properties = dict(data.get("properties", {}))
        if "on" in data:
            properties["on"] = tuple(data["on"])
        definitions[entry.id] = PieceDef(entry.id, tuple(data.get("moves", [])), tuple(data.get("components", [entry.id])), properties, int(data.get("material", 0)))
    statuses = {}
    for entry in registries.content["status"]:
        data = entry.value.tree
        statuses[entry.id] = StatusDef(entry.id, data.get("expiry"), dict(data.get("modifies", {})))
    resources = {}
    for entry in registries.content["resource"]:
        data = entry.value.tree
        resources[entry.id] = ResourceDef(entry.id, data["starting"], data["max"], dict(data["gain"]))
    abilities = {}
    for entry in registries.content["ability"]:
        data = entry.value.tree
        abilities[entry.id] = AbilityDef(
            entry.id,
            data.get("name", entry.id.rsplit(":", 1)[-1]),
            dict(data["owner"]),
            dict(data.get("cost", {})),
            data["target"],
            data["effect"],
            dict(data.get("when", {})),
        )
    uid = 0
    for row in board_data["rows"]:
        pieces = row.get("pieces") or [row["fill"]] * board.columns
        for col, piece_id in enumerate(pieces):
            uid += 1
            board.place(Piece(uid, definitions[piece_id], row["side"], (row["row"], col)), (row["row"], col))
    first = next(side.id for side in sides.values() if side.moves_first)
    return EngineState(
        board=board,
        status_defs=statuses,
        resource_defs=resources,
        ability_defs=abilities,
        resources={side: {resource.id: resource.starting for resource in resources.values()} for side in sides},
        move_counts={side: 0 for side in sides},
        fusion_defs=tuple(entry.value.tree for entry in registries.content["fusion"]),
        event_defs={entry.id: entry.value.tree for entry in registries.content["event"]},
        event_pools={entry.id: entry.value.tree for entry in registries.content["event_pool"]},
        pool_turns={entry.id: 0 for entry in registries.content["event_pool"]},
        active_pools=tuple(mode.get("pools", ())),
        piece_defs=definitions,
        move_types=registries.verbs["move_type"],
        current_side=first,
    )
