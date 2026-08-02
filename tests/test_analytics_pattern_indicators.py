from __future__ import annotations

import unittest

from memoria_audiovisual.analytics.base import IndicatorContext
from memoria_audiovisual.analytics.indicators import (
    DublinCoreCoverageIndicator,
    IiifCoverageIndicator,
    JsonLdCoverageIndicator,
    OaiPmhCoverageIndicator,
    SchemaOrgCoverageIndicator,
)


class PatternIndicatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = IndicatorContext(
            snapshot_id="snapshot_1",
            coverage_rows=(
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "interoperability", "status": "detected", "detected_values": ["IIIF Presentation API", "OAI-PMH"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "b", "detector_group": "interoperability", "status": "not_detected", "detected_values": []},
                {"snapshot_id": "snapshot_1", "corpus_code": "c", "detector_group": "interoperability", "status": "not_assessable", "detected_values": []},
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "metadata_format", "status": "detected", "detected_values": ["Dublin Core", "Schema.org", "JSON-LD"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "b", "detector_group": "metadata_format", "status": "detected", "detected_values": ["DCMI Terms"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "c", "detector_group": "metadata_format", "status": "error", "detected_values": []},
            ),
        )

    def test_interoperability_patterns_use_explicit_values(self) -> None:
        iiif = IiifCoverageIndicator().calculate(self.context)
        oai = OaiPmhCoverageIndicator().calculate(self.context)
        self.assertEqual((iiif.numerator, iiif.denominator, iiif.value), (1, 2, 50.0))
        self.assertEqual((oai.numerator, oai.denominator, oai.value), (1, 2, 50.0))
        self.assertEqual(iiif.dimensions["excluded_corpora"], ["c"])

    def test_metadata_patterns_have_independent_numerators(self) -> None:
        dublin = DublinCoreCoverageIndicator().calculate(self.context)
        schema = SchemaOrgCoverageIndicator().calculate(self.context)
        json_ld = JsonLdCoverageIndicator().calculate(self.context)
        self.assertEqual((dublin.numerator, dublin.denominator, dublin.value), (2, 2, 100.0))
        self.assertEqual((schema.numerator, schema.denominator, schema.value), (1, 2, 50.0))
        self.assertEqual((json_ld.numerator, json_ld.denominator, json_ld.value), (1, 2, 50.0))

    def test_detected_group_without_pattern_is_not_positive(self) -> None:
        context = IndicatorContext(
            snapshot_id="snapshot_1",
            coverage_rows=(
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "metadata_format", "status": "detected", "detected_values": ["MARCXML"]},
            ),
        )
        result = DublinCoreCoverageIndicator().calculate(context)
        self.assertEqual((result.numerator, result.denominator, result.value), (0, 1, 0.0))

    def test_invalid_detected_values_is_rejected(self) -> None:
        context = IndicatorContext(
            snapshot_id="snapshot_1",
            coverage_rows=(
                {"snapshot_id": "snapshot_1", "corpus_code": "a", "detector_group": "interoperability", "status": "detected", "detected_values": "IIIF"},
            ),
        )
        with self.assertRaisesRegex(ValueError, "detected_values"):
            IiifCoverageIndicator().calculate(context)


if __name__ == "__main__":
    unittest.main()
