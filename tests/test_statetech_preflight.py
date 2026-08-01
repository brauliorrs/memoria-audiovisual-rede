from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.statetech.preflight import PeriodicReviewPreflight


class PeriodicReviewPreflightTests(unittest.TestCase):
    def _repository(self, root: Path) -> None:
        (root / "schemas/statetech").mkdir(parents=True)
        (root / "schemas").mkdir(exist_ok=True)
        (root / "scripts").mkdir()
        (root / "scripts/audit_digital_infrastructure.py").write_text("# ok\n", encoding="utf-8")
        (root / "schemas/digital_infrastructure_audit.schema.json").write_text("{}", encoding="utf-8")
        schema = root / "schemas/statetech/example.schema.json"
        schema.write_text("{}", encoding="utf-8")
        registry = {"schema_version": "1", "schemas": [{"entity": "example", "path": "schemas/statetech/example.schema.json"}]}
        (root / "schemas/statetech/schema_registry.json").write_text(json.dumps(registry), encoding="utf-8")

    def test_clean_first_run_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            report = PeriodicReviewPreflight(root, root / "data/statetech").validate(
                snapshot_id="snapshot_2026_08",
                corpora={"ina": {"organism_active": True, "source_url": "https://example.org"}},
                selected_corpora=(),
                history_exists=False,
            )
            self.assertTrue(report.ok)

    def test_unknown_corpus_and_existing_snapshot_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            state = root / "data/statetech"
            (state / "coverage/snapshot_2026_08").mkdir(parents=True)
            report = PeriodicReviewPreflight(root, state).validate(
                snapshot_id="snapshot_2026_08",
                corpora={"ina": {"organism_active": True, "source_url": "https://example.org"}},
                selected_corpora=("missing",),
                history_exists=True,
            )
            codes = {issue.code for issue in report.issues}
            self.assertFalse(report.ok)
            self.assertIn("PRE-002", codes)
            self.assertIn("PRE-004", codes)

    def test_corrupt_jsonl_and_inconsistent_index_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._repository(root)
            state = root / "data/statetech"
            (state / "coverage").mkdir(parents=True)
            (state / "ledger.jsonl").write_text('{"ok": true}\n{broken\n', encoding="utf-8")
            (state / "coverage/snapshot_coverage_index.jsonl").write_text(
                json.dumps({"snapshot_id": "old_snapshot"}) + "\n", encoding="utf-8"
            )
            report = PeriodicReviewPreflight(root, state).validate(
                snapshot_id="snapshot_new",
                corpora={"ina": {"organism_active": True, "source_url": "https://example.org"}},
                history_exists=True,
            )
            codes = {issue.code for issue in report.issues}
            self.assertIn("PRE-007", codes)
            self.assertIn("PRE-018", codes)


if __name__ == "__main__":
    unittest.main()
