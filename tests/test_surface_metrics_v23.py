"""Arithmetic and integrity verification; never creates new validation evidence."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from memoria_audiovisual.digital_infrastructure.surface_metrics_v23 import evaluate_development, gate

DATA = Path("data/digital_infrastructure/ai_experiments")


@pytest.fixture
def protocol():
    return json.loads((DATA / "m3_surface_type_independent_validation_protocol_v2_3_draft.json").read_text())


def rows(pairs):
    expected, humans, predictions = [], [], []
    for i, (human_label, predicted_label) in enumerate(pairs):
        identity = {"review_unit_id": str(i), "entity_id": f"synthetic-{i % 6}", "page_url": f"https://example.org/{i}"}
        expected.append(identity)
        humans.append({**identity, "human_surface_type": human_label,
                       "human_is_item_level": None if human_label == "unknown" else human_label in {"item_record", "audiovisual_item"},
                       "human_access_state": "accessible"})
        predictions.append({**identity, "predicted_surface_type": predicted_label,
                            "predicted_item_level": predicted_label in {"item_record", "audiovisual_item"},
                            "predicted_access_state": "accessible"})
    return expected, humans, predictions


def test_reproduces_frozen_val007_arithmetic_without_reclassification(protocol):
    historical = json.loads((DATA / "m3_surface_type_independent_evaluation_v2_2.json").read_text())
    fine = historical["multiclass_surface_type"]
    labels = fine["class_order"]
    pairs = [(labels[i], labels[j]) for i, row in enumerate(fine["confusion_matrix_rows_human_columns_prediction"]) for j, count in enumerate(row) for _ in range(count)]
    result = evaluate_development(*rows(pairs), protocol=protocol)
    assert result["decision"] == "FAIL"
    assert result["fine"]["accuracy"] == 7 / 31
    assert result["fine"]["weighted_f1"] == pytest.approx(fine["weighted_f1"])
    assert result["fine"]["macro_f1_all_classes"] == pytest.approx(fine["macro_f1_all_protocol_classes"])
    assert result["fine"]["macro_f1_supported_classes"] == pytest.approx(fine["macro_f1_human_supported_classes"])
    assert {k: result["binary"][k] for k in ("TP", "TN", "FP", "FN")} == {"TP": 2, "TN": 16, "FP": 0, "FN": 12}
    assert result["binary"]["human_unknown_excluded"] == 1
    assert result["binary"]["recall"] == 2 / 14
    assert result["access"]["agreement"] == 1
    assert result["is_independent_validation_result"] is False


def test_pass_still_never_promotes_m4(protocol):
    result = evaluate_development(*rows([("audiovisual_item", "audiovisual_item")] * 12 + [("search_or_index", "search_or_index")] * 12), protocol=protocol)
    assert result["decision"] == "PASS"
    assert result["m4_scaling_allowed"] is False
    assert all(result["entity_item_gate"].values())


def test_model_abstention_is_fn_but_human_unknown_excluded(protocol):
    result = evaluate_development(*rows([("audiovisual_item", "unknown"), ("unknown", "audiovisual_item")]), protocol=protocol)
    assert result["binary"]["FN"] == 1
    assert result["binary"]["FP"] == 0
    assert result["binary"]["human_unknown_excluded"] == 1
    assert result["access"]["total"] == 2
    assert result["binary"]["precision"] is None
    assert result["decision"] == "FAIL"  # known failure dominates undefined metric


def test_undefined_required_metrics_are_inconclusive(protocol):
    result = evaluate_development(*rows([("search_or_index", "search_or_index")] * 24), protocol=protocol)
    assert result["binary"]["precision"] is None
    assert result["binary"]["recall"] is None
    assert result["gates"]["fine_grained"] == "PASS"
    assert result["decision"] == "INCONCLUSIVE"


def test_insufficient_sample_is_not_pass(protocol):
    result = evaluate_development(*rows([("audiovisual_item", "audiovisual_item"), ("homepage", "homepage")]), protocol=protocol)
    assert result["gates"] == dict.fromkeys(("fine_grained", "item_level", "access"), "PASS")
    assert result["decision"] == "INCONCLUSIVE"


def test_entity_all_miss_fails_even_if_aggregate_passes(protocol):
    expected, human, predicted = rows([("audiovisual_item", "audiovisual_item")] * 12 + [("homepage", "homepage")] * 12)
    for i in (0, 6):
        predicted[i].update(predicted_surface_type="homepage", predicted_item_level=False)
    result = evaluate_development(expected, human, predicted, protocol=protocol)
    assert result["binary"]["recall"] >= .7
    assert result["entity_item_gate"]["synthetic-0"] is False
    assert result["gates"]["item_level"] == "FAIL"


@pytest.mark.parametrize("defect", ["missing", "extra", "duplicate", "invalid_label", "mapping", "integer_boolean", "entity", "url", "access"])
def test_integrity_invalid_never_shrinks_denominator(protocol, defect):
    expected, human, predicted = rows([("homepage", "homepage")] * 24)
    if defect == "missing":
        predicted.pop()
    elif defect == "extra":
        predicted.append({**predicted[0], "review_unit_id": "extra"})
    elif defect == "duplicate":
        human.append(deepcopy(human[0]))
    elif defect == "invalid_label":
        human[0]["human_surface_type"] = "not_a_label"
    elif defect == "mapping":
        human[0]["human_is_item_level"] = None
    elif defect == "integer_boolean":
        predicted[0]["predicted_item_level"] = 0
    elif defect == "entity":
        human[0]["entity_id"] = "other"
    elif defect == "url":
        predicted[0]["page_url"] = "https://example.org/other"
    elif defect == "access":
        del predicted[0]["predicted_access_state"]
    result = evaluate_development(expected, human, predicted, protocol=protocol)
    assert result["decision"] == "INVALID"
    assert "fine" not in result


def test_gate_precedence():
    assert gate([None, False]) == "FAIL"
    assert gate([True, None]) == "INCONCLUSIVE"
    assert gate([True, True]) == "PASS"
