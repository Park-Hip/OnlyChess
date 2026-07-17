"""Central status evaluation and expiry policies."""

from __future__ import annotations

from .actions import ClearStatus, TickStatus


def effective_moves(piece):
    """Return move parts after order-independent status restrictions."""
    parts = [dict(part) for part in piece.definition.moves]
    modifiers = [instance.definition.modifies.get("movement", {}) for instance in piece.statuses.values()]
    if any(modifier.get("disable") for modifier in modifiers):
        return []
    for part in parts:
        kind = part.get("type")
        for modifier in modifiers:
            specific = modifier.get(kind, {})
            if specific.get("disable"):
                part["disabled"] = True
            if "limit" in specific:
                old = part.get("limit", "unlimited")
                part["limit"] = specific["limit"] if old == "unlimited" else min(old, specific["limit"])
    return [part for part in parts if not part.get("disabled")]


def capturable(piece) -> bool:
    return not any(instance.definition.modifies.get("capturable") is False for instance in piece.statuses.values())


def expiry_actions(state, completed_side: str):
    """Return reversible expiry actions after one completed turn."""
    actions = []
    for piece in state.board.pieces():
        for status_id, instance in list(piece.statuses.items()):
            expiry = instance.definition.expiry
            if expiry == "after_opponent_turn" and piece.side != completed_side:
                actions.append(ClearStatus(piece, status_id))
            elif isinstance(expiry, dict) and "turns" in expiry and instance.remaining is not None:
                if instance.remaining <= 1:
                    actions.append(ClearStatus(piece, status_id))
                else:
                    actions.append(TickStatus(piece, status_id))
    return actions
