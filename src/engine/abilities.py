"""Small generic ability interpreter exercised by the base chess content."""

from __future__ import annotations

from .actions import Relocate, Remove, Replace, SetStatus, Swap
from .piece import Piece, StatusInstance
from src.modding.registries import qualify


def build_ability_actions(state, owner, ability, target=None):
    """Validate one declared ability and return its reversible actions."""
    if not _matches(owner, ability.owner):
        raise ValueError(f"'{owner.definition.id}' cannot use '{ability.id}'")
    if ability.when.get("not_status") and any(status in owner.statuses for status in ability.when["not_status"]):
        raise ValueError("the ability condition is not met")
    selected = _select(state, owner, ability.target, target)
    return _effect_actions(state, owner, ability.effect, selected)


def _matches(piece, selector):
    tags = selector.get("tag_any", ())
    return not tags or any(tag in piece.definition.components for tag in tags)


def _select(state, owner, spec, explicit):
    if spec == "self":
        return [owner]
    if explicit is not None:
        selected = state.board.at(explicit) if isinstance(explicit, tuple) else explicit
        if selected is None or not _matches_target(state, owner, selected, spec):
            raise ValueError("the selected target is not permitted")
        return [selected]
    scope = spec.get("scope", {})
    if isinstance(scope, str) and scope == "board":
        return [piece for piece in state.board.pieces() if piece is not owner and _matches_target(state, owner, piece, spec)]
    if "offset" in scope:
        forward, right = scope["offset"]
        square = (owner.pos[0] + forward * state.board.sides[owner.side].forward, owner.pos[1] + right)
        return [square] if state.board.inside(square) and state.board.at(square) is None else []
    if "adjacent" in scope:
        # Honour the direction name the content declared. It used to be ignored and orthogonal
        # assumed, which happened to be right for the one ability that used it and silently wrong
        # for anything else. The names are movement's, so `all`, `orthogonal`, and `diagonal` mean
        # here exactly what they mean in a piece's moves.
        directions = _adjacent_directions(scope["adjacent"])
        pieces = [owner] if scope.get("include_self") else []
        for dr, dc in directions:
            candidate = state.board.at((owner.pos[0] + dr, owner.pos[1] + dc))
            if candidate is not None and _matches_target(state, owner, candidate, spec):
                pieces.append(candidate)
        return pieces
    if scope.get("ray") == "diagonal":
        pieces = []
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            row, col = owner.pos
            while True:
                row, col = row + dr, col + dc
                candidate = state.board.at((row, col))
                if not state.board.inside((row, col)):
                    break
                if candidate is not None:
                    if _matches_target(state, owner, candidate, spec):
                        pieces.append(candidate)
                    break
        return pieces
    raise ValueError("unsupported ability target scope")


_ADJACENT = {
    "orthogonal": ((-1, 0), (1, 0), (0, -1), (0, 1)),
    "diagonal": ((-1, -1), (-1, 1), (1, -1), (1, 1)),
}
_ADJACENT["all"] = _ADJACENT["orthogonal"] + _ADJACENT["diagonal"]


def _adjacent_directions(name):
    return _ADJACENT.get(name, _ADJACENT["orthogonal"])


def _matches_target(state, owner, candidate, spec):
    filters = spec.get("filter", {})
    if "friendly" in filters and (candidate.side == owner.side) != filters["friendly"]:
        return False
    # `is` and `not` mean here what they already mean in an event's selector: one vocabulary
    # reaching a second place, rather than a second vocabulary.
    if "is" in filters and candidate.definition.id != filters["is"]:
        return False
    if "not" in filters and candidate.definition.id == filters["not"]:
        return False
    if any(status in candidate.statuses for status in filters.get("not_status", ())):
        return False
    return True


def _effect_actions(state, owner, effects, selected):
    effects = effects if isinstance(effects, list) else [effects]
    actions = []
    current = owner
    current_pos = owner.pos
    for effect in effects:
        if effect.get("when", {}).get("at_promotion_rank") is True:
            if state.board.sides[current.side].promotes_at != current_pos[0]:
                continue
        kind = effect["type"]
        # An effect may aim somewhere other than the ability did. Previously only apply_status
        # could, which is why rook_shield's file calls itself "the one piece of base content whose
        # effect acts on something other than what the ability targeted" — that was a limit of the
        # interpreter, not a property of the content. One rule now, applied to every effect:
        # declare `target:` to re-select, or inherit what the ability chose.
        targeted = _select(state, owner, effect["target"], None) if "target" in effect else selected
        if kind == "destroy":
            actions.extend(Remove(piece) for piece in targeted)
        elif kind == "swap":
            if len(selected) != 1:
                raise ValueError("swap needs one selected target")
            actions.append(Swap(owner, selected[0]))
        elif kind == "move":
            if len(selected) != 1 or not isinstance(selected[0], tuple):
                raise ValueError("move needs one empty destination")
            actions.append(Relocate(owner, selected[0]))
            current = owner
            current_pos = selected[0]
        elif kind == "transform":
            target = current if effect.get("target") == "self" else selected[0]
            destination = qualify(effect["into"], target.definition.id)
            replacement = Piece(target.uid, state.piece_defs[destination], target.side, current_pos, target.has_moved, dict(target.statuses))
            actions.append(Replace(target, replacement))
            current = replacement
        elif kind == "apply_status":
            status_id = qualify(effect["status"], owner.definition.id)
            definition = state.status_defs[status_id]
            actions.extend(SetStatus(piece, StatusInstance(definition, None)) for piece in targeted)
        else:
            raise ValueError(f"unsupported effect '{kind}'")
    return actions
