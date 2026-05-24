"""Base event contract for the event subsystem."""


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

    def tick(self):
        """Advance any per-turn event state."""

    def draw(self, screen, font, width, height, info_panel_height):
        """Draw event-specific UI feedback when needed."""
