"""Small bounded message log for player-facing gameplay feedback."""


class GameMessageLog:
    """Store recent gameplay messages for the UI panel."""

    def __init__(self, max_messages=5):
        self.max_messages = max_messages
        self._messages = []

    def add(self, message):
        """Add one non-empty message and keep only the newest entries."""
        if not message:
            return
        self._messages.append(message)
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]

    def get_recent_messages(self):
        """Return recent messages with the newest message first."""
        return list(reversed(self._messages))
