"""The small, action-safe surface handed to a registered move-type function."""

from __future__ import annotations

from .actions import Relocate, Remove
from .move import Move


class MoveContext:
    """Read board state and construct actions without giving a mod a mutation path."""

    def __init__(self, state):
        self._state = state

    @property
    def last_move(self):
        return self._state.last_move

    def side(self, piece):
        return self._state.board.sides[piece.side]

    def inside(self, square):
        return self._state.board.inside(square)

    def at(self, square):
        return self._state.board.at(square)

    def pieces(self):
        return tuple(self._state.board.pieces())

    def matches(self, piece, selector):
        tags = selector.get("tag_any", ())
        return not tags or any(tag in piece.definition.components for tag in tags)

    def move(self, piece, target, *, remove=(), extra=(), captured=None):
        actions = [*(Remove(item) for item in remove), Relocate(piece, target), *extra]
        return Move(piece, piece.pos, target, actions, captured)

    def relocate(self, piece, target):
        """Create a relocation action for a compound move without exposing imports."""
        return Relocate(piece, target)

    def safe_after(self, side, actions):
        from .movegen import _apply, _undo, threatened

        temporary = Move(None, (), (), list(actions))
        _apply(temporary, self._state)
        safe = not threatened(self._state, side)
        _undo(temporary, self._state)
        return safe
