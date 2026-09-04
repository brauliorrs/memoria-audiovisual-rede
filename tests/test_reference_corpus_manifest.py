from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_audiovisual.scientific_infrastructure.reference_corpus_manifest import (
    assert_reference_corpus_manifest,
    audit_reference_corpus_manifest,
)

ROOT = Path(__file__).resolve().parents[1]


def test_reference_corpus_manifest_matches_canonical_source():
    report = audit_reference_corpus_manifest(ROOT)
    assert report.is_valid
    assert report.version == "1.0.0"
    assert report.dataset_path == "src/memoria_audiovisual/corpora.py"
    assert report.entity_count == 58
    assert report.content_hash == "64a8c8937131182ddbdf82df4e49ff9b3d8a4657"
    assert_reference_corpus_manifest(report)


def test_reference_corpus_is_not_duplicated():
    forbidden = ROOT / "data/reference_corpus/corpus_reference_v1.0.json"
    assert not forbidden.exists()


def test_hash_divergence_is_blocking(tmp_path: Path):
    source_manifest = ROOT / "data/reference_corpus/manifest.json"
    target_manifest = tmp_path / "data/reference_corpus/manifest.json"
    target_manifest.parent.mkdir(parents=True)
    payload = json.loads(source_manifest.read_text(encoding="utf-8"))
    payload["dataset"]["content_hash"] = "0" * 40
    target_manifest.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    source_dataset = ROOT / "src/memoria_audiovisual/corpora.py"
    target_dataset = tmp_path / "src/memoria_audiovisual/corpora.py"
    target_dataset.parent.mkdir(parents=True)
    target_dataset.write_text(source_dataset.read_text(encoding="utf-8"), encoding="utf-8")

    for relative in (
        "data/templates/analytics/indicator_registry.json",
        "data/templates/analytics/methodology_registry.json",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    report = audit_reference_corpus_manifest(tmp_path)
    assert not report.is_valid
    with pytest.raises(ValueError, match="dataset.content_hash"):
        assert_reference_corpus_manifest(report)
