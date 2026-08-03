from __future__ import annotations

import unittest

from memoria_audiovisual.digital_infrastructure.event_triage import triage_event, triage_events


class EventTriageTests(unittest.TestCase):
    def event(self, group: str, change: str) -> dict:
        return {
            "current_snapshot_id": "snapshot_2026_09",
            "corpus_code": "ina",
            "detector_group": group,
            "change_type": change,
            "previous_values": ["old"],
            "current_values": ["new"],
        }

    def test_unchanged_event_is_publishable(self) -> None:
        result = triage_event(self.event("technology", "unchanged"))
        self.assertEqual(result.triage_class, "routine")
        self.assertFalse(result.review_required)
        self.assertEqual(result.publication_status, "publishable")

    def test_disappearance_requires_review(self) -> None:
        result = triage_event(self.event("api_service", "disappeared"))
        self.assertEqual(result.triage_class, "disappearance_alert")
        self.assertEqual(result.severity, "high")
        self.assertTrue(result.review_required)

    def test_sensitive_change_requires_review(self) -> None:
        result = triage_event(self.event("ai_evidence", "appeared"))
        self.assertEqual(result.triage_class, "sensitive")
        self.assertEqual(result.publication_status, "pending_review")

    def test_error_is_blocked(self) -> None:
        result = triage_event(self.event("search", "error"))
        self.assertEqual(result.triage_class, "data_quality")
        self.assertEqual(result.publication_status, "blocked")

    def test_identical_events_are_rejected(self) -> None:
        item = self.event("technology", "changed")
        with self.assertRaises(ValueError):
            triage_events([item, item])


if __name__ == "__main__":
    unittest.main()
