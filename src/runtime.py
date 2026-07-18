"""Application-facing mode catalog and session boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .engine import Pipeline, build_state
from .engine.movegen import threatened
from .modding.loader import LoadResult, activate, load
from .presentation import PresentationNotification, PresentationPiece, PresentationSnapshot


@dataclass(frozen=True)
class ModeCatalogEntry:
    """Read-only data needed by the menu to offer one fully linked game mode."""

    id: str
    name: str
    rows: int
    columns: int


@dataclass(frozen=True)
class ApplicationContext:
    """The startup-loaded mod set shared by every screen and session."""

    load_result: LoadResult
    modes: tuple[ModeCatalogEntry, ...]

    @classmethod
    def load(cls, mods_dir: Path | None = None) -> "ApplicationContext":
        mods_dir = mods_dir or Path(__file__).resolve().parent.parent / "mods"
        result = load(mods_dir, validate=True, link=True)
        activate(result)
        assert result.linked is not None
        entries = []
        for mode_id, linked in result.linked.modes.items():
            parsed = result.registries.content["game_mode"].get(mode_id).value.tree
            entries.append(ModeCatalogEntry(mode_id, parsed["name"], linked.board.rows, linked.board.columns))
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
        self.notifications.append(PresentationNotification("capture_completed" if candidates[0].captured else "move_completed", self.mode_id, end, candidates[0].piece.definition.id))
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
        return record

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
