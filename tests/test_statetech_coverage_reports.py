from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.statetech.coverage_reports import CoverageReportStore
from memoria_audiovisual.statetech.parameter_coverage import ParameterCoverage


class CoverageReportStoreTests(unittest.TestCase):
    def test_second_snapshot_generates_change_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = CoverageReportStore(Path(directory))
            first = store.write(
                snapshot_id="snapshot_1",
                coverage=(ParameterCoverage(
                    corpus_code="ina", snapshot_id="snapshot_1",
                    detector_group="api_service", status="not_detected",
                    observation_count=1,
                ),),
            )
            second = store.write(
                snapshot_id="snapshot_2",
                coverage=(ParameterCoverage(
                    corpus_code="ina", snapshot_id="snapshot_2",
                    detector_group="api_service", status="detected",
                    observation_count=1, detected_values=("IIIF",),
                ),),
                previous_manifest=first,
            )
            self.assertEqual(second.previous_snapshot_id, "snapshot_1")
            self.assertTrue(Path(second.coverage_path).exists())
            self.assertTrue(Path(second.changes_path or "").exists())
            self.assertEqual(store.latest_manifest().snapshot_id, "snapshot_2")

    def test_existing_snapshot_report_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = CoverageReportStore(Path(directory))
            coverage = (ParameterCoverage(
                corpus_code="ina", snapshot_id="snapshot_1",
                detector_group="technology", status="detected",
                observation_count=1, detected_values=("Drupal",),
            ),)
            store.write(snapshot_id="snapshot_1", coverage=coverage)
            with self.assertRaises(FileExistsError):
                store.write(snapshot_id="snapshot_1", coverage=coverage)


if __name__ == "__main__":
    unittest.main()
