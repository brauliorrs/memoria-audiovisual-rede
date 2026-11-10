"""Offline regressions: failed monthly refreshes must retain audit evidence."""
from __future__ import annotations

import unittest
from pathlib import Path

from memoria_audiovisual.organism import (
    build_cycle_results_entries,
    build_monthly_cycle_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


class MonthlyFailureEvidenceTests(unittest.TestCase):
    def test_partial_failed_cycle_keeps_each_failure_and_stage(self):
        results = [
            {"code": "ape", "status": "failed",
             "failure_stage": "collection", "error": "exit status 1"},
            {"code": "eye", "status": "failed",
             "failure_stage": "validation", "error": "exit status 1"},
            {"code": "ina", "status": "success",
             "failure_stage": "", "error": ""},
        ]
        manifest = build_monthly_cycle_manifest(
            started_at="2026-11-01T10:00:00Z",
            finished_at="2026-11-01T10:10:00Z",
            cycle_results=results,
            selected_corpora=["ape", "eye", "ina"],
        )
        self.assertEqual(manifest["failed_corpora_total"], 2)
        self.assertEqual(manifest["successful_corpora_total"], 1)
        frame = build_cycle_results_entries(manifest)
        self.assertEqual(frame["failure_stage"].tolist(), [
            "collection", "validation", "",
        ])
        self.assertEqual(frame["status"].tolist(), [
            "failed", "failed", "success",
        ])

    def test_monthly_workflow_uploads_diagnostics_on_failure_without_masking(self):
        source = (ROOT / ".github/workflows/organism-monthly.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("id: monthly_run", source)
        self.assertIn("always() && steps.monthly_run.outcome != 'skipped'", source)
        self.assertIn("if-no-files-found: error", source)
        self.assertIn("data/output/observatorio_ciclo_mensal.json", source)
        self.assertIn("data/output/observatorio_resultados_ciclos.csv", source)
        self.assertIn("if: ${{ success() }}", source)
        self.assertNotIn("continue-on-error: true", source)


if __name__ == "__main__":
    unittest.main()
