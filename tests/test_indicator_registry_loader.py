import json
from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.loaders import (
    ArtifactState,
    ScientificInfrastructureLoader,
)
from memoria_audiovisual.scientific_infrastructure.registry import build_default_registry


ROOT = Path(__file__).resolve().parents[1]


def test_default_registry_uses_indicator_registry_only():
    registry = build_default_registry(ROOT)

    assert "indicator_registry" in registry
    assert "indicator_catalog" not in registry
    spec = registry.get("indicator_registry")
    assert spec.relative_path == "data/templates/analytics/indicator_registry.json"
    assert spec.required is True


def test_static_loader_exposes_only_canonical_indicator_source():
    loader = ScientificInfrastructureLoader(build_default_registry(ROOT))

    static = loader.load_static()

    assert set(static) == {"indicator_registry", "methodology_registry"}
    assert static["indicator_registry"].state is ArtifactState.FOUND
    assert static["indicator_registry"].path.name == "indicator_registry.json"


def test_parsed_indicator_registry_returns_nine_validated_indicators():
    loader = ScientificInfrastructureLoader(build_default_registry(ROOT))

    registry = loader.parsed_indicator_registry()

    assert registry is not None
    assert registry.version == "1.0.0"
    assert len(registry.indicators) == 9
    assert "audiovisual_archive_access_index" in registry.indicator_ids
    assert "interoperability_index" in registry.indicator_ids


def test_invalid_indicator_registry_is_rejected(tmp_path):
    target = tmp_path / "data/templates/analytics"
    target.mkdir(parents=True)
    (target / "indicator_registry.json").write_text(
        json.dumps({"registry": {}, "indicators": []}),
        encoding="utf-8",
    )

    loader = ScientificInfrastructureLoader(build_default_registry(tmp_path))
    artifact = loader.load_indicator_registry()

    assert artifact.state is ArtifactState.INVALID
    assert artifact.error
    assert loader.parsed_indicator_registry() is None


def test_legacy_catalog_does_not_restore_operational_fallback(tmp_path):
    target = tmp_path / "data/templates/analytics"
    target.mkdir(parents=True)
    (target / "indicator_catalog.json").write_text(
        json.dumps({"catalog_version": "legacy", "indicators": []}),
        encoding="utf-8",
    )

    loader = ScientificInfrastructureLoader(build_default_registry(tmp_path))
    artifact = loader.load_indicator_registry()

    assert artifact.state is ArtifactState.MISSING
    assert artifact.path.name == "indicator_registry.json"
