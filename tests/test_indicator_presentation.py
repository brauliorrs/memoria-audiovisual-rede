import json
from pathlib import Path

from memoria_audiovisual.ui.indicator_presentation import (
    build_indicator_presentations,
    registry_summary,
)


ROOT = Path(__file__).resolve().parents[1]


def _payloads():
    registry = json.loads(
        (ROOT / "data/templates/analytics/indicator_registry.json").read_text(
            encoding="utf-8"
        )
    )
    methodology = json.loads(
        (ROOT / "data/templates/analytics/methodology_registry.json").read_text(
            encoding="utf-8"
        )
    )
    methodologies = {
        str(item["indicator_id"]): item for item in methodology["methodologies"]
    }
    return registry, methodologies


def test_summary_uses_registry_metadata_without_hardcoded_version():
    registry, _ = _payloads()
    summary = registry_summary(registry)

    assert summary["version"] == registry["registry"]["registry_version"]
    assert summary["indicator_count"] == 9
    assert summary["dimension_count"] >= 1
    assert summary["language"] == "pt-BR"


def test_presentations_cover_every_canonical_indicator():
    registry, methodologies = _payloads()
    presentations = build_indicator_presentations(
        registry["indicators"], methodologies
    )

    assert len(presentations) == registry["registry"]["indicator_count"]
    assert {item.indicator_id for item in presentations} == {
        item["indicator_id"] for item in registry["indicators"]
    }


def test_semantic_fields_are_exposed_from_registry():
    registry, methodologies = _payloads()
    source = registry["indicators"][0]
    presentation = build_indicator_presentations([source], methodologies)[0]

    assert presentation.scientific_question == source["scientific_question"]
    assert presentation.scientific_rationale == source["scientific_rationale"]
    assert presentation.selection_rationale == source["selection_rationale"]
    assert presentation.interpretation == source["interpretation"]
    assert presentation.corpus_rule == source["corpus_rule"]
    assert presentation.methodology_reference == source["methodology_reference"]


def test_access_index_methodology_is_available_and_resolved():
    registry, methodologies = _payloads()
    source = next(
        item
        for item in registry["indicators"]
        if item["indicator_id"] == "audiovisual_archive_access_index"
    )
    presentation = build_indicator_presentations([source], methodologies)[0]

    assert presentation.methodology_available
    assert presentation.methodology_id == "audiovisual_archive_access_index"
    assert presentation.methodology_reference == (
        "methodology_registry.json#audiovisual_archive_access_index"
    )
    assert presentation.formula == (
        "100 * arquivos_elegiveis_sem_barreira_observada / "
        "arquivos_elegiveis_avaliaveis"
    )


def test_missing_methodology_remains_explicit_for_unregistered_definition():
    indicator = {
        "indicator_id": "example_without_methodology",
        "title": "Exemplo sem metodologia",
        "methodology_id": "example_without_methodology",
        "methodology_reference": (
            "methodology_registry.json#example_without_methodology"
        ),
    }
    presentation = build_indicator_presentations([indicator], {})[0]

    assert not presentation.methodology_available
    assert presentation.formula == ""


def test_expected_range_and_dependencies_are_presentable():
    indicator = {
        "indicator_id": "example",
        "title": "Exemplo",
        "expected_range": {"minimum": 0, "maximum": 100},
        "dependencies": ["a", "b"],
        "evidence_requirements": ["fonte pública"],
    }
    presentation = build_indicator_presentations([indicator], {})[0]

    assert presentation.expected_range == "0 a 100"
    assert presentation.dependencies == ("a", "b")
    assert presentation.evidence_requirements == ("fonte pública",)
