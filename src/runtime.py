"""Application-facing mode catalog and session boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .engine import Pipeline, build_state
from .engine.actions import ClearStatus, SetPendingEvent, SetStatus
from .engine.movegen import threatened
from .modding.loader import LoadResult, activate, load
from .notation import history
from .presentation import PresentationNotification, PresentationPiece, PresentationSnapshot, PresentationWarning


def consequence_kinds(record) -> list[str]:
    """Map recorded state consequences to presentation notifications once each.

    The action log is the observation boundary: effects only need to emit reversible
    actions, and this scan remains useful for content the engine does not otherwise know.
    """
    found = set()
    for action in record:
        if isinstance(action, SetStatus):
            found.add("status_applied")
        elif isinstance(action, ClearStatus):
            found.add("status_expired")
        elif isinstance(action, SetPendingEvent):
            found.add("event_warning" if action.event_id is not None else "event_executed")
    return [kind for kind in ("status_applied", "status_expired", "event_warning", "event_executed") if kind in found]


@dataclass(frozen=True)
class ModeCatalogEntry:
    """Read-only data needed by the menu to offer one fully linked game mode."""

    id: str
    name: str
    rows: int
    columns: int
    palette: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ApplicationContext:
    """The startup-loaded mod set shared by every screen and session."""

    load_result: LoadResult
    modes: tuple[ModeCatalogEntry, ...]

    @property
    def installed(self):
        """Read-only summaries of every selected installed mod."""
        return self.load_result.installed

    @property
    def errors(self):
        """Loader errors retained for the read-only trust/error surface."""
        return tuple(self.load_result.errors)

    @classmethod
    def load(cls, mods_dir: Path | None = None) -> "ApplicationContext":
        mods_dir = mods_dir or Path(__file__).resolve().parent.parent / "mods"
        result = load(mods_dir, validate=True, link=True)
        if result.errors:
            return cls(result, ())
        activate(result)
        assert result.linked is not None
        entries = []
        for mode_id, linked in result.linked.modes.items():
            parsed = result.registries.content["game_mode"].get(mode_id).value.tree
            palette = {}
            presentation = parsed.get("presentation", {})
            theme_id = presentation.get("theme") if isinstance(presentation, dict) else None
            if theme_id:
                palette = dict(result.registries.content["theme"].get(theme_id).value.tree.get("palette", {}))
            entries.append(ModeCatalogEntry(mode_id, parsed["name"], linked.board.rows, linked.board.columns, palette))
        return cls(result, tuple(sorted(entries, key=lambda item: (item.name.casefold(), item.id))))

    def mode(self, mode_id: str) -> ModeCatalogEntry:
        for entry in self.modes:
            if entry.id == mode_id:
                return entry
        raise ValueError(f"game mode '{mode_id}' is not in the loaded mode catalog")


class EngineSession:
    """A playable selected mode; loading belongs to :class:`ApplicationContext`."""

    def __init__(self, load_result: LoadResult, mode_id: str, *, time_limit: float | None = None):
        if load_result.linked is None or mode_id not in load_result.linked.modes:
            raise ValueError(f"game mode '{mode_id}' is not linked in this loaded mod set")
        self.loaded_mods = load_result.mods
        self.load_result = load_result
        self.mode_id = mode_id
        self.state = build_state(load_result.registries, mode_id)
        self.pipeline = Pipeline(self.state)
        self.notifications: list[PresentationNotification] = []
        # Clocks live on the session, deliberately outside EngineState and the action log.
        #
        # Undo reverses the log, so a clock recorded there would hand back the time spent on the
        # move being taken back — turning undo into a way to buy thinking time. Time is the one
        # thing in this game that is not a move and cannot be unmade, so it is not an action.
        # `time_limit` of None means the mode has no clock at all, which is every mode today.
        self.time_limit = time_limit
        self.clocks = {side: float(time_limit) for side in self.state.board.sides} if time_limit else {}
        self.flagged = None

    def tick(self, elapsed: float):
        """Charge `elapsed` seconds to whoever is to move. Callers pass real time; nothing here
        reads a wall clock, so a test can play out an entire time scramble deterministically."""
        if not self.clocks or self.flagged or self.outcome:
            return
        side = self.state.current_side
        self.clocks[side] = max(0.0, self.clocks[side] - elapsed)
        if self.clocks[side] == 0.0:
            self.flagged = side
            self.notifications.append(PresentationNotification("outcome_reached", self.mode_id))

    @property
    def legal_moves(self):
        return self.pipeline.legal_moves()

    def moves_from(self, square):
        return [move for move in self.legal_moves if move.start == square]

    def move(self, start, end, *, choice=None):
        candidates = [move for move in self.legal_moves if move.start == start and move.end == end]
        if not candidates:
            raise ValueError("that move is not legal")
        record = self.pipeline.apply(candidates[0], choice=choice)
        # One notification per player action, most-specific kind first: a promotion is
        # reported as a promotion (not the move/capture it also is) so a mod can cue it.
        kind = "promotion_chosen" if choice else ("capture_completed" if candidates[0].captured else "move_completed")
        self.notifications.append(PresentationNotification(kind, self.mode_id, end, candidates[0].piece.definition.id))
        self.notifications.extend(PresentationNotification(consequence, self.mode_id) for consequence in consequence_kinds(record))
        self._notify_outcome()
        return record

    def undo(self):
        if not self.state.action_log:
            return False
        self.pipeline.undo_last()
        self.notifications.append(PresentationNotification("undo_completed", self.mode_id))
        return True

    def abilities_for(self, square):
        piece = self.state.board.at(square)
        if piece is None:
            return ()
        return tuple(
            ability_id for ability_id, ability in self.state.ability_defs.items()
            if not ability.owner.get("tag_any") or any(tag in piece.definition.components for tag in ability.owner["tag_any"])
        )

    def use_ability(self, square, ability_id, *, target=None):
        owner = self.state.board.at(square)
        if owner is None:
            raise ValueError("select a piece before choosing an ability")
        record = self.pipeline.use_ability(owner, ability_id, target=target)
        self.notifications.append(PresentationNotification("ability_used", self.mode_id, owner.pos, owner.definition.id))
        self.notifications.extend(PresentationNotification(consequence, self.mode_id) for consequence in consequence_kinds(record))
        self._notify_outcome()
        return record

    def _notify_outcome(self):
        """Emit `outcome_reached` once when an action leaves the game in a terminal
        position. Reads the same computed `outcome` the UI shows; no state is mutated."""
        if self.outcome is not None:
            self.notifications.append(PresentationNotification("outcome_reached", self.mode_id))

    def presentation_snapshot(self, *, prompt: str | None = None, glyph=None):
        board = self.state.board
        pieces = tuple(PresentationPiece(piece.definition.id, piece.side, piece.pos, tuple(sorted(piece.statuses))) for piece in board.pieces())
        resources = tuple(sorted((f"{side}:{resource}", value) for side, values in self.state.resources.items() for resource, value in values.items()))
        clocks = tuple((board.sides[side].name, remaining) for side, remaining in self.clocks.items())
        material = tuple((board.sides[side].name, sum(piece.definition.material for piece in board.pieces() if piece.side == side)) for side in board.sides)
        last = self.state.last_move
        return PresentationSnapshot(
            self.mode_id, board.rows, board.columns, board.sides[self.state.current_side].name,
            pieces, resources, tuple(self.state.event_messages), prompt, self.outcome, clocks,
            (last.start, last.end) if last is not None else None,
            material, self.state.completed_turns, self._event_countdown(),
            tuple((board.sides[side].name, tuple(self.state.captures.get(side, ()))) for side in board.sides),
            # A caller that can resolve glyphs gets readable history; one that cannot gets ids,
            # which keeps the session usable without the presentation runtime attached.
            history(self.state, glyph or (lambda piece_id: piece_id.rsplit(":", 1)[-1][:1].upper())),
            self._pending_warning(),
            tuple(sorted(((side_id, side.name) for side_id, side in board.sides.items()), key=lambda seat: not board.sides[seat[0]].moves_first)),
        )

    def _pending_warning(self):
        """The announced event and whatever it has already committed to.

        A zone bound at warning time is a real promise — those squares will be hit — so it can be
        shown. An event that selects at execution has promised nothing yet, and the honest answer is
        a name with no squares rather than a guess drawn on the board.
        """
        for pool_id, event_id in self.state.pending_events.items():
            if event_id is None:
                continue
            squares = []
            for binding in self.state.pending_bindings.get(pool_id, {}).values():
                if isinstance(binding, tuple) and len(binding) == 4:
                    row, col, height, width = binding
                    squares.extend((r, c) for r in range(row, row + height) for c in range(col, col + width))
            name = self.state.event_defs.get(event_id, {}).get("name", event_id.rsplit(":", 1)[-1])
            return PresentationWarning(name, tuple(squares))
        return None

    def _event_countdown(self):
        """Moves until the soonest active pool executes, or None when no pool is scheduled.

        Derived from the pool's own schedule rather than stored, so it cannot drift out of step
        with the turn counter it is describing, and undo needs to know nothing about it.
        """
        countdowns = []
        for pool_id in self.state.active_pools:
            pool = self.state.event_pools.get(pool_id)
            if not pool or not pool.get("every"):
                continue
            every = pool["every"]
            countdowns.append(every - (self.state.pool_turns.get(pool_id, 0) % every))
        return min(countdowns) if countdowns else None

    def drain_notifications(self):
        notices, self.notifications = tuple(self.notifications), []
        return notices

    @property
    def outcome(self):
        # Checked before legality: a flag falls whatever the position is, and asking for legal moves
        # first would call it stalemate when a player simply ran out of time in a dead position.
        if self.flagged is not None:
            return f"{self.state.board.sides[self.flagged].name} ran out of time"
        if self.legal_moves:
            return None
        side = self.state.board.sides[self.state.current_side].name
        return f"{side} is checkmated" if threatened(self.state, self.state.current_side) else "Stalemate"
