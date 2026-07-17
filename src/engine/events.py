"""Deterministic, action-only execution of loaded event data."""

from __future__ import annotations

import random

from .actions import AppendMessage, Relocate, Remove, Replace, SetPendingBindings, SetPendingEvent, SetPoolTurn, SetSide, SetStatus, Swap
from .piece import Piece, StatusInstance


class EventRunner:
    def __init__(self, state, *, seed=0):
        self.state = state
        self.rng = random.Random(seed)

    def execute(self, event_id, bindings=None):
        event = self.state.event_defs[event_id]
        actions = []
        for step in event.get("execute", []):
            selected = self._select(step.get("select", {}), bindings or {})
            actions.extend(self._effect(step["effect"], selected))
            actions.extend(self._messages(step.get("message"), selected))
        if not actions and event.get("empty_message"):
            actions.append(AppendMessage(event["empty_message"]))
        return actions

    def advance_pool(self, pool_id):
        """Return the next warning or execution record for one loaded pool."""
        pool = self.state.event_pools[pool_id]
        turn = self.state.pool_turns[pool_id] + 1
        actions = [SetPoolTurn(pool_id, turn)]
        phase = turn % pool["every"]
        warning_phase = (pool["every"] - pool.get("warn_before", 0)) % pool["every"]
        if phase == warning_phase:
            event_id = self.rng.choice(pool["members"])
            bindings = self._bind(self.state.event_defs[event_id].get("warning", {}).get("bind", {}))
            actions.extend((SetPendingEvent(pool_id, event_id), SetPendingBindings(pool_id, bindings)))
            message = self.state.event_defs[event_id].get("warning", {}).get("message")
            if message: actions.append(AppendMessage(message))
            return "warning", event_id, actions
        if phase == 0:
            event_id = self.state.pending_events.get(pool_id)
            if event_id is None:
                event_id = self.rng.choice(pool["members"])
            actions.extend(self.execute(event_id, self.state.pending_bindings.get(pool_id, {})))
            actions.extend((SetPendingEvent(pool_id, None), SetPendingBindings(pool_id, None)))
            return "execute", event_id, actions
        return None, None, actions

    def _messages(self, declaration, pieces):
        if not declaration: return []
        if isinstance(declaration, str): return [AppendMessage(declaration)]
        template = declaration.get("each")
        if template is None: return []
        return [AppendMessage(template.replace("{piece}", piece.definition.id).replace("{square}", f"{piece.pos[0]},{piece.pos[1]}")) for piece in pieces]

    def _bind(self, declarations):
        bindings = {}
        for name, declaration in declarations.items():
            if declaration.get("type") == "random_zone":
                rows = declaration["origin"]["rows"]
                cols = declaration["origin"]["cols"]
                bindings[name] = (self.rng.randint(*rows), self.rng.randint(*cols), *declaration["size"])
        return bindings

    def _select(self, spec, bindings):
        scope = spec.get("scope", "board")
        pieces = list(self.state.board.pieces())
        if isinstance(scope, dict) and any(key in scope for key in ("ray", "adjacent", "offset")):
            raise ValueError("this selector scope requires an acting-piece context")
        if isinstance(scope, dict) and "zone" in scope:
            binding = bindings[scope["zone"].removeprefix("$")]
            row, col, height, width = binding
            pieces = [piece for piece in pieces if row <= piece.pos[0] < row + height and col <= piece.pos[1] < col + width]
        pieces = [piece for piece in pieces if self._matches(piece, spec.get("filter", {}))]
        pick = spec.get("pick", "all")
        if pick == "all": return pieces
        count = pick.get("random", 1)
        if pick.get("per") == "color":
            out = []
            for side in self.state.board.sides:
                candidates = [piece for piece in pieces if piece.side == side]
                out.extend(self.rng.sample(candidates, min(count, len(candidates))))
            return out
        return self.rng.sample(pieces, min(count, len(pieces)))

    def _matches(self, piece, filters):
        if "is" in filters and piece.definition.id != filters["is"]: return False
        if "primary" in filters and piece.definition.components[0] != filters["primary"]: return False
        if "tag_any" in filters and not any(tag in piece.definition.components for tag in filters["tag_any"]): return False
        if "not" in filters and piece.definition.id == filters["not"]: return False
        if "color" in filters:
            wanted = filters["color"]
            if wanted != "random_one" and not piece.side.endswith(wanted): return False
        if filters.get("empty") is True:
            return False
        return not any(status in piece.statuses for status in filters.get("not_status", ()))

    def _effect(self, effect, pieces):
        kind = effect["type"]
        if kind == "destroy": return [Remove(piece) for piece in pieces]
        if kind == "set_color": return [SetSide(piece, effect["to"]) for piece in pieces]
        if kind == "apply_status":
            definition = self.state.status_defs[effect["status"]]
            return [SetStatus(piece, StatusInstance(definition, effect.get("duration"))) for piece in pieces]
        if kind == "transform":
            definition = self.state.piece_defs[effect["into"]]
            def replacement(piece):
                preserve = effect.get("preserve", [])
                statuses = dict(piece.statuses) if preserve == "all_except_identity" else {}
                moved = piece.has_moved if preserve == "all_except_identity" or "has_moved" in preserve else False
                return Replace(piece, Piece(piece.uid, definition, piece.side, piece.pos, moved, statuses))
            return [replacement(piece) for piece in pieces]
        if kind == "move":
            destination = effect.get("to")
            if not (isinstance(destination, (list, tuple)) and len(destination) == 2):
                raise ValueError("event move needs a concrete two-coordinate destination")
            square = tuple(destination)
            if not self.state.board.inside(square) or self.state.board.at(square) is not None:
                raise ValueError("event move destination must be an empty board square")
            if len(pieces) != 1:
                raise ValueError("event move needs exactly one selected piece")
            return [Relocate(pieces[0], square)]
        if kind == "swap":
            if len(pieces) != 2:
                raise ValueError("event swap needs exactly two selected pieces")
            return [Swap(pieces[0], pieces[1])]
        raise ValueError(f"unsupported event effect '{kind}'")
