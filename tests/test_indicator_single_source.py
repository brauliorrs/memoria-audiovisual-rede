import json
from pathlib import Path

import pytest

from memoria_audiovisual.scientific_infrastructure.single_source_audit import (
    assert_single_source,
    find_duplicate_definitions,
)


ROOT = Path(__file__).resolve().parents[1]


def test_repository_has_no_competing_indicator_definitions():
    findings = find_duplicate_definitions(ROOT)
    assert findings == ()
    assert_single_source(findings)


def test_audit_detects_semantic_copy(tmp_path: Path):
    registry_path = tmp_path / "data/templates/analytics/indicator_registry.json"
    registry_path.parent.mkdir(parents=True)
    question = "Qual percentual suficientemente longo deve ser detectado como definição duplicada?"
    registry_path.write_text(
        json.dumps(
            {
                "indicators": [
                    {
                        "indicator_id": "example",
                        "scientific_question": question,
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    duplicate = tmp_path / "src/duplicate.py"
    duplicate.parent.mkdir(parents=True)
    duplicate.write_text(f'QUESTION = "{question}"\n', encoding="utf-8")

    findings = find_duplicate_definitions(tmp_path)
    assert len(findings) == 1
    assert findings[0].indicator_id == "example"
    assert findings[0].field == "scientific_question"
    with pytest.raises(ValueError, match="Definições científicas duplicadas"):
        assert_single_source(findings)


def test_outputs_and_tests_are_not_treated_as_sources(tmp_path: Path):
    registry_path = tmp_path / "data/templates/analytics/indicator_registry.json"
    registry_path.parent.mkdir(parents=True)
    title = "Título científico suficientemente longo para a auditoria permanente"
    registry_path.write_text(
        json.dumps(
            {"indicators": [{"indicator_id": "example", "title": title}]},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    output = tmp_path / "data/output/snapshot.json"
    output.parent.mkdir(parents=True)
    output.write_text(title, encoding="utf-8")
    fixture = tmp_path / "tests/fixture.json"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(title, encoding="utf-8")

    assert find_duplicate_definitions(tmp_path) == ()
