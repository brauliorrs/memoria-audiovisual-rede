import json
from pathlib import Path

import pytest

from memoria_audiovisual.scientific_infrastructure.indicator_registry import (
    IndicatorRegistryError,
    REGISTRY_RELATIVE_PATH,
    load_indicator_registry,
    validate_indicator_registry,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
EXPECTED_IDS = {
    "audiovisual_archive_access_index",
    "api_coverage",
    "interoperability_coverage",
    "iiif_coverage",
    "oai_pmh_coverage",
    "dublin_core_coverage",
    "schema_org_coverage",
    "json_ld_coverage",
    "interoperability_index",
}


def _payload():
    return json.loads((ROOT_DIR / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8"))


def test_canonical_registry_loads_and_contains_exactly_nine_indicators():
    registry = load_indicator_registry(ROOT_DIR)

    assert registry.version == "1.0.0"
    assert len(registry.indicators) == 9
    assert set(registry.indicator_ids) == EXPECTED_IDS


def test_every_indicator_has_stable_identity_and_separate_methodology_reference():
    registry = load_indicator_registry(ROOT_DIR)

    for indicator in registry.indicators:
        assert indicator["indicator_id"] == indicator["methodology_id"]
        assert indicator["methodology_reference"].startswith("methodology_registry.json#")
        assert indicator["scientific_question"]
        assert indicator["scientific_rationale"]
        assert indicator["evidence_requirements"]


def test_duplicate_ids_are_rejected():
    payload = _payload()
    payload["indicators"].append(dict(payload["indicators"][0]))
    payload["registry"]["indicator_count"] += 1

    with pytest.raises(IndicatorRegistryError, match="IDs duplicados"):
        validate_indicator_registry(payload)


def test_unknown_dependency_is_rejected():
    payload = _payload()
    payload["indicators"][0]["dependencies"] = ["unknown_indicator"]

    with pytest.raises(IndicatorRegistryError, match="Dependências não registradas"):
        validate_indicator_registry(payload)


def test_declared_count_must_match_registry_content():
    payload = _payload()
    payload["registry"]["indicator_count"] = 8

    with pytest.raises(IndicatorRegistryError, match="indicator_count"):
        validate_indicator_registry(payload)


def test_methodology_identity_must_match_indicator_identity():
    payload = _payload()
    payload["indicators"][0]["methodology_id"] = "another_methodology"

    with pytest.raises(IndicatorRegistryError, match="methodology_id"):
        validate_indicator_registry(payload)
