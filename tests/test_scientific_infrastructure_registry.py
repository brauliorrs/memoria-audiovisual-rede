import json
from pathlib import Path

import pytest

from memoria_audiovisual.scientific_infrastructure import (
    ArtifactFormat,
    ArtifactScope,
    ArtifactSpec,
    ArtifactState,
    InfrastructureRegistry,
    ScientificInfrastructureLoader,
    build_default_registry,
)


def _valid_indicator_registry() -> dict:
    return {
        "registry": {
            "registry_id": "scientific_indicator_registry",
            "name": "Registro científico de indicadores",
            "platform": "Memória Audiovisual em Rede",
            "registry_version": "1.0.0",
            "methodology_registry_version": "1.0.0",
            "schema_version": "1.0.0",
            "language": "pt-BR",
            "status": "active",
            "indicator_count": 1,
            "compatibility": {
                "pipeline": ">=1.0.0",
                "interface": ">=1.0.0",
                "snapshot": ">=1.0.0",
            },
            "governance": {
                "identity_is_stable": True,
                "methodology_is_versioned_separately": True,
                "results_are_not_stored_in_registry": True,
                "breaking_changes_require_major_version": True,
            },
        },
        "indicators": [
            {
                "indicator_id": "test_indicator",
                "indicator_version": "1.0.0",
                "status": "implemented",
                "title": "Indicador de teste",
                "scientific_question": "O que o indicador mede?",
                "scientific_rationale": "Racional científico.",
                "selection_rationale": "Justificativa de seleção.",
                "dimension": "test",
                "unit": "percent",
                "expected_range": {"minimum": 0, "maximum": 100},
                "result_type": "coverage_percentage",
                "interpretation": "Valores maiores indicam maior cobertura.",
                "does_not_measure": ["qualidade"],
                "relationship_to_other_indicators": "Independente.",
                "corpus_rule": "Somente corpora avaliáveis.",
                "evidence_requirements": ["evidência verificável"],
                "dependencies": [],
                "methodology_id": "test_indicator",
                "methodology_reference": "methodology_registry.json#test_indicator",
            }
        ],
    }


def test_default_registry_contains_canonical_artifacts(tmp_path: Path):
    registry = build_default_registry(tmp_path)

    assert "indicator_registry" in registry
    assert "indicator_catalog" not in registry
    assert "methodology_registry" in registry
    assert "indicator_results_registry" in registry
    assert "snapshot_indicators" in registry
    assert "parameter_coverage" in registry
    assert "operational_baseline_latest" in registry
    assert "operational_baseline_manifest" in registry
    assert "ledger" in registry
    assert len(registry.all()) == 15

    indicator_spec = registry.get("indicator_registry")
    assert indicator_spec.relative_path.endswith("indicator_registry.json")
    assert "indicator_catalog.json" not in indicator_spec.relative_path


def test_registry_rejects_duplicate_keys(tmp_path: Path):
    duplicated = ArtifactSpec(
        key="same",
        label="Same",
        relative_path="same.json",
        format=ArtifactFormat.JSON,
        scope=ArtifactScope.STATIC,
    )
    with pytest.raises(ValueError, match="must be unique"):
        InfrastructureRegistry(tmp_path, [duplicated, duplicated])


def test_loader_reports_missing_invalid_and_found_for_canonical_registry(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)

    missing = loader.load_indicator_registry()
    assert missing.state is ArtifactState.MISSING

    indicator_path = tmp_path / "data/templates/analytics/indicator_registry.json"
    indicator_path.parent.mkdir(parents=True)
    indicator_path.write_text("{invalid", encoding="utf-8")
    invalid_json = loader.load_indicator_registry()
    assert invalid_json.state is ArtifactState.INVALID

    indicator_path.write_text("{}", encoding="utf-8")
    invalid_contract = loader.load_indicator_registry()
    assert invalid_contract.state is ArtifactState.INVALID

    indicator_path.write_text(
        json.dumps(_valid_indicator_registry(), ensure_ascii=False),
        encoding="utf-8",
    )
    found = loader.load_indicator_registry()
    assert found.state is ArtifactState.FOUND
    assert found.is_usable

    parsed = loader.parsed_indicator_registry()
    assert parsed is not None
    assert parsed.get("test_indicator")["title"] == "Indicador de teste"


def test_static_loader_exposes_only_canonical_indicator_source(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)

    loaded = loader.load_static()

    assert set(loaded) == {
        "indicator_registry",
        "methodology_registry",
        "indicator_results_registry",
    }
    assert "indicator_catalog" not in loaded


def test_loader_uses_coverage_alternative_path(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)
    snapshot_dir = registry.coverage_root / "snapshot-1"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "coverage.json").write_text(
        json.dumps({"rows": [1]}), encoding="utf-8"
    )

    loaded = loader.load("parameter_coverage", snapshot_dir=snapshot_dir)

    assert loaded.state is ArtifactState.FOUND
    assert loaded.path.name == "coverage.json"


def test_latest_snapshot_loaders_preserve_public_keys(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)
    analytics = registry.analytics_root / "2026-08-03"
    analytics.mkdir(parents=True)
    (analytics / "snapshot_indicators.json").write_text(
        json.dumps({"indicators": []}), encoding="utf-8"
    )

    loaded = loader.load_latest_analytics_snapshot()

    assert set(loaded) == {"snapshot", "indicators", "manifest", "run", "sensitivity"}
    assert loaded["snapshot"].payload["snapshot_id"] == "2026-08-03"
    assert loaded["indicators"].state is ArtifactState.FOUND
    assert loaded["manifest"].state is ArtifactState.MISSING


def test_operational_baseline_is_resolved_only_from_official_pointer(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)
    snapshot_id = "operational-baseline-v1-123"
    pointer_path = tmp_path / "data/output/operational_baseline_latest.json"
    pointer_path.parent.mkdir(parents=True)
    pointer_path.write_text(
        json.dumps(
            {
                "snapshot_id": snapshot_id,
                "manifest_path": (
                    f"data/output/analytics/{snapshot_id}/operational_baseline_manifest.json"
                ),
                "manifest_sha256": "abc",
                "status": "completed",
                "official_baseline": True,
            }
        ),
        encoding="utf-8",
    )
    snapshot_dir = registry.analytics_root / snapshot_id
    snapshot_dir.mkdir(parents=True)
    for filename, payload in {
        "snapshot_indicators.json": {"status": "completed", "results": []},
        "manifest.json": {"status": "completed"},
        "run.json": {"status": "completed"},
        "interoperability_sensitivity.json": {"status": "completed"},
        "operational_baseline_manifest.json": {
            "status": "completed",
            "official_baseline": True,
        },
    }.items():
        (snapshot_dir / filename).write_text(json.dumps(payload), encoding="utf-8")

    loaded = loader.load_operational_baseline()

    assert set(loaded) == {
        "pointer",
        "snapshot",
        "indicators",
        "manifest",
        "run",
        "sensitivity",
        "operational_manifest",
    }
    assert loaded["pointer"].state is ArtifactState.FOUND
    assert loaded["snapshot"].payload["snapshot_id"] == snapshot_id
    assert loaded["operational_manifest"].state is ArtifactState.FOUND


def test_operational_baseline_does_not_fall_back_to_newest_directory(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)
    unpointed = registry.analytics_root / "newest-but-not-official"
    unpointed.mkdir(parents=True)
    (unpointed / "snapshot_indicators.json").write_text("{}", encoding="utf-8")

    loaded = loader.load_operational_baseline()

    assert set(loaded) == {"pointer"}
    assert loaded["pointer"].state is ArtifactState.MISSING


def test_operational_baseline_rejects_unsafe_snapshot_id(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)
    pointer_path = tmp_path / "data/output/operational_baseline_latest.json"
    pointer_path.parent.mkdir(parents=True)
    pointer_path.write_text(
        json.dumps({"snapshot_id": "../outside", "official_baseline": True}),
        encoding="utf-8",
    )

    loaded = loader.load_operational_baseline()

    assert loaded["pointer"].state is ArtifactState.INVALID
    assert "inseguro" in loaded["pointer"].error
