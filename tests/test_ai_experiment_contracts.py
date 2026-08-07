import pytest

from memoria_audiovisual.digital_infrastructure.ai_contracts import (
    AIEvidenceReference,
    AIExperimentRecord,
    AIModelDescriptor,
)


def test_ai_record_is_versioned_and_keeps_dimension_separate():
    record = AIExperimentRecord(
        run_id="run-1",
        entity_id="ina",
        task="institutional_ai_use",
        status="experimental",
        prediction="declared_tool_use",
        confidence=0.8,
        evidence=(
            AIEvidenceReference(
                evidence_id="evidence-1",
                evidence_type="documentary",
                source_url="https://example.org/policy",
            ),
        ),
        model=AIModelDescriptor(
            provider="local",
            model_name="baseline",
            model_version="1",
        ),
    )
    payload = record.to_dict()
    assert payload["dimension"] == "institutional_ai_use"
    assert payload["experiment_id"].startswith("ai-experiment_")
    assert payload["record_version_id"].startswith(payload["experiment_id"] + "@")
    assert payload["evidence"][0]["evidence_id"] == "evidence-1"


def test_confidence_outside_interval_is_rejected():
    with pytest.raises(ValueError, match="confidence"):
        AIExperimentRecord(
            run_id="run-1",
            entity_id="ina",
            task="institutional_ai_use",
            status="experimental",
            confidence=1.1,
        )


def test_synthetic_video_detection_requires_item_level_target():
    with pytest.raises(ValueError, match="exige item_id"):
        AIExperimentRecord(
            run_id="run-1",
            entity_id="ina",
            task="synthetic_video_detection",
            status="experimental",
        )


def test_error_requires_diagnostic():
    with pytest.raises(ValueError, match="status error"):
        AIExperimentRecord(
            run_id="run-1",
            entity_id="ina",
            task="institutional_ai_use",
            status="error",
        )
