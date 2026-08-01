from __future__ import annotations

import unittest

from memoria_audiovisual.digital_infrastructure_audit import InfrastructureAudit
from memoria_audiovisual.statetech.adapters import validate_adapter
from memoria_audiovisual.statetech.digital_infrastructure_adapter import (
    DigitalInfrastructureAuditAdapter,
)


class DigitalInfrastructureAuditAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = DigitalInfrastructureAuditAdapter(snapshot_id="snapshot_2026_q3")

    def test_adapter_satisfies_protocol(self) -> None:
        validate_adapter(self.adapter)

    def test_expands_aggregated_signals_into_records(self) -> None:
        source = InfrastructureAudit(
            corpus_code="example",
            institution="Example Archive",
            source_url="https://example.org/catalogue",
            final_url="https://example.org/catalogue",
            checked_at_utc="2026-08-01T12:00:00+00:00",
            http_status=200,
            reachable=True,
            cms="Drupal",
            api_open_detected=True,
            api_types="IIIF | OAI-PMH",
            api_evidence="iiif manifest | verb=listrecords",
            metadata_formats="Dublin Core",
            interoperability_protocols="IIIF",
            search_mechanisms="Busca facetada",
            access_restrictions="",
            ai_cataloguing_status="Não identificado na superfície observada",
            ai_cataloguing_evidence="",
            evidence_urls="https://example.org/iiif/manifest",
            error="",
        )

        records = self.adapter.adapt(source)
        groups = [record.payload["detector_group"] for record in records]

        self.assertIn("technology", groups)
        self.assertEqual(groups.count("api_service"), 2)
        self.assertIn("metadata_format", groups)
        self.assertIn("interoperability", groups)
        self.assertIn("search", groups)
        self.assertTrue(all(record.evidences for record in records))
        self.assertTrue(all(record.provenance.evidence_ids for record in records))
        self.assertTrue(all(record.payload["review_status"] == "pending_review" for record in records))

    def test_unreachable_source_is_not_assessable(self) -> None:
        source = {
            "corpus_code": "offline",
            "institution": "Offline Archive",
            "source_url": "https://offline.example.org",
            "final_url": "",
            "checked_at_utc": "2026-08-01T12:00:00+00:00",
            "http_status": 503,
            "reachable": False,
            "cms": "",
            "api_types": "",
            "metadata_formats": "",
            "interoperability_protocols": "",
            "search_mechanisms": "",
            "access_restrictions": "",
            "ai_cataloguing_evidence": "",
            "error": "service unavailable",
        }

        records = self.adapter.adapt(source)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].payload["detection_status"], "unknown")
        self.assertEqual(records[0].payload["review_status"], "not_assessable")
        self.assertEqual(records[0].payload["collection_status"], "error")

    def test_missing_identity_fields_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.adapter.adapt({"corpus_code": "x"})


if __name__ == "__main__":
    unittest.main()
