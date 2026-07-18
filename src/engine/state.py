"""Mutable engine state; mutations are made only by actions."""

from __future__ import annotations

from dataclasses import dataclass, field

from .board import Board
from .piece import AbilityDef, Piece, ResourceDef, StatusDef


@dataclass
class EngineState:
    board: Board
    status_defs: dict[str, StatusDef] = field(default_factory=dict)
    resource_defs: dict[str, ResourceDef] = field(default_factory=dict)
    ability_defs: dict[str, AbilityDef] = field(default_factory=dict)
    resources: dict[str, dict[str, int]] = field(default_factory=dict)
    move_counts: dict[str, int] = field(default_factory=dict)
    fusion_defs: tuple[dict, ...] = ()
    event_defs: dict[str, dict] = field(default_factory=dict)
    event_pools: dict[str, dict] = field(default_factory=dict)
    completed_turns: int = 0
    pool_turns: dict[str, int] = field(default_factory=dict)
    pending_events: dict[str, str] = field(default_factory=dict)
    pending_bindings: dict[str, dict[str, object]] = field(default_factory=dict)
    event_messages: list[str] = field(default_factory=list)
    active_pools: tuple[str, ...] = ()
    piece_defs: dict[str, object] = field(default_factory=dict)
    move_types: object | None = None
    current_side: str = ""
    action_log: list[list[object]] = field(default_factory=list)
    last_move: object | None = None
    #: Piece ids each side has captured, in capture order. Filled by RecordCapture; the only
    #: presentation data the engine stores rather than derives, because a board cannot say whether
    #: a missing piece was taken or destroyed.
    captures: dict[str, list[str]] = field(default_factory=dict)

    def royal_piece(self, side: str) -> Piece:
        for piece in self.board.pieces():
            if piece.side == side and piece.definition.royal:
                return piece
        raise ValueError(f"side '{side}' has no royal piece")
