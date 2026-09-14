from memoria_audiovisual.digital_infrastructure.ai_content_production import (
    AIContentUsageObservation,
    classify_ai_content_usage,
    observation_to_experiment_record,
    quantify_ai_content_by,
    quantify_ai_content_usage,
)


def test_explicit_fully_synthetic_disclosure_is_positive():
    observation = classify_ai_content_usage(
        entity_id="example",
        item_id="item-1",
        source_url="https://example.org/item-1",
        texts=["This film is fully AI-generated."],
        language="en",
    )
    assert observation.usage_class == "fully_synthetic"
    assert observation.is_ai_positive
    assert observation.is_synthetic

    record = observation_to_experiment_record(observation, run_id="run-1")
    assert record.task == "ai_content_production_detection"
    assert record.status == "detected_pending_review"
    assert record.item_id == "item-1"


def test_supporting_detector_score_is_not_sufficient_for_positive():
    observation = classify_ai_content_usage(
        entity_id="example",
        item_id="item-2",
        texts=["Historical film digitised in 2024."],
        supporting_model_score=0.97,
    )
    assert observation.usage_class == "no_verified_ai_evidence"
    assert not observation.is_ai_positive
    assert observation.evidence_strength == "supporting_signal_only"


def test_material_modification_and_assisted_production_are_distinct():
    modified = classify_ai_content_usage(
        entity_id="example",
        item_id="item-3",
        texts=["The documentary uses a cloned voice and AI dubbing."],
    )
    assisted = classify_ai_content_usage(
        entity_id="example",
        item_id="item-4",
        texts=["Production used AI-assisted editing."],
    )
    assert modified.usage_class == "materially_ai_modified"
    assert assisted.usage_class == "ai_assisted_production"


def test_quantification_uses_evaluable_items_as_denominator():
    observations = [
        AIContentUsageObservation(
            entity_id="a",
            item_id="1",
            usage_class="fully_synthetic",
            evidence_strength="verified_disclosure",
            language="en",
        ),
        AIContentUsageObservation(
            entity_id="a",
            item_id="2",
            usage_class="ai_assisted_production",
            evidence_strength="verified_disclosure",
            language="en",
        ),
        AIContentUsageObservation(
            entity_id="b",
            item_id="3",
            usage_class="no_verified_ai_evidence",
            evidence_strength="none",
            language="fr",
        ),
        AIContentUsageObservation(
            entity_id="b",
            item_id="4",
            usage_class="not_assessable",
            evidence_strength="none",
            language="fr",
        ),
    ]
    result = quantify_ai_content_usage(observations)
    assert result.items_total == 4
    assert result.items_evaluable == 3
    assert result.items_with_ai_evidence == 2
    assert result.items_synthetic == 1
    assert result.share_with_ai_evidence == 2 / 3
    assert result.share_synthetic == 1 / 3

    by_entity = quantify_ai_content_by(observations, attribute="entity_id")
    assert by_entity["a"].share_with_ai_evidence == 1.0
    assert by_entity["b"].items_not_assessable == 1
