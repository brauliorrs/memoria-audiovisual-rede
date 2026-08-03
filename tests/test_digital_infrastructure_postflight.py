from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.parameter_coverage import EXPECTED_DETECTOR_GROUPS
from memoria_audiovisual.digital_infrastructure.postflight import validate_periodic_run


class PostflightTests(unittest.TestCase):
    def _prepare(self, root: Path, *, missing_group: bool = False, wrong_count: bool = False) -> None:
        snapshot = "snapshot_test"
        state = root / "data" / "digital_infrastructure"
        snapshot_dir = state / "coverage" / snapshot
        snapshot_dir.mkdir(parents=True)
        groups = list(EXPECTED_DETECTOR_GROUPS)
        if missing_group:
            groups.pop()
        coverage = [
            {
                "corpus_code": "sample",
                "snapshot_id": snapshot,
                "detector_group": group,
                "status": "not_detected",
                "observation_count": 1,
                "detected_values": [],
            }
            for group in groups
        ]
        record_count = len(coverage) + (1 if wrong_count else 0)
        summary = {
            "mode": "ledger",
            "snapshot_id": snapshot,
            "source_count": 1,
            "record_count": record_count,
            "committed_count": record_count,
            "resumed_count": 0,
            "batches": [{"batch_id": "batch_1", "items": []}],
        }
        (snapshot_dir / "parameter_coverage.json").write_text(json.dumps(coverage), encoding="utf-8")
        (snapshot_dir / "execution_summary.json").write_text(json.dumps(summary), encoding="utf-8")
        index = {
            "snapshot_id": snapshot,
            "coverage_path": str(snapshot_dir / "parameter_coverage.json"),
            "changes_path": None,
            "previous_snapshot_id": None,
            "corpus_count": 1,
            "parameter_count": len(coverage),
            "created_at": "2026-08-01T12:00:00+00:00",
        }
        (state / "coverage" / "snapshot_coverage_index.jsonl").write_text(json.dumps(index) + "\n", encoding="utf-8")
        (state / "ingestion_batches.jsonl").write_text(json.dumps({"batch_id": "batch_1"}) + "\n", encoding="utf-8")
        (state / "ledger.jsonl").write_text(json.dumps({"transaction_id": "tx_1"}) + "\n", encoding="utf-8")

    def test_valid_run_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._prepare(root)
            report = validate_periodic_run(snapshot_id="snapshot_test", state_dir=root / "data" / "digital_infrastructure")
            self.assertTrue(report.ok)
            self.assertEqual(report.coverage_row_count, 7)

    def test_missing_group_blocks_consolidation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._prepare(root, missing_group=True)
            report = validate_periodic_run(snapshot_id="snapshot_test", state_dir=root / "data" / "digital_infrastructure")
            self.assertFalse(report.ok)
            self.assertTrue(any(issue.code == "POST-009" for issue in report.issues))

    def test_count_mismatch_blocks_consolidation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._prepare(root, wrong_count=True)
            report = validate_periodic_run(snapshot_id="snapshot_test", state_dir=root / "data" / "digital_infrastructure")
            self.assertFalse(report.ok)
            self.assertTrue(any(issue.code == "POST-010" for issue in report.issues))


if __name__ == "__main__":
    unittest.main()
