import json
from pathlib import Path

from scripts.build_surface_type_review_queue import build_surface_type_artifacts


def write_report(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "root_url": "https://example.org/",
                "pages": [
                    {
                        "url": "https://example.org/",
                        "parent_url": None,
                        "depth": 0,
                        "title": "Example Archive",
                        "fetch_status": "fetched",
                        "content_type": "text/html",
                        "media_urls": [],
                        "text": "Archive homepage",
                        "metadata_text": "",
                        "structured_text": "",
                    },
                    {
                        "url": "https://example.org/video/item-123456",
                        "parent_url": "https://example.org/",
                        "depth": 1,
                        "title": "Interview 123456",
                        "fetch_status": "fetched",
                        "content_type": "text/html",
                        "media_urls": ["https://cdn.example.org/123456.mp4"],
                        "text": "Interview",
                        "metadata_text": "og:video: https://cdn.example.org/123456.mp4",
                        "structured_text": (
                            '{"@type":"VideoObject","identifier":"123456",'
                            '"contentUrl":"https://cdn.example.org/123456.mp4"}'
                        ),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_review_queue_blinds_predictions(tmp_path):
    report = tmp_path / "run-1" / "ina" / "surface_discovery_report.json"
    write_report(report)

    predictions, review = build_surface_type_artifacts(tmp_path, max_units=10)

    assert predictions["schema_version"] == "2.0.0"
    assert predictions["protocol_version"] == "2.0.0"
    assert review["schema_version"] == "2.0.0"
    assert review["protocol_version"] == "2.0.0"
    assert predictions["units_total"] == 2
    assert review["units_total"] == 2
    assert review["model_prediction_blinded"] is True
    assert "predicted_surface_type" in predictions["units"][0]
    assert "predicted_access_state" in predictions["units"][0]
    assert "predicted_surface_type" not in review["units"][0]
    assert review["units"][0]["collector_access_state"] == "accessible"
    assert review["units"][0]["human_surface_type"] is None
    assert review["units"][0]["human_access_state"] is None
    assert review["units"][0]["review_status"] == "pending"


def test_predictions_keep_item_level_separate_from_human_label(tmp_path):
    report = tmp_path / "run-1" / "bfi" / "surface_discovery_report.json"
    write_report(report)

    predictions, review = build_surface_type_artifacts(tmp_path, max_units=10)

    item_prediction = next(
        row for row in predictions["units"] if row["page_url"].endswith("item-123456")
    )
    item_review = next(
        row for row in review["units"] if row["page_url"].endswith("item-123456")
    )
    assert item_prediction["predicted_surface_type"] == "audiovisual_item"
    assert item_prediction["predicted_item_level"] is True
    assert item_prediction["predicted_access_state"] == "accessible"
    assert item_review["human_is_item_level"] is None


def test_independent_sample_excludes_reference_urls_and_preserves_blinding(tmp_path):
    report = tmp_path / "run-1" / "new-corpus" / "surface_discovery_report.json"
    write_report(report)

    predictions, review = build_surface_type_artifacts(
        tmp_path,
        max_units=10,
        exclude_page_urls={"https://example.org/"},
        artifact_id="independent-predictions-v2",
        queue_id="independent-review-v2",
        stage="t2a_mar_surface_typing_independent_validation",
        sample_role="independent_ecological_validation",
        is_independent_validation_sample=True,
    )

    assert predictions["artifact_id"] == "independent-predictions-v2"
    assert review["queue_id"] == "independent-review-v2"
    assert predictions["is_independent_validation_sample"] is True
    assert review["is_independent_validation_sample"] is True
    assert predictions["sample_role"] == "independent_ecological_validation"
    assert review["stage"] == "t2a_mar_surface_typing_independent_validation"
    assert review["excluded_reference_urls_total"] == 1
    assert review["excluded_observed_matches"] == 1
    assert review["units_total"] == 1
    assert review["units"][0]["page_url"] == "https://example.org/video/item-123456"
    assert "predicted_surface_type" not in review["units"][0]
    assert predictions["units"][0]["review_unit_id"] == review["units"][0]["review_unit_id"]


def test_missing_input_root_produces_explicit_no_inputs_state(tmp_path):
    predictions, review = build_surface_type_artifacts(
        tmp_path / "missing",
        max_units=10,
    )
    assert predictions["status"] == "no_inputs_found"
    assert review["status"] == "no_inputs_found"
    assert review["units_total"] == 0
