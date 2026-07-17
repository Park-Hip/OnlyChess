"""Apply, simulate, and undo moves through the one action path."""

from .actions import AdvanceTurn
from .bus import Bus, Capture
from .movegen import _apply, _undo, legal_moves
from .status import expiry_actions


class Pipeline:
    def __init__(self, state, bus=None):
        self.state = state
        self.bus = bus or Bus()

    def legal_moves(self):
        return legal_moves(self.state)

    def simulate(self, move):
        _apply(move, self.state)
        _undo(move, self.state)

    def apply(self, move):
        if move.piece.side != self.state.current_side:
            raise ValueError("a side may only act on its own turn")
        _apply(move, self.state)
        if move.captured is not None:
            self.bus.emit(Capture(move.piece, move.captured, displaced=True))
        turn = AdvanceTurn(); turn.apply(self.state)
        expiry = expiry_actions(self.state, move.piece.side)
        for action in expiry:
            action.apply(self.state)
        record = [*move.actions, turn, *expiry]
        self.state.action_log.append(record)
        return record

    def undo_last(self):
        for action in reversed(self.state.action_log.pop()):
            action.undo(self.state)
