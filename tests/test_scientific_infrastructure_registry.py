import json
from pathlib import Path

import pytest

from memoria_audiovisual.scientific_infrastructure import (
    ArtifactScope,
    ArtifactSpec,
    ArtifactFormat,
    ArtifactState,
    InfrastructureRegistry,
    ScientificInfrastructureLoader,
    build_default_registry,
)


def test_default_registry_contains_canonical_artifacts(tmp_path: Path):
    registry = build_default_registry(tmp_path)

    assert "indicator_catalog" in registry
    assert "methodology_registry" in registry
    assert "snapshot_indicators" in registry
    assert "parameter_coverage" in registry
    assert "ledger" in registry
    assert len(registry.all()) == 12


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


def test_loader_reports_missing_invalid_empty_and_found(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)

    missing = loader.load("indicator_catalog")
    assert missing.state is ArtifactState.MISSING

    indicator_path = tmp_path / "data/templates/analytics/indicator_catalog.json"
    indicator_path.parent.mkdir(parents=True)
    indicator_path.write_text("{invalid", encoding="utf-8")
    invalid = loader.load("indicator_catalog")
    assert invalid.state is ArtifactState.INVALID

    indicator_path.write_text("{}", encoding="utf-8")
    empty = loader.load("indicator_catalog")
    assert empty.state is ArtifactState.EMPTY

    indicator_path.write_text(json.dumps({"indicators": [{"indicator_id": "x"}]}), encoding="utf-8")
    found = loader.load("indicator_catalog")
    assert found.state is ArtifactState.FOUND
    assert found.is_usable


def test_loader_uses_coverage_alternative_path(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)
    snapshot_dir = registry.coverage_root / "snapshot-1"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "coverage.json").write_text(json.dumps({"rows": [1]}), encoding="utf-8")

    loaded = loader.load("parameter_coverage", snapshot_dir=snapshot_dir)

    assert loaded.state is ArtifactState.FOUND
    assert loaded.path.name == "coverage.json"


def test_latest_snapshot_loaders_preserve_public_keys(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    loader = ScientificInfrastructureLoader(registry)
    analytics = registry.analytics_root / "2026-08-03"
    analytics.mkdir(parents=True)
    (analytics / "snapshot_indicators.json").write_text(json.dumps({"indicators": []}), encoding="utf-8")

    loaded = loader.load_latest_analytics_snapshot()

    assert set(loaded) == {"snapshot", "indicators", "manifest", "run", "sensitivity"}
    assert loaded["snapshot"].payload["snapshot_id"] == "2026-08-03"
    assert loaded["indicators"].state is ArtifactState.FOUND
    assert loaded["manifest"].state is ArtifactState.MISSING
