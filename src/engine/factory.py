"""Construct Wave 3 state from loader registries without naming chess content in core."""

from __future__ import annotations

from .board import Board, Side
from .piece import Piece, PieceDef, StatusDef
from .state import EngineState


def build_state(registries, mode_id: str) -> EngineState:
    """Build pieces and geometry from registered data for one selected game mode."""
    mode = registries.content["game_mode"].get(mode_id).value.tree
    board_data = registries.content["board"].get(mode["board"]).value.tree
    sides = {
        item["id"]: Side(item["id"], -1 if item["forward"] == "up" else 1, item.get("moves_first", False))
        for item in board_data["sides"]
    }
    board = Board(*board_data["size"], sides)
    definitions = {}
    for entry in registries.content["piece"]:
        data = entry.value.tree
        definitions[entry.id] = PieceDef(entry.id, tuple(data.get("moves", [])), tuple(data.get("components", [entry.id])), dict(data.get("properties", {})))
    statuses = {}
    for entry in registries.content["status"]:
        data = entry.value.tree
        statuses[entry.id] = StatusDef(entry.id, data.get("expiry"), dict(data.get("modifies", {})))
    uid = 0
    for row in board_data["rows"]:
        pieces = row.get("pieces") or [row["fill"]] * board.columns
        for col, piece_id in enumerate(pieces):
            uid += 1
            board.place(Piece(uid, definitions[piece_id], row["side"], (row["row"], col)), (row["row"], col))
    first = next(side.id for side in sides.values() if side.moves_first)
    return EngineState(board=board, status_defs=statuses, current_side=first)
