from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_audiovisual.scientific_infrastructure.scientific_snapshot import (
    assert_scientific_snapshot,
    audit_scientific_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]


def test_initialized_snapshot_matches_scientific_context():
    report = audit_scientific_snapshot(ROOT)
    assert report.is_valid
    assert report.version == "1.0.0"
    assert report.status == "initialized"
    assert report.entity_count == 58
    assert_scientific_snapshot(report)


def test_initialized_snapshot_does_not_fabricate_execution_or_results():
    payload = json.loads(
        (ROOT / "data/reference_corpus/snapshots/snapshot_v1.0.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["execution"]["status"] == "not_executed"
    assert payload["execution"]["started_at"] is None
    assert payload["execution"]["finished_at"] is None
    assert payload["materialization"]["coverage_snapshot_available"] is False
    assert payload["materialization"]["indicator_results_available"] is False
    assert payload["materialization"]["provenance_available"] is False
    assert payload["materialization"]["absence_reason"]


def test_snapshot_hash_divergence_is_blocking(tmp_path: Path):
    for relative in (
        "data/reference_corpus/manifest.json",
        "data/reference_corpus/snapshots/snapshot_v1.0.json",
        "data/templates/analytics/indicator_registry.json",
        "data/templates/analytics/methodology_registry.json",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    snapshot_path = tmp_path / "data/reference_corpus/snapshots/snapshot_v1.0.json"
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    payload["reference_corpus"]["source_content_hash"] = "0" * 40
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = audit_scientific_snapshot(tmp_path)
    assert not report.is_valid
    with pytest.raises(ValueError, match="source_content_hash"):
        assert_scientific_snapshot(report)
