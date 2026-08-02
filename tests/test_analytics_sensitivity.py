from __future__ import annotations

import unittest

from memoria_audiovisual.analytics.base import IndicatorContext
from memoria_audiovisual.analytics.sensitivity import (
    DEFAULT_WEIGHT_SCENARIOS,
    analyze_interoperability_sensitivity,
)


class InteroperabilitySensitivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = IndicatorContext(
            snapshot_id="snapshot_1",
            coverage_rows=(
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "interoperability", "status": "detected", "detected_values": ["IIIF", "OAI-PMH"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "metadata_format", "status": "detected", "detected_values": ["Dublin Core"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "b", "detector_group": "interoperability", "status": "detected", "detected_values": ["IIIF"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "b", "detector_group": "metadata_format", "status": "detected", "detected_values": ["Schema.org", "JSON-LD"]},
            ),
        )

    def test_official_scenario_matches_equal_weights(self) -> None:
        report = analyze_interoperability_sensitivity(self.context)
        official = next(
            item for item in report.scenarios
            if item.scenario_id == "official_equal_weights"
        )
        self.assertEqual(official.corpus_scores["a"], 60.0)
        self.assertEqual(official.corpus_scores["b"], 60.0)
        self.assertEqual(official.aggregate_score, 60.0)

    def test_alternative_weights_change_scores_without_changing_official(self) -> None:
        report = analyze_interoperability_sensitivity(self.context)
        protocol = next(
            item for item in report.scenarios if item.scenario_id == "protocol_priority"
        )
        semantic = next(
            item for item in report.scenarios if item.scenario_id == "semantic_web_priority"
        )
        self.assertEqual(protocol.corpus_scores["a"], 75.0)
        self.assertEqual(protocol.corpus_scores["b"], 50.0)
        self.assertEqual(semantic.corpus_scores["a"], 40.0)
        self.assertEqual(semantic.corpus_scores["b"], 70.0)
        official = next(item for item in report.scenarios if item.scenario_id == report.official_scenario)
        self.assertEqual(official.aggregate_score, 60.0)

    def test_report_exposes_range_variation_and_rank_changes(self) -> None:
        report = analyze_interoperability_sensitivity(self.context)
        self.assertGreater(report.aggregate_range or 0, 0)
        self.assertGreater(report.maximum_corpus_variation["a"], 0)
        self.assertIn("protocol_priority", report.rank_changes)
        self.assertIn("sensível", report.interpretation)

    def test_rejects_invalid_weights(self) -> None:
        scenarios = {
            "official_equal_weights": {
                "iiif": 0.50,
                "oai_pmh": 0.20,
                "dublin_core": 0.20,
                "schema_org": 0.20,
                "json_ld": 0.20,
            }
        }
        with self.assertRaisesRegex(ValueError, "somar 1,0"):
            analyze_interoperability_sensitivity(self.context, scenarios=scenarios)

    def test_default_scenarios_preserve_five_components(self) -> None:
        expected = {"iiif", "oai_pmh", "dublin_core", "schema_org", "json_ld"}
        for weights in DEFAULT_WEIGHT_SCENARIOS.values():
            self.assertEqual(set(weights), expected)


if __name__ == "__main__":
    unittest.main()
