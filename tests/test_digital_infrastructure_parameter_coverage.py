from __future__ import annotations

import unittest

from memoria_audiovisual.digital_infrastructure.parameter_coverage import (
    EXPECTED_DETECTOR_GROUPS,
    build_coverage_matrix,
    compare_coverage,
)


class ParameterCoverageTests(unittest.TestCase):
    def test_matrix_exposes_missing_groups(self) -> None:
        observations = ({
            "corpus_code": "ina",
            "snapshot_id": "s1",
            "detector_group": "technology",
            "detection_status": "detected",
            "detected_value": "Drupal",
        },)
        matrix = build_coverage_matrix(observations, corpus_code="ina", snapshot_id="s1")
        self.assertEqual(len(matrix), len(EXPECTED_DETECTOR_GROUPS))
        by_group = {item.detector_group: item for item in matrix}
        self.assertEqual(by_group["technology"].status, "detected")
        self.assertEqual(by_group["api_service"].status, "missing_observation")

    def test_explicit_not_detected_is_not_missing(self) -> None:
        observations = ({
            "corpus_code": "ina",
            "snapshot_id": "s1",
            "detector_group": "ai_evidence",
            "detection_status": "not_detected",
            "detected_value": "not_detected",
        },)
        matrix = build_coverage_matrix(observations, corpus_code="ina", snapshot_id="s1")
        ai = next(item for item in matrix if item.detector_group == "ai_evidence")
        self.assertEqual(ai.status, "not_detected")
        self.assertEqual(ai.detected_values, ())

    def test_comparison_detects_appearance_and_disappearance(self) -> None:
        previous = build_coverage_matrix(({
            "corpus_code": "ina", "snapshot_id": "s1",
            "detector_group": "api_service", "detection_status": "not_detected",
            "detected_value": "not_detected",
        }, {
            "corpus_code": "ina", "snapshot_id": "s1",
            "detector_group": "technology", "detection_status": "detected",
            "detected_value": "Drupal",
        }), corpus_code="ina", snapshot_id="s1")
        current = build_coverage_matrix(({
            "corpus_code": "ina", "snapshot_id": "s2",
            "detector_group": "api_service", "detection_status": "detected",
            "detected_value": "IIIF",
        }, {
            "corpus_code": "ina", "snapshot_id": "s2",
            "detector_group": "technology", "detection_status": "not_detected",
            "detected_value": "not_detected",
        }), corpus_code="ina", snapshot_id="s2")
        changes = {item.detector_group: item.change_type for item in compare_coverage(previous, current)}
        self.assertEqual(changes["api_service"], "appeared")
        self.assertEqual(changes["technology"], "disappeared")


if __name__ == "__main__":
    unittest.main()
