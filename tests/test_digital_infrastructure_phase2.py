from pathlib import Path

import pytest

from memoria_audiovisual.statetech.contracts import SchemaRegistry
from memoria_audiovisual.statetech.digital_infrastructure_adapter import (
    DigitalInfrastructureAuditAdapter,
    curated_rows,
    publishable_rows,
)
from memoria_audiovisual.statetech.digital_infrastructure_review import (
    register_infrastructure_review,
)
from memoria_audiovisual.statetech.ledger import AtomicLedger
from memoria_audiovisual.statetech.service import StatetechDataService


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def sample_source() -> dict:
    return {
        "snapshot_id": "infrastructure-test-001",
        "corpus_code": "demo",
        "institution": "Arquivo de teste",
        "entity_level": "institution",
        "country": "PT",
        "source_url": "https://example.org/archive",
        "final_url": "https://example.org/archive",
        "checked_at_utc": "2026-08-18T18:00:00+00:00",
        "http_status": 200,
        "reachable": True,
        "cms": "Omeka S 4.0",
        "api_types": "IIIF | REST/JSON",
        "api_evidence": "iiif manifest | /api/",
        "metadata_formats": "JSON-LD / Schema.org | Dublin Core",
        "interoperability_protocols": "IIIF | Schema.org",
        "search_mechanisms": "Formulário de busca HTML",
        "access_restrictions": "Autenticação/login",
        "ai_cataloguing_status": "Evidência pública textual detectada",
        "ai_cataloguing_evidence": "Automatic transcription is used to enrich archive metadata.",
        "error": "",
    }


def test_adapter_emits_contract_rows_pending_review_and_unique_evidence():
    adapter = DigitalInfrastructureAuditAdapter()
    records = adapter.adapt(sample_source())
    schemas = SchemaRegistry(REPOSITORY_ROOT)

    assert records
    evidence_ids = []
    observation_ids = set()
    for record in records:
        schemas.validate_structure("digital_infrastructure_audit", record.payload)
        assert record.entity_type == "digital_infrastructure_audit"
        assert record.payload["review_status"] == "pending_review"
        assert record.payload["snapshot_id"] == "infrastructure-test-001"
        observation_ids.add(record.payload["observation_id"])
        evidence_ids.extend(evidence.to_dict()["evidence_id"] for evidence in record.evidences)

    assert len(observation_ids) == 1
    assert len(evidence_ids) == len(set(evidence_ids))
    assert any(record.payload["detector_group"] == "ai_evidence" for record in records)
    assert any(record.payload["detected_value"] == "IIIF" for record in records)


def test_unreachable_surface_is_not_interpreted_as_technology_absence():
    source = sample_source()
    source.update(
        {
            "reachable": False,
            "http_status": 403,
            "final_url": "",
            "cms": "",
            "api_types": "",
            "metadata_formats": "",
            "interoperability_protocols": "",
            "search_mechanisms": "",
            "access_restrictions": "",
            "ai_cataloguing_status": "Não avaliado",
            "ai_cataloguing_evidence": "",
            "error": "403 Client Error",
        }
    )

    records = DigitalInfrastructureAuditAdapter().adapt(source)

    assert {record.payload["collection_status"] for record in records} == {"blocked"}
    assert {record.payload["detection_status"] for record in records} == {"unknown"}
    assert all(record.payload["review_status"] == "pending_review" for record in records)


def test_human_review_creates_new_immutable_version(tmp_path):
    source_record = DigitalInfrastructureAuditAdapter().adapt(sample_source())[0]
    ledger = AtomicLedger(tmp_path / "infrastructure.jsonl")
    service = StatetechDataService(ledger, SchemaRegistry(REPOSITORY_ROOT))

    raw_entity = service.register_entity(
        entity_type=source_record.entity_type,
        natural_key=source_record.natural_key,
        payload=source_record.payload,
        provenance=source_record.provenance,
        evidences=source_record.evidences,
    )
    reviewed = register_infrastructure_review(
        service,
        source_record=source_record,
        previous_version_id=raw_entity.version_id,
        review_status="confirmed",
        reviewer="reviewer:test",
        review_note="Assinatura técnica inequívoca na superfície observada.",
        reviewed_at="2026-08-18T18:30:00+00:00",
    )

    assert raw_entity.validation_status == "pending_review"
    assert reviewed.validation_status == "confirmed"
    assert reviewed.previous_version_id == raw_entity.version_id
    assert reviewed.version_id != raw_entity.version_id
    assert reviewed.payload["review_status"] == "confirmed"
    assert len(ledger.read_all()) == 2


def test_nonconfirmed_review_requires_note(tmp_path):
    source_record = DigitalInfrastructureAuditAdapter().adapt(sample_source())[0]
    ledger = AtomicLedger(tmp_path / "infrastructure.jsonl")
    service = StatetechDataService(ledger, SchemaRegistry(REPOSITORY_ROOT))
    raw_entity = service.register_entity(
        entity_type=source_record.entity_type,
        natural_key=source_record.natural_key,
        payload=source_record.payload,
        provenance=source_record.provenance,
        evidences=source_record.evidences,
    )

    with pytest.raises(ValueError, match="review_note"):
        register_infrastructure_review(
            service,
            source_record=source_record,
            previous_version_id=raw_entity.version_id,
            review_status="probable",
            reviewer="reviewer:test",
        )


def test_curated_and_publishable_views_do_not_include_pending_or_false_positive():
    pending = {"review_status": "pending_review", "detected_value": "A"}
    confirmed = {"review_status": "confirmed", "detected_value": "B"}
    probable = {"review_status": "probable", "detected_value": "C"}
    inconclusive = {"review_status": "inconclusive", "detected_value": "D"}
    false_positive = {"review_status": "false_positive", "detected_value": "E"}

    rows = [pending, confirmed, probable, inconclusive, false_positive]

    assert [row["detected_value"] for row in curated_rows(rows)] == ["B", "C", "D"]
    assert [row["detected_value"] for row in publishable_rows(rows)] == ["B", "C"]
