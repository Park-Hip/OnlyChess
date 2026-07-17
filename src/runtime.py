"""Application-facing session built from the public mod-loader and engine APIs.

The pygame layer uses this object instead of reaching into legacy game classes.
It is deliberately small: presentation chooses a move, while the pipeline owns
legality, turn changes, events, fusion, and undo.
"""

from __future__ import annotations

from pathlib import Path

from .engine import Pipeline, build_state
from .engine.movegen import threatened
from .modding.loader import load


DEFAULT_MODS = ("base:chess", "base:fusion", "base:events")
DEFAULT_MODE = "base:advanced"


class EngineSession:
    """A playable mod-defined game and its user-facing operation boundary."""

    def __init__(self, *, mods_dir: Path | None = None, enabled_mod_ids=DEFAULT_MODS, mode_id=DEFAULT_MODE):
        mods_dir = mods_dir or Path(__file__).resolve().parent.parent / "mods"
        result = load(mods_dir, enabled_mod_ids=enabled_mod_ids, validate=True, link=True)
        result.raise_if_failed()
        self.loaded_mods = result.mods
        self.mode_id = mode_id
        self.state = build_state(result.registries, mode_id)
        self.pipeline = Pipeline(self.state)

    @property
    def legal_moves(self):
        """Return the currently legal moves, calculated by the engine."""
        return self.pipeline.legal_moves()

    def moves_from(self, square):
        """Return legal moves beginning on one board square."""
        return [move for move in self.legal_moves if move.start == square]

    def move(self, start, end, *, choice=None):
        """Apply the one legal move matching a player selection."""
        candidates = [move for move in self.legal_moves if move.start == start and move.end == end]
        if not candidates:
            raise ValueError("that move is not legal")
        return self.pipeline.apply(candidates[0], choice=choice)

    def undo(self):
        """Undo the complete last turn, including any scheduled event actions."""
        if not self.state.action_log:
            return False
        self.pipeline.undo_last()
        return True

    def abilities_for(self, square):
        """Return content-defined abilities available to the selected piece."""
        piece = self.state.board.at(square)
        if piece is None:
            return ()
        return tuple(
            ability_id
            for ability_id, ability in self.state.ability_defs.items()
            if not ability.owner.get("tag_any")
            or any(tag in piece.definition.components for tag in ability.owner["tag_any"])
        )

    def use_ability(self, square, ability_id, *, target=None):
        """Use one loaded ability; target validation stays in the engine."""
        owner = self.state.board.at(square)
        if owner is None:
            raise ValueError("select a piece before choosing an ability")
        return self.pipeline.use_ability(owner, ability_id, target=target)

    @property
    def outcome(self):
        """Describe a terminal position without embedding chess rules in the UI."""
        if self.legal_moves:
            return None
        if threatened(self.state, self.state.current_side):
            return f"{self.state.current_side} is checkmated"
        return "Stalemate"
