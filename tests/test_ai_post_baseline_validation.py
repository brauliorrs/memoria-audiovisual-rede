import pytest

from memoria_audiovisual.digital_infrastructure.ai_post_baseline_validation import (
    apply_review_amendments,
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
    assert report["amendments_applied"] == 0


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


def test_amendment_preserves_original_and_changes_metric_projection():
    rows = [row("ina-ai", "detected_pending_review", "negative", task="institutional_ai_use", language="fr")]
    amendments = [
        {
            "amendment_id": "amend-1",
            "review_unit_id": "ina-ai",
            "previous_human_label": "negative",
            "human_label": "positive",
            "human_decision": "Evidência institucional encontrada em superfície especializada.",
            "reviewer_id": "reviewer-1",
            "reviewed_at": "2026-08-14T18:46:00Z",
            "validation_url": "https://data.ina.fr/traitements-ia",
            "amendment_reason": "surface_scope_expansion",
        }
    ]

    projected = apply_review_amendments(rows, amendments)
    assert projected[0]["human_label_original"] == "negative"
    assert projected[0]["human_label"] == "positive"
    assert projected[0]["review_status"] == "corrected"

    report = evaluate_human_reviews(rows, amendments=amendments)
    assert report["amendments_applied"] == 1
    assert report["overall"]["confusion_matrix"]["true_positive"] == 1
    assert report["overall"]["confusion_matrix"]["false_positive"] == 0


def test_amendment_rejects_mismatched_previous_label():
    rows = [row("unit", "detected_pending_review", "negative")]
    with pytest.raises(ValueError, match="esperava label anterior"):
        apply_review_amendments(
            rows,
            [
                {
                    "amendment_id": "bad",
                    "review_unit_id": "unit",
                    "previous_human_label": "positive",
                    "human_label": "negative",
                    "reviewer_id": "reviewer-1",
                    "reviewed_at": "2026-08-14T18:46:00Z",
                }
            ],
        )
