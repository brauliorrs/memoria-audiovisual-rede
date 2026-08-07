import pytest

from memoria_audiovisual.digital_infrastructure.ai_post_baseline_validation import (
    evaluate_human_reviews,
    validate_review_rows,
)


def row(unit, model_status, human_label, task="audiovisual_collection_detection", language="en"):
    return {
        "review_unit_id": unit,
        "review_status": "completed",
        "human_label": human_label,
        "reviewer_id": "reviewer-1",
        "reviewed_at": "2026-08-06T12:00:00Z",
        "model_status": model_status,
        "task": task,
        "language_group": language,
        "geographic_group": "Europe",
        "analytical_stratum": "archive",
    }


def test_calculates_confusion_matrix_precision_recall_and_f1():
    report = evaluate_human_reviews([
        row("tp", "detected_pending_review", "positive"),
        row("fp", "detected_pending_review", "negative"),
        row("tn", "not_identified_on_assessed_surfaces", "negative"),
        row("fn", "not_identified_on_assessed_surfaces", "positive"),
    ])

    matrix = report["overall"]["confusion_matrix"]
    assert matrix == {
        "true_positive": 1,
        "false_positive": 1,
        "true_negative": 1,
        "false_negative": 1,
    }
    assert report["overall"]["precision"] == 0.5
    assert report["overall"]["recall"] == 0.5
    assert report["overall"]["f1"] == 0.5
    assert report["does_not_modify_official_baseline"] is True


def test_pending_and_ambiguous_rows_do_not_enter_binary_metrics():
    pending = {
        "review_unit_id": "pending",
        "review_status": "pending",
        "human_label": None,
        "model_status": "detected_pending_review",
        "task": "institutional_ai_use",
        "language_group": "fr",
        "geographic_group": "Europe",
        "analytical_stratum": "institution",
    }
    ambiguous = row("ambiguous", "detected_pending_review", "ambiguous", task="institutional_ai_use")
    report = evaluate_human_reviews([pending, ambiguous])

    assert report["reviewed_units"] == 1
    assert report["pending_units"] == 1
    assert report["ambiguous_or_not_assessable"] == 1
    assert report["overall"]["evaluated"] == 0
    assert report["activation_decision"]["institutional_ai_use"] == "insufficient_human_review"


def test_completed_review_requires_label_reviewer_and_timestamp():
    with pytest.raises(ValueError, match="human_label inválido"):
        validate_review_rows([
            {
                "review_unit_id": "invalid",
                "review_status": "completed",
                "human_label": "",
                "reviewer_id": "reviewer",
                "reviewed_at": "2026-08-06T12:00:00Z",
            }
        ])


def test_rejects_duplicate_review_units():
    with pytest.raises(ValueError, match="duplicado"):
        validate_review_rows([
            {"review_unit_id": "same", "review_status": "pending"},
            {"review_unit_id": "same", "review_status": "pending"},
        ])
