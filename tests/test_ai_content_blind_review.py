import json
from collections import Counter
from pathlib import Path

from scripts.assess_ai_content_blind_queue import assess_unit

QUEUE = Path(
    "data/digital_infrastructure/ai_experiments/ai_content_blind_review_queue_v1.json"
)


def load_queue():
    return json.loads(QUEUE.read_text(encoding="utf-8"))


def test_blind_queue_has_four_entities_and_no_predictions():
    payload = load_queue()
    units = payload["units"]
    assert payload["review_protocol"]["prediction_blinding"] is True
    assert len(units) == 12
    assert Counter(unit["entity_id"] for unit in units) == {
        "bfi": 3,
        "ina": 3,
        "archipop": 3,
        "aapb": 3,
    }
    forbidden = {
        "prediction",
        "predicted_usage_class",
        "predicted_positive",
        "model_prediction",
        "model_status",
        "model_confidence",
    }
    for unit in units:
        assert forbidden.isdisjoint(unit)
        assert unit["review_status"] == "pending"
        assert unit["human_label"] is None
        assert str(unit["item_url"]).startswith("https://")


def test_metadata_triage_does_not_confuse_ai_topic_with_ai_production():
    payload = load_queue()
    unit = next(
        item for item in payload["units"]
        if item["review_unit_id"] == "ina-machine-hommes-ia-1972"
    )
    prediction = assess_unit(
        unit,
        fetch_surfaces=False,
        surface_output_dir=Path("data/output"),
        run_id="test",
    )
    assert prediction["assessment_stage"] == "metadata_triage"
    assert prediction["predicted_usage_class"] == "no_verified_ai_evidence"
    assert prediction["predicted_positive"] is False


def test_metadata_triage_keeps_animation_distinct_from_ai():
    payload = load_queue()
    unit = next(
        item for item in payload["units"]
        if item["review_unit_id"] == "archipop-animation-metamorphoses-1979-1981"
    )
    prediction = assess_unit(
        unit,
        fetch_surfaces=False,
        surface_output_dir=Path("data/output"),
        run_id="test",
    )
    assert prediction["predicted_usage_class"] == "no_verified_ai_evidence"
    assert prediction["predicted_positive"] is False
