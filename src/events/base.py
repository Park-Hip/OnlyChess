"""Base event contracts and snapshot models for the event subsystem."""

from dataclasses import dataclass, field

import copy


@dataclass
class EventStateSnapshot:
    """Store the state needed to restore the event layer after undo."""

    move_log_len: int
    grid_copy: list
    resolved_event_key: str
    queued_event_key: str | None
    active_event_keys: list[str] = field(default_factory=list)
    event_snapshot_data: dict | None = None

    @classmethod
    def from_game_state(cls, game_state, resolved_event_key, queued_event_key, active_event_keys, event_snapshot_data=None):
        """Build a snapshot from the current game state before an event executes."""
        return cls(
            move_log_len=len(game_state.move_log),
            grid_copy=copy.deepcopy(game_state.board.grid),
            resolved_event_key=resolved_event_key,
            queued_event_key=queued_event_key,
            active_event_keys=list(active_event_keys),
            event_snapshot_data=event_snapshot_data or {},
        )


class ChessEvent:
    """Base class for all special events in the game."""

    event_key = "base_event"

    def __init__(self, game_state):
        self.gs = game_state
        self.name = "Base Event"
        self.duration = 0
        self.warning_active = False

    def trigger_warning(self):
        """Mark the event as announced to the player."""
        self.warning_active = True

    def execute(self):
        """Apply the event effect."""
        self.warning_active = False

    def cleanup(self):
        """Clean up event state after it resolves."""

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw event-specific UI feedback when needed."""

    def build_snapshot_data(self):
        """Return extra event-specific state needed for restoration."""
        return {}

    def restore_from_snapshot_data(self, snapshot_data):
        """Restore extra event-specific state after undo if needed."""
        self.warning_active = snapshot_data.get("warning_active", self.warning_active)
