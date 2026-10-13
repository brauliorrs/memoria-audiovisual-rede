"""Offline candidate-clock tests: not authorization for live harvesting."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from scripts.finna_expiry_hypotheses import assess_naive_finna_expiry


class FinnaExpiryHypothesesTests(unittest.TestCase):
    def test_both_clocks_before_and_after(self):
        now = datetime(2026, 10, 13, 13, 0, tzinfo=timezone.utc)
        both_future = assess_naive_finna_expiry("2026-10-13T20:00:00", now=now)
        both_past = assess_naive_finna_expiry("2026-10-13T10:00:00", now=now)
        self.assertEqual(both_future.classification, "both_future")
        self.assertEqual(both_past.classification, "both_past")
        self.assertEqual(both_future.utc_offset_hours, 3.0)

    def test_disagreement_is_not_two_network_attempts(self):
        now = datetime(2026, 10, 13, 13, 0, tzinfo=timezone.utc)
        finding = assess_naive_finna_expiry(
            "2026-10-13T15:00:00", now=now
        )
        self.assertEqual(finding.classification, "disagreement")
        self.assertEqual(finding.utc_candidate.hour, 15)
        self.assertEqual(finding.helsinki_candidate.hour, 12)

    def test_winter_helsinki_offset(self):
        now = datetime(2026, 1, 13, 13, 0, tzinfo=timezone.utc)
        x = assess_naive_finna_expiry("2026-01-13T20:00:00", now=now)
        self.assertEqual(x.utc_offset_hours, 2.0)

    def test_autumn_fold_does_not_pick_an_arbitrary_time(self):
        now = datetime(2026, 10, 25, 0, 0, tzinfo=timezone.utc)
        x = assess_naive_finna_expiry("2026-10-25T03:30:00", now=now)
        self.assertEqual(x.classification, "helsinki_dst_fold_ambiguous")
        self.assertIsNone(x.helsinki_candidate)

    def test_spring_gap_is_unrepresentable(self):
        now = datetime(2026, 3, 29, 0, 0, tzinfo=timezone.utc)
        x = assess_naive_finna_expiry("2026-03-29T03:30:00", now=now)
        self.assertEqual(x.classification, "helsinki_nonexistent_time")

    def test_reject_aware_input_and_naive_clock(self):
        now = datetime(2026, 1, 13, 12, 0, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, "requires_naive_expiry"):
            assess_naive_finna_expiry("2026-01-13T20:00:00Z", now=now)
        with self.assertRaisesRegex(ValueError, "aware_now_required"):
            assess_naive_finna_expiry("2026-01-13T20:00:00", now=now.replace(tzinfo=None))

    def test_margin_can_change_candidate_classification(self):
        now = datetime(2026, 1, 13, 12, 0, tzinfo=timezone.utc)
        x = assess_naive_finna_expiry("2026-01-13T12:00:20", now=now, safety_margin_seconds=30)
        self.assertEqual(x.classification, "both_past")


if __name__ == "__main__":
    unittest.main()
