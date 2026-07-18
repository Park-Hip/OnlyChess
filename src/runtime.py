"""Application-facing mode catalog and session boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .engine import Pipeline, build_state
from .engine.actions import ClearStatus, SetPendingEvent, SetStatus
from .engine.movegen import threatened
from .modding.loader import LoadResult, activate, load
from .presentation import PresentationNotification, PresentationPiece, PresentationSnapshot


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

    def __init__(self, load_result: LoadResult, mode_id: str):
        if load_result.linked is None or mode_id not in load_result.linked.modes:
            raise ValueError(f"game mode '{mode_id}' is not linked in this loaded mod set")
        self.loaded_mods = load_result.mods
        self.load_result = load_result
        self.mode_id = mode_id
        self.state = build_state(load_result.registries, mode_id)
        self.pipeline = Pipeline(self.state)
        self.notifications: list[PresentationNotification] = []

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

    def presentation_snapshot(self, *, prompt: str | None = None):
        board = self.state.board
        pieces = tuple(PresentationPiece(piece.definition.id, piece.side, piece.pos, tuple(sorted(piece.statuses))) for piece in board.pieces())
        resources = tuple(sorted((f"{side}:{resource}", value) for side, values in self.state.resources.items() for resource, value in values.items()))
        return PresentationSnapshot(self.mode_id, board.rows, board.columns, board.sides[self.state.current_side].name, pieces, resources, tuple(self.state.event_messages), prompt, self.outcome)

    def drain_notifications(self):
        notices, self.notifications = tuple(self.notifications), []
        return notices

    @property
    def outcome(self):
        if self.legal_moves:
            return None
        side = self.state.board.sides[self.state.current_side].name
        return f"{side} is checkmated" if threatened(self.state, self.state.current_side) else "Stalemate"
