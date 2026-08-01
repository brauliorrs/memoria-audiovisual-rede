from __future__ import annotations

import importlib.util
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from typing import Any

from memoria_audiovisual.statetech.ingestion import IngestionItem, IngestionResult

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_digital_infrastructure.py"
SPEC = importlib.util.spec_from_file_location("audit_digital_infrastructure_script", SCRIPT_PATH)
assert SPEC and SPEC.loader
SCRIPT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCRIPT)


class _Coordinator:
    def __init__(self) -> None:
        self.preview_calls: list[dict[str, Any]] = []
        self.commit_calls: list[dict[str, Any]] = []

    @staticmethod
    def _result(mode: str) -> IngestionResult:
        status = "validated" if mode == "preview" else "committed"
        return IngestionResult(
            mode=mode,  # type: ignore[arg-type]
            adapter_name="digital_infrastructure_audit",
            adapter_version="1.0.0",
            source_count=1,
            record_count=1,
            items=(IngestionItem(
                position=1,
                entity_type="digital_infrastructure_audit",
                natural_key="sample",
                payload={
                    "observation_id": "sample",
                    "snapshot_id": "snapshot_test",
                    "corpus_code": "sample",
                    "detector_group": "api_service",
                    "detected_value": "IIIF",
                    "detection_status": "detected",
                },
                evidence_count=1,
                referenced_entity_ids=(),
                status=status,  # type: ignore[arg-type]
                entity_id="entity_1" if mode == "commit" else None,
                version_id="version_1" if mode == "commit" else None,
            ),),
            batch_id="batch_1" if mode == "commit" else None,
            source_artifact_id="artifact_1" if mode == "commit" else None,
        )

    def preview(self, adapter: Any, source: dict[str, Any]) -> IngestionResult:
        self.preview_calls.append(source)
        return self._result("preview")

    def commit(self, adapter: Any, source: dict[str, Any]) -> IngestionResult:
        self.commit_calls.append(source)
        return self._result("commit")


def _args(mode: str, **overrides: Any) -> Namespace:
    values = {
        "mode": mode,
        "snapshot_id": "snapshot_test",
        "result_output": None,
        "write_coverage": False,
        "coverage_dir": Path("data/statetech/coverage"),
    }
    values.update(overrides)
    return Namespace(**values)


class AuditExecutorModeTests(unittest.TestCase):
    def test_legacy_is_default_mode(self) -> None:
        args = SCRIPT.parse_args([])
        self.assertEqual(args.mode, "legacy")
        self.assertIsNone(args.snapshot_id)

    def test_preview_requires_snapshot(self) -> None:
        with self.assertRaises(SystemExit):
            SCRIPT.parse_args(["--mode", "preview"])

    def test_preview_builds_coverage_without_writing(self) -> None:
        coordinator = _Coordinator()
        records = [{
            "corpus_code": "sample",
            "institution": "Sample Archive",
            "source_url": "https://example.org",
            "checked_at_utc": "2026-08-01T12:00:00+00:00",
            "entity_level": "corpus",
        }]
        summary = SCRIPT.run_statetech_mode(records, args=_args("preview"), coordinator=coordinator)
        self.assertEqual(summary["committed_count"], 0)
        self.assertEqual(summary["coverage"]["parameter_count"], 7)
        self.assertEqual(summary["coverage"]["status_counts"]["detected"], 1)
        self.assertEqual(summary["coverage"]["status_counts"]["missing_observation"], 6)
        self.assertNotIn("coverage_manifest", summary)
        self.assertEqual(len(coordinator.preview_calls), 1)
        self.assertEqual(coordinator.commit_calls, [])

    def test_ledger_writes_summary_and_coverage_manifest(self) -> None:
        coordinator = _Coordinator()
        records = [{
            "corpus_code": "sample",
            "institution": "Sample Archive",
            "source_url": "https://example.org",
            "checked_at_utc": "2026-08-01T12:00:00+00:00",
            "entity_level": "corpus",
        }]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "summary.json"
            args = _args("ledger", result_output=output, coverage_dir=root / "coverage")
            summary = SCRIPT.run_statetech_mode(records, args=args, coordinator=coordinator)
            self.assertEqual(summary["committed_count"], 1)
            self.assertTrue(output.exists())
            self.assertTrue(Path(summary["coverage_manifest"]["coverage_path"]).exists())
            self.assertIsNone(summary["coverage_manifest"]["previous_snapshot_id"])
            self.assertEqual(len(coordinator.commit_calls), 1)


if __name__ == "__main__":
    unittest.main()
