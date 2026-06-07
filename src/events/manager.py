"""Event timing, queueing, and execution orchestration."""

from ..game.mode_config import DEFAULT_ADVANCED_EVENT_POOL
from .registry import choose_random_event_key, create_event


DEFAULT_EVENT_POOL = list(DEFAULT_ADVANCED_EVENT_POOL)


class EventManager:
    """Coordinate event timing while concrete events own their behavior."""

    def __init__(self, game_state, event_pool=None):
        self.gs = game_state
        self.turn_counter = 0
        self.active_events = []
        self.queued_event = None
        self.queued_event_key = None
        self.event_pool = list(DEFAULT_EVENT_POOL) if event_pool is None else list(event_pool)
        if self.event_pool:
            self._queue_next_event()

    def _queue_next_event(self):
        """Choose and instantiate the next event in the pool."""
        if not self.event_pool:
            self.queued_event = None
            self.queued_event_key = None
            return
        self.queued_event_key = choose_random_event_key(self.event_pool)
        self.queued_event = create_event(self.queued_event_key, self.gs)

    def _tick_active_events(self):
        """Advance any active event state before warning/execution checks."""
        for event in list(self.active_events):
            event.tick()
            if event.duration == 0 and not event.warning_active and event is not self.queued_event:
                event.cleanup()
                self.active_events.remove(event)

    def update(self):
        """Advance warning and execution flow based on full-turn count."""
        self.turn_counter = self.gs.get_full_turn_count()

        if self.turn_counter > 0:
            self._tick_active_events()

        if self.turn_counter > 0 and self.turn_counter % 10 == 9:
            if self.queued_event and self.queued_event not in self.active_events:
                self.queued_event.trigger_warning()
                self.active_events.append(self.queued_event)

        if self.turn_counter > 0 and self.turn_counter % 10 == 0:
            if self.queued_event and self.queued_event in self.active_events:
                self.queued_event.execute()
                if self.queued_event.duration == 0:
                    self.queued_event.cleanup()
                    self.active_events.remove(self.queued_event)
                self.queued_event = None
                self.queued_event_key = None
                self._queue_next_event()
