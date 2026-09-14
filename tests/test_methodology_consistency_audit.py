from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from memoria_audiovisual.analytics.pipeline import default_indicator_registry
from memoria_audiovisual.scientific_infrastructure.methodology_consistency_audit import (
    assert_methodology_consistency,
    audit_methodologies,
)

ROOT = Path(__file__).resolve().parents[1]


def _methodologies() -> list[dict]:
    payload = json.loads(
        (ROOT / "data/templates/analytics/methodology_registry.json").read_text(
            encoding="utf-8"
        )
    )
    return payload["methodologies"]


def test_all_registered_methodologies_are_complete_and_consistent():
    report = audit_methodologies(_methodologies(), default_indicator_registry())

    assert report.is_valid
    assert report.methodology_count == 9
    assert report.complete_count == 9
    assert set(report.methodology_classes) == {
        "access",
        "composite_index",
        "infrastructure_coverage",
        "interoperability_coverage",
        "metadata_coverage",
    }
    assert_methodology_consistency(report)


def test_status_policy_cannot_include_and_exclude_same_state():
    methodologies = deepcopy(_methodologies())
    methodologies[0]["excluded_statuses"].append("detected")

    report = audit_methodologies(methodologies, default_indicator_registry())

    assert any(item.rule == "status_policy" for item in report.findings)
    with pytest.raises(ValueError, match="status_policy"):
        assert_methodology_consistency(report)


def test_methodology_version_must_match_implementation():
    methodologies = deepcopy(_methodologies())
    methodologies[0]["methodology_version"] = "999.0.0"

    report = audit_methodologies(methodologies, default_indicator_registry())

    assert any(
        item.rule == "version" and "methodology_version" in item.message
        for item in report.findings
    )


def test_composite_weights_must_sum_to_one():
    methodologies = deepcopy(_methodologies())
    composite = next(
        item for item in methodologies if item["indicator_id"] == "interoperability_index"
    )
    composite["components"][0]["weight"] = 0.4

    report = audit_methodologies(methodologies, default_indicator_registry())

    assert any(
        item.indicator_id == "interoperability_index"
        and item.rule == "composite"
        and "soma dos pesos" in item.message
        for item in report.findings
    )


def test_percentage_formula_must_make_scale_explicit():
    methodologies = deepcopy(_methodologies())
    methodologies[0]["formula"] = "numerador / denominador"

    report = audit_methodologies(methodologies, default_indicator_registry())

    assert any(item.rule == "formula" for item in report.findings)
