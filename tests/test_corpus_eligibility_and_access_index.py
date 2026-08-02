from __future__ import annotations

import unittest

from memoria_audiovisual.analytics.base import IndicatorContext
from memoria_audiovisual.analytics.indicators import AudiovisualArchiveAccessIndex
from memoria_audiovisual.digital_infrastructure.corpus_eligibility import (
    EXCLUDED,
    ELIGIBLE,
    classify_corpus_eligibility,
    eligible_corpus_codes,
)


class CorpusEligibilityAndAccessIndexTests(unittest.TestCase):
    def test_paid_image_bank_is_catalogued_but_excluded(self) -> None:
        decision = classify_corpus_eligibility({
            "entity_id": "stock_bank",
            "entity_category": "image_bank",
            "is_paid": True,
        })
        self.assertEqual(decision.corpus_status, EXCLUDED)
        self.assertEqual(decision.exclusion_reason, "commercial_image_bank")

    def test_eligible_archive_enters_research_corpus(self) -> None:
        entities = (
            {"entity_id": "archive_a", "entity_category": "audiovisual_archive"},
            {"entity_id": "stock_bank", "entity_category": "commercial_image_bank"},
        )
        self.assertEqual(eligible_corpus_codes(entities), ("archive_a",))
        self.assertEqual(classify_corpus_eligibility(entities[0]).corpus_status, ELIGIBLE)

    def test_access_index_uses_only_eligible_archives(self) -> None:
        context = IndicatorContext(
            snapshot_id="snapshot_1",
            metadata={"eligible_corpus_codes": ["open_archive", "formal_request_archive"]},
            coverage_rows=(
                {"snapshot_id": "snapshot_1", "corpus_code": "open_archive", "detector_group": "restriction", "status": "not_detected", "detected_values": []},
                {"snapshot_id": "snapshot_1", "corpus_code": "formal_request_archive", "detector_group": "restriction", "status": "detected", "detected_values": ["Solicitação formal por e-mail"]},
                {"snapshot_id": "snapshot_1", "corpus_code": "paid_bank", "detector_group": "restriction", "status": "detected", "detected_values": ["Pagamento"]},
            ),
        )
        result = AudiovisualArchiveAccessIndex().calculate(context)
        self.assertEqual((result.numerator, result.denominator, result.value), (1, 2, 50.0))
        self.assertEqual(result.dimensions["excluded_non_corpus"], ["paid_bank"])


if __name__ == "__main__":
    unittest.main()
