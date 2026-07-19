"""Reversible state transitions. No engine caller mutates board state directly."""

from __future__ import annotations

from dataclasses import dataclass

from .piece import Piece, StatusInstance


@dataclass
class Relocate:
    piece: Piece
    target: tuple[int, int]
    previous: tuple[int, int] | None = None
    previous_has_moved: bool | None = None

    def apply(self, state) -> None:
        self.previous = self.piece.pos
        self.previous_has_moved = self.piece.has_moved
        state.board.remove(self.previous)
        state.board.place(self.piece, self.target)
        self.piece.has_moved = True

    def undo(self, state) -> None:
        state.board.remove(self.target)
        state.board.place(self.piece, self.previous)
        self.piece.has_moved = self.previous_has_moved


@dataclass
class Remove:
    piece: Piece
    square: tuple[int, int] | None = None

    def apply(self, state) -> None:
        self.square = self.piece.pos
        state.board.remove(self.square)

    def undo(self, state) -> None:
        state.board.place(self.piece, self.square)


@dataclass
class Replace:
    """Swap a board piece while retaining enough information to undo it."""

    old: Piece
    new: Piece
    square: tuple[int, int] | None = None

    def apply(self, state) -> None:
        self.square = self.old.pos
        state.board.remove(self.square)
        state.board.place(self.new, self.square)

    def undo(self, state) -> None:
        state.board.remove(self.square)
        state.board.place(self.old, self.square)


@dataclass
class SetStatus:
    piece: Piece
    instance: StatusInstance
    previous: StatusInstance | None = None

    def apply(self, state) -> None:
        self.previous = self.piece.statuses.get(self.instance.definition.id)
        self.piece.statuses[self.instance.definition.id] = self.instance

    def undo(self, state) -> None:
        if self.previous is None:
            self.piece.statuses.pop(self.instance.definition.id, None)
        else:
            self.piece.statuses[self.instance.definition.id] = self.previous


@dataclass
class ClearStatus:
    piece: Piece
    status_id: str
    previous: StatusInstance | None = None

    def apply(self, state) -> None:
        self.previous = self.piece.statuses.pop(self.status_id, None)

    def undo(self, state) -> None:
        if self.previous is not None:
            self.piece.statuses[self.status_id] = self.previous


@dataclass
class TickStatus:
    """Reduce a duration without mutating a status outside the action log."""

    piece: Piece
    status_id: str
    previous: int | None = None

    def apply(self, state) -> None:
        instance = self.piece.statuses[self.status_id]
        self.previous = instance.remaining
        if instance.remaining is not None:
            instance.remaining -= 1

    def undo(self, state) -> None:
        instance = self.piece.statuses.get(self.status_id)
        if instance is not None:
            instance.remaining = self.previous


@dataclass
class AdvanceTurn:
    previous: str | None = None

    def apply(self, state) -> None:
        self.previous = state.current_side
        sides = list(state.board.sides)
        state.current_side = sides[(sides.index(state.current_side) + 1) % len(sides)]

    def undo(self, state) -> None:
        state.current_side = self.previous


@dataclass
class RecordCapture:
    """Credit a captured piece to the side that took it.

    Kept as an action rather than derived, unlike the other presentation data, because it cannot be
    derived: a piece is gone from the board whether it was captured or destroyed by an event, and
    only the capture path knows which happened. Recording it here keeps undo working the same way
    everything else does — the list reverses with the move that filled it.
    """

    side: str
    piece_id: str

    def apply(self, state) -> None:
        state.captures.setdefault(self.side, []).append(self.piece_id)

    def undo(self, state) -> None:
        state.captures[self.side].pop()


@dataclass
class RecordAbility:
    """Note that an ability was used, for history that would otherwise be unreadable.

    An ability's record is a list of costs and effects with nothing naming what was invoked, so a
    log derived from it could say a piece lost 2 AP and two pieces swapped, but never that it was
    Knight Swap. Carries only what history needs, and reverses like everything else.
    """

    piece_id: str
    square: tuple[int, int]
    name: str
    cost: str = ""
    #: Where the ability acted. Recorded because an ability that moves its owner leaves no other
    #: trace of where it started, and a log saying only where the piece ended is worse than none.
    targets: tuple[tuple[int, int], ...] = ()
    #: The effect verb invoked — engine vocabulary such as `swap` or `destroy`, never a content
    #: name — so history can write what happened without knowing which ability did it.
    verb: str = ""

    def apply(self, state) -> None:
        pass

    def undo(self, state) -> None:
        pass


@dataclass
class RecordMove:
    """Make the previous completed move available to history-aware mod verbs."""

    move: object
    previous: object | None = None

    def apply(self, state) -> None:
        self.previous = state.last_move
        state.last_move = self.move

    def undo(self, state) -> None:
        state.last_move = self.previous


@dataclass
class AdjustResource:
    side: str
    resource_id: str
    amount: int
    previous: int | None = None

    def apply(self, state) -> None:
        self.previous = state.resources[self.side][self.resource_id]
        maximum = state.resource_defs[self.resource_id].maximum
        state.resources[self.side][self.resource_id] = max(0, min(maximum, self.previous + self.amount))

    def undo(self, state) -> None:
        state.resources[self.side][self.resource_id] = self.previous


@dataclass
class CountMove:
    side: str
    previous: int | None = None

    def apply(self, state) -> None:
        self.previous = state.move_counts[self.side]
        state.move_counts[self.side] += 1

    def undo(self, state) -> None:
        state.move_counts[self.side] = self.previous


@dataclass
class Swap:
    first: Piece
    second: Piece
    first_square: tuple[int, int] | None = None
    second_square: tuple[int, int] | None = None

    def apply(self, state) -> None:
        self.first_square, self.second_square = self.first.pos, self.second.pos
        state.board.remove(self.first_square)
        state.board.remove(self.second_square)
        state.board.place(self.first, self.second_square)
        state.board.place(self.second, self.first_square)

    def undo(self, state) -> None:
        state.board.remove(self.second_square)
        state.board.remove(self.first_square)
        state.board.place(self.first, self.first_square)
        state.board.place(self.second, self.second_square)


@dataclass
class SetSide:
    piece: Piece
    side: str
    previous: str | None = None

    def apply(self, state) -> None:
        self.previous = self.piece.side
        self.piece.side = self.side

    def undo(self, state) -> None:
        self.piece.side = self.previous


@dataclass
class SetPoolTurn:
    pool_id: str
    value: int
    previous: int | None = None

    def apply(self, state) -> None:
        self.previous = state.pool_turns[self.pool_id]
        state.pool_turns[self.pool_id] = self.value

    def undo(self, state) -> None:
        state.pool_turns[self.pool_id] = self.previous


@dataclass
class SetPendingEvent:
    pool_id: str
    event_id: str | None
    previous: str | None = None

    def apply(self, state) -> None:
        self.previous = state.pending_events.get(self.pool_id)
        if self.event_id is None:
            state.pending_events.pop(self.pool_id, None)
        else:
            state.pending_events[self.pool_id] = self.event_id

    def undo(self, state) -> None:
        if self.previous is None:
            state.pending_events.pop(self.pool_id, None)
        else:
            state.pending_events[self.pool_id] = self.previous


@dataclass
class SetPendingBindings:
    pool_id: str
    bindings: dict[str, object] | None
    previous: dict[str, object] | None = None

    def apply(self, state) -> None:
        self.previous = state.pending_bindings.get(self.pool_id)
        if self.bindings is None:
            state.pending_bindings.pop(self.pool_id, None)
        else:
            state.pending_bindings[self.pool_id] = dict(self.bindings)

    def undo(self, state) -> None:
        if self.previous is None:
            state.pending_bindings.pop(self.pool_id, None)
        else:
            state.pending_bindings[self.pool_id] = self.previous


@dataclass
class AppendMessage:
    message: str

    def apply(self, state) -> None:
        state.event_messages.append(self.message)

    def undo(self, state) -> None:
        state.event_messages.pop()
