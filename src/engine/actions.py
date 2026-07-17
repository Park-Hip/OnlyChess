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
