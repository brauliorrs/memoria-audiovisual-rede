from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.historical_migration import HistoricalMigrationAnalyzer


class HistoricalMigrationTests(unittest.TestCase):
    def test_compatible_json_is_reported_without_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.json"
            source.write_text(json.dumps([{
                "corpus_code": "ina",
                "institution": "INA",
                "source_url": "https://example.org",
                "reachable": True,
                "cms": ["Drupal"],
            }]), encoding="utf-8")
            report = HistoricalMigrationAnalyzer().analyze(source)
            self.assertTrue(report.dry_run)
            self.assertEqual(report.compatible_rows, 1)
            self.assertEqual(report.blocked_rows, 0)

    def test_missing_required_fields_blocks_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.json"
            source.write_text(json.dumps([{"corpus_code": "ina", "cms": ["Drupal"]}]), encoding="utf-8")
            report = HistoricalMigrationAnalyzer().analyze(source)
            self.assertEqual(report.blocked_rows, 1)
            self.assertTrue(any(issue.code == "MIG-001" for issue in report.issues))

    def test_duplicate_natural_keys_block_all_occurrences(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.json"
            row = {
                "corpus_code": "ina", "institution": "INA",
                "source_url": "https://example.org", "reachable": True,
                "api_types": ["IIIF"],
            }
            source.write_text(json.dumps([row, row]), encoding="utf-8")
            report = HistoricalMigrationAnalyzer().analyze(source)
            self.assertEqual(report.blocked_rows, 2)
            self.assertEqual(len(report.duplicate_keys), 1)

    def test_unknown_fields_are_reported_not_discarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "legacy.json"
            source.write_text(json.dumps([{
                "corpus_code": "ina", "institution": "INA",
                "source_url": "https://example.org", "reachable": True,
                "cms": ["Drupal"], "legacy_note": "preservar",
            }]), encoding="utf-8")
            report = HistoricalMigrationAnalyzer().analyze(source)
            self.assertIn("legacy_note", report.unknown_fields)
            self.assertTrue(any(issue.code == "MIG-004" for issue in report.issues))


if __name__ == "__main__":
    unittest.main()
