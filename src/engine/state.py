"""Mutable engine state; mutations are made only by actions."""

from __future__ import annotations

from dataclasses import dataclass, field

from .board import Board
from .piece import Piece, StatusDef


@dataclass
class EngineState:
    board: Board
    status_defs: dict[str, StatusDef] = field(default_factory=dict)
    current_side: str = ""
    action_log: list[list[object]] = field(default_factory=list)

    def royal_piece(self, side: str) -> Piece:
        for piece in self.board.pieces():
            if piece.side == side and piece.definition.royal:
                return piece
        raise ValueError(f"side '{side}' has no royal piece")
