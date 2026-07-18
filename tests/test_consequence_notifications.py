"""Presentation notifications derived from reversible action records."""

import unittest

from src.engine.actions import ClearStatus, SetPendingEvent, SetStatus, TickStatus
from src.runtime import consequence_kinds


class ConsequenceNotificationTests(unittest.TestCase):
    def test_status_actions_are_deduplicated_and_tick_is_ignored(self):
        record = [SetStatus(None, None), SetStatus(None, None), TickStatus(None, "proof:glow"), ClearStatus(None, "proof:glow")]
        self.assertEqual(["status_applied", "status_expired"], consequence_kinds(record))

    def test_pending_event_id_distinguishes_warning_and_execution(self):
        self.assertEqual(["event_warning"], consequence_kinds([SetPendingEvent("base:pool", "base:event")]))
        self.assertEqual(["event_executed"], consequence_kinds([SetPendingEvent("base:pool", None)]))

    def test_a_record_can_report_all_consequence_kinds_in_stable_order(self):
        record = [SetPendingEvent("base:pool", "base:event"), SetStatus(None, None), ClearStatus(None, "proof:glow"), SetPendingEvent("base:pool", None)]
        self.assertEqual(["status_applied", "status_expired", "event_warning", "event_executed"], consequence_kinds(record))


if __name__ == "__main__":
    unittest.main()
