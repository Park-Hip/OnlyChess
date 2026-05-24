"""Event timing, queueing, execution, and undo orchestration."""

from .base import EventStateSnapshot
from .registry import choose_random_event_key, create_event


class EventManager:
    """Coordinate event timing while concrete events own their behavior."""

    def __init__(self, game_state, event_pool=None):
        self.gs = game_state
        self.turn_counter = 0
        self.active_events = []
        self.queued_event = None
        self.queued_event_key = None
        self.snapshots = []
        self.restore_snapshot = None
        self.event_pool = list(event_pool or ["gia_xang_tang"])
        self._queue_next_event()

    def _queue_next_event(self):
        """Choose and instantiate the next event in the pool."""
        self.queued_event_key = choose_random_event_key(self.event_pool)
        self.queued_event = create_event(self.queued_event_key, self.gs)

    def _create_snapshot(self):
        """Capture the event-layer state needed to undo a resolved event."""
        event_snapshot_data = {}
        if self.queued_event is not None:
            event_snapshot_data = self.queued_event.build_snapshot_data()
        return EventStateSnapshot.from_game_state(
            self.gs,
            resolved_event_key=self.queued_event_key,
            queued_event_key=self.queued_event_key,
            active_event_keys=[event.event_key for event in self.active_events],
            event_snapshot_data=event_snapshot_data,
        )

    def update(self):
        """Advance warning and execution flow based on full-turn count."""
        self.turn_counter = len(self.gs.move_log) // 2

        if self.turn_counter > 0 and self.turn_counter % 10 == 9:
            if self.queued_event and self.queued_event not in self.active_events:
                self.queued_event.trigger_warning()
                self.active_events.append(self.queued_event)

        if self.turn_counter > 0 and self.turn_counter % 10 == 0:
            if self.queued_event and self.queued_event in self.active_events:
                self.snapshots.append(self._create_snapshot())
                self.queued_event.execute()
                if self.queued_event.duration == 0:
                    self.queued_event.cleanup()
                    self.active_events.remove(self.queued_event)
                self.queued_event = None
                self.queued_event_key = None
                self._queue_next_event()

    def handle_undo(self):
        """Restore board state before undo when the latest move triggered an event."""
        if not self.snapshots:
            return False

        latest_snapshot = self.snapshots[-1]
        if len(self.gs.move_log) == latest_snapshot.move_log_len:
            self.gs.board.grid = latest_snapshot.grid_copy
            self.restore_snapshot = self.snapshots.pop()
            return True
        return False

    def sync_state(self):
        """Rebuild warning and queue state after an undo changes move history."""
        self.turn_counter = len(self.gs.move_log) // 2
        self.active_events.clear()

        if self.restore_snapshot is not None and self.turn_counter > 0 and self.turn_counter % 10 == 9:
            snapshot = self.restore_snapshot
            self.queued_event_key = snapshot.resolved_event_key
            self.queued_event = create_event(self.queued_event_key, self.gs)
            self.queued_event.restore_from_snapshot_data(snapshot.event_snapshot_data or {})
            self.queued_event.trigger_warning()
            self.active_events.append(self.queued_event)
            self.restore_snapshot = None
            return

        self.restore_snapshot = None

        if self.turn_counter > 0 and self.turn_counter % 10 == 9:
            if self.queued_event_key is None:
                self._queue_next_event()
            else:
                self.queued_event = create_event(self.queued_event_key, self.gs)
            self.queued_event.trigger_warning()
            self.active_events.append(self.queued_event)
        elif self.turn_counter % 10 != 0:
            if self.queued_event_key is None:
                self._queue_next_event()
            else:
                self.queued_event = create_event(self.queued_event_key, self.gs)
