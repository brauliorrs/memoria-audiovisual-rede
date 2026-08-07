from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.scientific_infrastructure.reference_corpus_inventory import (
    assert_reference_corpus_inventory,
    audit_reference_corpus_inventory,
    build_reference_corpus_inventory,
)

ROOT = Path(__file__).resolve().parents[1]


def test_reference_corpus_inventory_matches_canonical_source():
    report = audit_reference_corpus_inventory(ROOT)
    assert report.is_valid
    assert report.total_entities == 58
    assert report.active_entities == 55
    assert report.inventory["distributions"]["category_code"] == {
        "aggregator": 7,
        "institution": 51,
    }
    assert report.inventory["field_completeness"]["complete_entities"] == 58
    assert_reference_corpus_inventory(report)


def test_inventory_is_deterministic_and_non_authoritative():
    manifest = json.loads(
        (ROOT / "data/reference_corpus/manifest.json").read_text(encoding="utf-8")
    )
    first = build_reference_corpus_inventory(CORPORA, manifest)
    second = build_reference_corpus_inventory(CORPORA, manifest)
    assert first == second
    assert first["governance"]["regenerable"] is True
    assert first["governance"]["authoritative_for_corpus_membership"] is False


def test_stale_inventory_is_blocking(tmp_path: Path):
    for relative in (
        "data/reference_corpus/manifest.json",
        "data/reference_corpus/inventory.json",
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    inventory_path = tmp_path / "data/reference_corpus/inventory.json"
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    payload["summary"]["active_entities"] = 0
    inventory_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = audit_reference_corpus_inventory(tmp_path)
    assert not report.is_valid
    with pytest.raises(ValueError, match="regenere o inventário"):
        assert_reference_corpus_inventory(report)
