from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.analytics.pipeline import analyze_snapshot, load_coverage_rows


class AnalyticsPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.snapshot_id = "snapshot_2026_09"
        self.coverage_path = self.root / "parameter_coverage.json"
        self.coverage_path.write_text(
            json.dumps([
                {"corpus_code": "ina", "snapshot_id": self.snapshot_id, "detector_group": "api_service", "status": "detected", "observation_count": 1, "detected_values": ["IIIF API"]},
                {"corpus_code": "archive_b", "snapshot_id": self.snapshot_id, "detector_group": "api_service", "status": "not_detected", "observation_count": 1, "detected_values": []},
                {"corpus_code": "ina", "snapshot_id": self.snapshot_id, "detector_group": "interoperability", "status": "detected", "observation_count": 1, "detected_values": ["IIIF", "OAI-PMH"]},
                {"corpus_code": "archive_b", "snapshot_id": self.snapshot_id, "detector_group": "interoperability", "status": "not_assessable", "observation_count": 1, "detected_values": []},
                {"corpus_code": "ina", "snapshot_id": self.snapshot_id, "detector_group": "metadata_format", "status": "detected", "observation_count": 1, "detected_values": ["Dublin Core", "Schema.org", "JSON-LD"]},
                {"corpus_code": "archive_b", "snapshot_id": self.snapshot_id, "detector_group": "metadata_format", "status": "not_detected", "observation_count": 1, "detected_values": []},
            ]),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_executes_native_indicators_and_persists(self) -> None:
        output = self.root / "analytics"
        result = analyze_snapshot(snapshot_id=self.snapshot_id, coverage_path=self.coverage_path, output_root=output)
        self.assertEqual(result.run.status, "completed")
        self.assertEqual(result.run.indicator_count, 9)
        values = {item.indicator_id: item.value for item in result.run.results}
        self.assertEqual(values["api_coverage"], 50.0)
        self.assertEqual(values["interoperability_coverage"], 100.0)
        self.assertEqual(values["iiif_coverage"], 100.0)
        self.assertEqual(values["oai_pmh_coverage"], 100.0)
        self.assertEqual(values["dublin_core_coverage"], 50.0)
        self.assertEqual(values["schema_org_coverage"], 50.0)
        self.assertEqual(values["json_ld_coverage"], 50.0)
        self.assertEqual(values["interoperability_index"], 50.0)
        self.assertIn("audiovisual_archive_access_index", values)
        self.assertIsNotNone(result.manifest)
        self.assertTrue((output / self.snapshot_id / "snapshot_indicators.json").exists())
        self.assertTrue((output / "indicator_history.jsonl").exists())

    def test_rejects_coverage_from_another_snapshot(self) -> None:
        payload = json.loads(self.coverage_path.read_text(encoding="utf-8"))
        payload[0]["snapshot_id"] = "snapshot_other"
        self.coverage_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outro snapshot"):
            load_coverage_rows(self.coverage_path, snapshot_id=self.snapshot_id)

    def test_rejects_duplicate_corpus_parameter_pair(self) -> None:
        payload = json.loads(self.coverage_path.read_text(encoding="utf-8"))
        payload.append(dict(payload[0]))
        self.coverage_path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cobertura duplicada"):
            load_coverage_rows(self.coverage_path, snapshot_id=self.snapshot_id)

    def test_rejects_empty_coverage(self) -> None:
        self.coverage_path.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "vazia"):
            load_coverage_rows(self.coverage_path, snapshot_id=self.snapshot_id)

    def test_does_not_overwrite_same_snapshot(self) -> None:
        output = self.root / "analytics"
        analyze_snapshot(snapshot_id=self.snapshot_id, coverage_path=self.coverage_path, output_root=output)
        with self.assertRaises(FileExistsError):
            analyze_snapshot(snapshot_id=self.snapshot_id, coverage_path=self.coverage_path, output_root=output)


if __name__ == "__main__":
    unittest.main()
