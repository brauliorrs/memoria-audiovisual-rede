from memoria_audiovisual.digital_infrastructure.ai_content_validation import (
    AI_CONTENT_VALIDATION_SAMPLE_ID,
    CONTROLS,
    build_ai_content_validation_sample,
    evaluate_ai_content_validation_sample,
)


def test_content_validation_sample_is_balanced_and_versioned():
    sample = build_ai_content_validation_sample()
    assert sample["sample"]["sample_id"] == AI_CONTENT_VALIDATION_SAMPLE_ID
    assert sample["sample"]["is_prevalence_sample"] is False
    assert sample["sample"]["does_not_modify_official_baseline"] is True
    assert sample["summary"]["controls"] == 6
    assert sample["summary"]["positive_controls"] == 3
    assert sample["summary"]["negative_controls"] == 3
    assert set(sample["summary"]["languages"]) == {"en", "es"}


def test_controls_are_item_level_and_have_reproducible_evidence():
    for control in CONTROLS:
        assert control.item_id
        assert control.item_url.startswith("https://")
        assert control.evidence_url.startswith("https://")
        assert control.evidence_text.strip()
        assert control.evidence_source_role


def test_reference_controls_calibrate_binary_ai_presence():
    report = evaluate_ai_content_validation_sample()
    assert report["controls"] == 6
    assert report["binary"] == {
        "true_positive": 3,
        "false_positive": 0,
        "true_negative": 3,
        "false_negative": 0,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
    }


def test_reference_controls_require_exact_class_match():
    report = evaluate_ai_content_validation_sample()
    assert report["exact_class_matches"] == 6
    assert report["exact_class_accuracy"] == 1.0
