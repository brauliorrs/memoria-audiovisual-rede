from __future__ import annotations

import unittest

from memoria_audiovisual.digital_infrastructure.eligibility import (
    IncorporationCandidate,
    evaluate_scientific_incorporation,
)


class IncorporationEligibilityTests(unittest.TestCase):
    def candidate(self, **overrides):
        payload = {
            "candidate_id": "candidate-europe-001",
            "label": "Arquivo Audiovisual de Teste",
            "source_url": "https://example.org/archive",
            "audiovisual_relevance": True,
            "institutional_identity_confirmed": True,
            "observable_surface": True,
            "evidence_ids": ("evidence-1", "evidence-2"),
            "territory_code": "EU-FR",
            "institutional_role": "institution",
            "archive_type": "audiovisual_archive",
            "duplicate_entity_ids": (),
            "curator_decision": "not_required",
        }
        payload.update(overrides)
        return IncorporationCandidate(**payload)

    def test_clear_candidate_is_automatically_approved(self) -> None:
        result = evaluate_scientific_incorporation(self.candidate())
        self.assertEqual(result.status, "approved")
        self.assertTrue(result.automatic)
        self.assertFalse(result.failed_codes)
        self.assertFalse(result.unknown_codes)

    def test_explicit_curatorial_approval_is_not_automatic(self) -> None:
        result = evaluate_scientific_incorporation(
            self.candidate(curator_decision="approved")
        )
        self.assertEqual(result.status, "approved")
        self.assertFalse(result.automatic)

    def test_possible_duplicate_requires_human_review(self) -> None:
        result = evaluate_scientific_incorporation(
            self.candidate(duplicate_entity_ids=("entity-existing",))
        )
        self.assertEqual(result.status, "requires_human_review")
        self.assertIn("non_duplicate_unit", result.unknown_codes)

    def test_missing_evidence_requires_human_review(self) -> None:
        result = evaluate_scientific_incorporation(
            self.candidate(evidence_ids=("evidence-1",))
        )
        self.assertEqual(result.status, "requires_human_review")
        self.assertIn("sufficient_evidence", result.unknown_codes)

    def test_absent_audiovisual_relevance_rejects_candidate(self) -> None:
        result = evaluate_scientific_incorporation(
            self.candidate(audiovisual_relevance=False)
        )
        self.assertEqual(result.status, "rejected")
        self.assertIn("audiovisual_relevance", result.failed_codes)

    def test_rejected_curatorial_decision_blocks_incorporation(self) -> None:
        result = evaluate_scientific_incorporation(
            self.candidate(curator_decision="rejected")
        )
        self.assertEqual(result.status, "rejected")
        self.assertIn("curatorial_decision", result.failed_codes)

    def test_pending_decision_requires_review(self) -> None:
        result = evaluate_scientific_incorporation(
            self.candidate(curator_decision="pending")
        )
        self.assertEqual(result.status, "requires_human_review")
        self.assertIn("curatorial_decision", result.unknown_codes)

    def test_result_is_serializable_and_explains_criteria(self) -> None:
        payload = evaluate_scientific_incorporation(self.candidate()).to_dict()
        self.assertEqual(payload["candidate_id"], "candidate-europe-001")
        self.assertEqual(payload["status"], "approved")
        self.assertEqual(len(payload["criteria"]), 9)


if __name__ == "__main__":
    unittest.main()
