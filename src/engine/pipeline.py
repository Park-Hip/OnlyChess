"""Apply, simulate, and undo moves through the one action path."""

from .actions import AdjustResource, AdvanceTurn, CountMove, RecordAbility, RecordCapture, RecordMove, Replace
from .abilities import build_ability_actions
from .piece import Piece
from .bus import Bus, Capture
from .movegen import _apply, _undo, legal_moves
from .status import expiry_actions
from .fusion import FusionResolver
from .events import EventRunner


class Pipeline:
    def __init__(self, state, bus=None):
        self.state = state
        self.bus = bus or Bus()
        self.events = EventRunner(state)
        if state.fusion_defs:
            self.bus.listen(FusionResolver(state))

    def legal_moves(self):
        return legal_moves(self.state)

    def simulate(self, move):
        _apply(move, self.state)
        _undo(move, self.state)

    def apply(self, move, *, choice=None):
        if move.piece.side != self.state.current_side:
            raise ValueError("a side may only act on its own turn")
        self._apply_choice(move, choice)
        _apply(move, self.state)
        reactions = []
        if move.captured is not None:
            credit = RecordCapture(move.piece.side, move.captured.definition.id)
            credit.apply(self.state)
            reactions = [credit, *self.bus.emit(Capture(move.piece, move.captured, displaced=True))]
            for action in reactions[1:]:
                action.apply(self.state)
        turn = AdvanceTurn(); turn.apply(self.state)
        expiry = expiry_actions(self.state, move.piece.side)
        for action in expiry:
            action.apply(self.state)
        counted = CountMove(move.piece.side); counted.apply(self.state)
        gains = []
        for resource in self.state.resource_defs.values():
            every = resource.gain.get("every_moves")
            if every and self.state.move_counts[move.piece.side] % every == 0:
                gain = AdjustResource(move.piece.side, resource.id, resource.gain["amount"])
                gain.apply(self.state)
                gains.append(gain)
        event_actions = []
        event_mode_pools = getattr(self.state, "active_pools", ())
        for pool_id in event_mode_pools:
            _, _, scheduled = self.events.advance_pool(pool_id)
            for action in scheduled:
                action.apply(self.state)
            event_actions.extend(scheduled)
        previous = RecordMove(move); previous.apply(self.state)
        record = [*move.actions, *reactions, turn, *expiry, counted, *gains, *event_actions, previous]
        self.state.action_log.append(record)
        return record

    def undo_last(self):
        for action in reversed(self.state.action_log.pop()):
            action.undo(self.state)

    def use_ability(self, owner, ability_id, *, target=None):
        if owner.side != self.state.current_side:
            raise ValueError("a side may only act on its own turn")
        ability = self.state.ability_defs[ability_id]
        costs = [AdjustResource(owner.side, resource_id, -amount) for resource_id, amount in ability.cost.items()]
        if any(self.state.resources[owner.side][cost.resource_id] < -cost.amount for cost in costs):
            raise ValueError("insufficient resources")
        actions = [*costs, *build_ability_actions(self.state, owner, ability, target)]
        for action in actions:
            action.apply(self.state)
        turn = AdvanceTurn(); turn.apply(self.state)
        expiry = expiry_actions(self.state, owner.side)
        for action in expiry:
            action.apply(self.state)
        noted = RecordAbility(owner.definition.id, owner.pos, ability.name, ", ".join(f"-{amount} {resource.rsplit(':', 1)[-1]}" for resource, amount in ability.cost.items()))
        record = [*actions, turn, *expiry, noted]
        self.state.action_log.append(record)
        return record

    def _apply_choice(self, move, choice):
        if not move.choices:
            if choice is not None:
                raise ValueError("this move has no choice")
            return
        if choice not in move.choices:
            raise ValueError(f"choose one of: {', '.join(move.choices)}")
        if move.selected_choice is not None:
            if move.selected_choice != choice:
                raise ValueError("a move's choice cannot change after it has been prepared")
            return
        replacement_def = self.state.piece_defs[choice]
        replacement = Piece(
            move.piece.uid,
            replacement_def,
            move.piece.side,
            move.end,
            has_moved=move.piece.has_moved,
            statuses=dict(move.piece.statuses),
        )
        move.actions.append(Replace(move.piece, replacement))
        move.selected_choice = choice
