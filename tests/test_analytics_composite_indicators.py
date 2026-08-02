from __future__ import annotations

import unittest

from memoria_audiovisual.analytics.base import IndicatorContext
from memoria_audiovisual.analytics.indicators import InteroperabilityIndexIndicator


class CompositeIndicatorTests(unittest.TestCase):
    def test_equal_weights_and_corpus_scores(self) -> None:
        context = IndicatorContext(
            snapshot_id="snapshot_1",
            coverage_rows=(
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "interoperability", "status": "detected", "detected_values": ["IIIF", "OAI-PMH"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "metadata_format", "status": "detected", "detected_values": ["Dublin Core", "Schema.org", "JSON-LD"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "b", "detector_group": "interoperability", "status": "detected", "detected_values": ["IIIF"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "b", "detector_group": "metadata_format", "status": "detected", "detected_values": ["Dublin Core"]},
            ),
        )
        result = InteroperabilityIndexIndicator().calculate(context)
        self.assertEqual(result.value, 70.0)
        self.assertEqual(result.denominator, 2)
        self.assertEqual(result.dimensions["corpus_scores"], {"a": 100.0, "b": 40.0})
        self.assertEqual(sum(result.dimensions["weights"].values()), 1.0)

    def test_missing_group_is_renormalized_when_three_components_remain(self) -> None:
        context = IndicatorContext(
            snapshot_id="snapshot_1",
            coverage_rows=(
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "metadata_format", "status": "detected", "detected_values": ["Dublin Core", "Schema.org"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "interoperability", "status": "not_assessable", "detected_values": []},
            ),
        )
        result = InteroperabilityIndexIndicator().calculate(context)
        self.assertEqual(result.value, round((2 / 3) * 100, 4))
        self.assertEqual(result.dimensions["eligible_corpora"], ["a"])

    def test_corpus_with_less_than_three_components_is_excluded(self) -> None:
        context = IndicatorContext(
            snapshot_id="snapshot_1",
            coverage_rows=(
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "interoperability", "status": "detected", "detected_values": ["IIIF"]},
            ),
        )
        result = InteroperabilityIndexIndicator().calculate(context)
        self.assertIsNone(result.value)
        self.assertEqual(result.status, "insufficient_data")
        self.assertIn("a", result.dimensions["excluded_corpora"])


if __name__ == "__main__":
    unittest.main()
