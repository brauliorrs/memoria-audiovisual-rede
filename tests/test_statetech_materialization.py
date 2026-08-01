from __future__ import annotations

import unittest

from memoria_audiovisual.statetech.materialization import CuratorialMaterializer


def _observation(**overrides):
    payload = {
        "observation_id": "obs_1",
        "observed_at": "2026-08-01T12:00:00+00:00",
        "corpus_code": "archive",
        "detector_group": "api_service",
        "detected_value": "IIIF",
        "detection_status": "detected",
        "automatic_confidence": "medium",
        "review_status": "confirmed",
        "review_note": "revisão manual",
    }
    payload.update(overrides)
    return payload


class CuratorialMaterializerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.materializer = CuratorialMaterializer()
        self.institutions = {"archive": "institution_1"}
        self.evidences = {"obs_1": "evidence_1"}

    def test_pending_observation_is_blocked(self) -> None:
        result = self.materializer.materialize(
            (_observation(review_status="pending_review"),),
            institution_ids=self.institutions,
            evidence_ids=self.evidences,
        )
        self.assertEqual(result.records, ())
        self.assertEqual(result.decisions[0].reason, "review_status_not_confirmed")

    def test_confirmed_api_creates_technology_and_relation(self) -> None:
        result = self.materializer.materialize(
            (_observation(),),
            institution_ids=self.institutions,
            evidence_ids=self.evidences,
        )
        self.assertEqual(result.promoted_count, 1)
        self.assertEqual([item.entity_type for item in result.records], [
            "technology", "institution_technology_relation"
        ])
        technology, relation = result.records
        self.assertEqual(technology.payload["validation_status"], "confirmed")
        self.assertEqual(relation.payload["institution_id"], "institution_1")
        self.assertEqual(relation.referenced_entity_ids, (
            "institution_1", technology.payload["technology_id"]
        ))

    def test_missing_evidence_blocks_promotion(self) -> None:
        result = self.materializer.materialize(
            (_observation(),),
            institution_ids=self.institutions,
            evidence_ids={},
        )
        self.assertEqual(result.records, ())
        self.assertEqual(result.decisions[0].reason, "evidence_id_missing")

    def test_confirmed_ai_signal_creates_conservative_ai_system(self) -> None:
        result = self.materializer.materialize(
            (_observation(detector_group="ai_evidence", detected_value="IA na catalogação"),),
            institution_ids=self.institutions,
            evidence_ids=self.evidences,
        )
        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual(record.entity_type, "ai_system")
        self.assertEqual(record.payload["function"], "unknown")
        self.assertEqual(record.payload["deployment_stage"], "unknown")

    def test_restriction_remains_unmaterialized_without_contract(self) -> None:
        result = self.materializer.materialize(
            (_observation(detector_group="restriction", detected_value="Login"),),
            institution_ids=self.institutions,
            evidence_ids=self.evidences,
        )
        self.assertEqual(result.records, ())
        self.assertEqual(result.decisions[0].status, "not_materialized")
        self.assertEqual(result.decisions[0].reason, "no_relational_contract_for_group")


if __name__ == "__main__":
    unittest.main()
