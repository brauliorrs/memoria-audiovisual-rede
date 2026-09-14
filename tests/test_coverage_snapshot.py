from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure.parameter_coverage import (
    EXPECTED_DETECTOR_GROUPS,
)
from memoria_audiovisual.scientific_infrastructure.coverage_snapshot import (
    build_coverage_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]


def _rows(snapshot_id: str):
    return [
        {
            "corpus_code": corpus_code,
            "snapshot_id": snapshot_id,
            "detector_group": group,
            "status": "not_detected",
            "observation_count": 1,
            "detected_values": [],
        }
        for corpus_code in CORPORA
        for group in EXPECTED_DETECTOR_GROUPS
    ]


def test_builds_complete_coverage_snapshot():
    snapshot_id = "scientific-coverage-v1-test"
    manifest = json.loads(
        (ROOT / "data/reference_corpus/manifest.json").read_text(encoding="utf-8")
    )
    payload = build_coverage_snapshot(
        coverage_rows=_rows(snapshot_id),
        source_snapshot_id=snapshot_id,
        started_at="2026-08-04T18:00:00Z",
        finished_at="2026-08-04T18:01:00Z",
        duration_seconds=60,
        pipeline_commit="a" * 40,
        manifest=manifest,
    )
    assert payload["summary"]["corpus_count"] == 58
    assert payload["summary"]["detector_group_count"] == 7
    assert payload["summary"]["parameter_count"] == 406
    assert payload["governance"]["unknown_is_not_negative"] is True


def test_rejects_incomplete_matrix():
    snapshot_id = "scientific-coverage-v1-test"
    manifest = json.loads(
        (ROOT / "data/reference_corpus/manifest.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ValueError, match="matriz incompleta"):
        build_coverage_snapshot(
            coverage_rows=_rows(snapshot_id)[:-1],
            source_snapshot_id=snapshot_id,
            started_at="2026-08-04T18:00:00Z",
            finished_at="2026-08-04T18:01:00Z",
            duration_seconds=60,
            pipeline_commit="a" * 40,
            manifest=manifest,
        )


def test_rejects_duplicate_pair():
    snapshot_id = "scientific-coverage-v1-test"
    manifest = json.loads(
        (ROOT / "data/reference_corpus/manifest.json").read_text(encoding="utf-8")
    )
    rows = _rows(snapshot_id)
    rows.append(dict(rows[0]))
    with pytest.raises(ValueError, match="cobertura duplicada"):
        build_coverage_snapshot(
            coverage_rows=rows,
            source_snapshot_id=snapshot_id,
            started_at="2026-08-04T18:00:00Z",
            finished_at="2026-08-04T18:01:00Z",
            duration_seconds=60,
            pipeline_commit="a" * 40,
            manifest=manifest,
        )
