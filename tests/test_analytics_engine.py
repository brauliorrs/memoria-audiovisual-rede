from __future__ import annotations

import unittest

from memoria_audiovisual.analytics import AnalyticsEngine, IndicatorContext, IndicatorRegistry
from memoria_audiovisual.analytics.indicators import (
    ApiCoverageIndicator,
    InteroperabilityCoverageIndicator,
)


class AnalyticsEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = (
            {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "api_service", "status": "detected"},
            {"snapshot_id": "snapshot_1", "corpus_code": "b", "detector_group": "api_service", "status": "not_detected"},
            {"snapshot_id": "snapshot_1", "corpus_code": "c", "detector_group": "api_service", "status": "not_assessable"},
            {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "interoperability", "status": "detected"},
            {"snapshot_id": "snapshot_1", "corpus_code": "b", "detector_group": "interoperability", "status": "detected"},
            {"snapshot_id": "snapshot_1", "corpus_code": "c", "detector_group": "interoperability", "status": "error"},
        )
        self.context = IndicatorContext(snapshot_id="snapshot_1", coverage_rows=self.rows)

    def test_registry_blocks_duplicate_version(self) -> None:
        registry = IndicatorRegistry((ApiCoverageIndicator(),))
        with self.assertRaisesRegex(ValueError, "já registrado"):
            registry.register(ApiCoverageIndicator())

    def test_engine_runs_in_deterministic_order(self) -> None:
        registry = IndicatorRegistry((InteroperabilityCoverageIndicator(), ApiCoverageIndicator()))
        run = AnalyticsEngine(registry).run(self.context)
        self.assertEqual(
            [result.indicator_id for result in run.results],
            ["api_coverage", "interoperability_coverage"],
        )
        self.assertEqual(run.status, "completed")

    def test_api_coverage_excludes_not_assessable(self) -> None:
        result = ApiCoverageIndicator().calculate(self.context)
        self.assertEqual(result.numerator, 1)
        self.assertEqual(result.denominator, 2)
        self.assertEqual(result.value, 50.0)
        self.assertEqual(result.dimensions["excluded_corpora"], ["c"])

    def test_interoperability_coverage_excludes_errors(self) -> None:
        result = InteroperabilityCoverageIndicator().calculate(self.context)
        self.assertEqual(result.numerator, 2)
        self.assertEqual(result.denominator, 2)
        self.assertEqual(result.value, 100.0)

    def test_context_rejects_mixed_snapshots(self) -> None:
        rows = self.rows + ({
            "snapshot_id": "snapshot_2",
            "corpus_code": "d",
            "detector_group": "api_service",
            "status": "detected",
        },)
        with self.assertRaisesRegex(ValueError, "outro snapshot"):
            IndicatorContext(snapshot_id="snapshot_1", coverage_rows=rows)

    def test_duplicate_coverage_row_is_blocked(self) -> None:
        context = IndicatorContext(
            snapshot_id="snapshot_1",
            coverage_rows=self.rows + (self.rows[0],),
        )
        with self.assertRaisesRegex(ValueError, "duplicada"):
            ApiCoverageIndicator().calculate(context)


if __name__ == "__main__":
    unittest.main()
