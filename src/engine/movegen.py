"""Generic slide/leap move generation with a separate threat path."""

from __future__ import annotations

from .actions import Relocate, Remove
from .move import Move
from .status import capturable, effective_moves
from .verbs import MoveContext
from src.modding.registries import qualify


_DIRECTIONS = {
    "orthogonal": ((-1, 0), (1, 0), (0, -1), (0, 1)),
    "diagonal": ((-1, -1), (-1, 1), (1, -1), (1, 1)),
}


def legal_moves(state):
    moves = []
    for piece in state.board.pieces():
        if piece.side == state.current_side:
            for move in pseudo_moves(state, piece):
                _apply(move, state)
                safe = not threatened(state, piece.side)
                _undo(move, state)
                if safe:
                    moves.append(_attach_choices(state, move))
    return moves


def pseudo_moves(state, piece, *, threat=False):
    moves = []
    for part in effective_moves(piece):
        if part.get("type") == "slide":
            moves.extend(_slides(state, piece, part, threat))
        elif part.get("type") == "leap":
            moves.extend(_leaps(state, piece, part, threat))
        else:
            moves.extend(_registered_moves(state, piece, part, threat))
    if len(piece.definition.components) > 1:
        moves = _without_duplicate_destinations(moves)
    return moves


def _without_duplicate_destinations(moves):
    """Drop repeats a composed piece's overlapping parts produce.

    A queen that absorbs a rook contributes orthogonal slides twice, and the same square must not be
    offered as two moves — the UI would draw one marker over another and perft would double-count.
    Deliberately confined to multi-component pieces so single-component generation, which the perft
    oracle measures, produces the identical list it always has.
    """
    seen, unique = set(), []
    for move in moves:
        key = (move.start, move.end)
        if key not in seen:
            seen.add(key)
            unique.append(move)
    return unique


def threatened(state, side):
    royal = state.royal_piece(side)
    for piece in state.board.pieces():
        if piece.side != side:
            if any(move.end == royal.pos for move in pseudo_moves(state, piece, threat=True)):
                return True
    return False


def _directions(part, side):
    forward = side.forward
    name = part["dirs"]
    if name == "all":
        return _DIRECTIONS["orthogonal"] + _DIRECTIONS["diagonal"]
    if name == "forward": return ((forward, 0),)
    if name == "forward_diagonal": return ((forward, -1), (forward, 1))
    return _DIRECTIONS[name]


def _slides(state, piece, part, threat):
    out = []
    limit = max(state.board.rows, state.board.columns) if part.get("limit") == "unlimited" else part.get("limit", 1)
    capture = part.get("capture", "allowed")
    for dr, dc in _directions(part, state.board.sides[piece.side]):
        for distance in range(1, limit + 1):
            # A conditional multi-square move (the pawn's opening move) names
            # its destination, not every square on the way there. Intervening
            # squares are still inspected, so a piece cannot be jumped over.
            destination_only = part.get("when", {}).get("has_moved") is False and distance != limit
            target = (piece.pos[0] + dr * distance, piece.pos[1] + dc * distance)
            if not state.board.inside(target): break
            occupant = state.board.at(target)
            if threat and capture != False:
                out.append(_move(piece, target, None))
            if occupant is None:
                if not threat and not destination_only and capture != "only" and _when(piece, part): out.append(_move(piece, target, None))
                continue
            if occupant.side != piece.side and capturable(occupant) and capture != False and _when(piece, part):
                if not threat: out.append(_move(piece, target, occupant))
            break
    return out


def _leaps(state, piece, part, threat):
    out = []
    forward = state.board.sides[piece.side].forward
    for rel_row, rel_col in part["offsets"]:
        target = (piece.pos[0] + rel_row * forward, piece.pos[1] + rel_col)
        if not state.board.inside(target): continue
        occupant = state.board.at(target)
        if threat: out.append(_move(piece, target, None)); continue
        if occupant is None or (occupant.side != piece.side and capturable(occupant)):
            out.append(_move(piece, target, occupant))
    return out


def _registered_moves(state, piece, part, threat):
    """Dispatch an opaque data verb registered by the piece's owning namespace."""
    if state.move_types is None:
        return []
    verb_id = qualify(part["type"], piece.definition.id)
    entry = state.move_types.get(verb_id)
    if entry is None:
        raise ValueError(f"unknown move type '{part['type']}' for '{piece.definition.id}'")
    move_type = entry.value
    if threat and not move_type.threatens:
        return []
    return list(move_type.generate(MoveContext(state), piece, part, threat))


def _when(piece, part):
    return not (part.get("when", {}).get("has_moved") is False and piece.has_moved)


def _move(piece, target, captured):
    actions = ([Remove(captured)] if captured is not None else []) + [Relocate(piece, target)]
    return Move(piece, piece.pos, target, actions, captured)


def _attach_choices(state, move):
    """Expose data-declared move-completion choices before applying the move."""
    side = state.board.sides[move.piece.side]
    for reaction in move.piece.definition.properties.get("on", ()):
        if reaction.get("trigger") != "moved":
            continue
        if reaction.get("when", {}).get("at_promotion_rank") is not True:
            continue
        if side.promotes_at != move.end[0]:
            continue
        effect = reaction.get("effect", {})
        if effect.get("type") == "transform" and effect.get("choose") == "mover":
            options = tuple(qualify(option, move.piece.definition.id) for option in effect["into"])
            move.choices = options
    return move


def _apply(move, state):
    for action in move.actions: action.apply(state)


def _undo(move, state):
    for action in reversed(move.actions): action.undo(state)
