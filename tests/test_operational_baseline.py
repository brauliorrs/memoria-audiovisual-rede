import hashlib
import json
from pathlib import Path

import pytest

from scripts.materialize_operational_baseline import materialize


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_fixture(tmp_path: Path, snapshot_id: str = "operational-test") -> dict[str, Path]:
    t1_gate = tmp_path / "t1.json"
    write_json(
        t1_gate,
        {
            "gate": "t1_auditable_completion",
            "auditable_completion": True,
            "active_corpora_total": 2,
            "recorded_results_total": 2,
            "successful_corpora_total": 1,
            "non_successful_corpora_total": 1,
            "source_run_id": "123",
            "source_manifest_sha256": "abc",
        },
    )

    coverage_path = tmp_path / "coverage" / "parameter_coverage.json"
    write_json(coverage_path, [{"snapshot_id": snapshot_id}])
    audit_summary = tmp_path / "audit.json"
    write_json(
        audit_summary,
        {
            "mode": "ledger",
            "snapshot_id": snapshot_id,
            "source_count": 2,
            "batches": [{"batch_id": "b1"}, {"batch_id": "b2"}],
            "coverage": {"corpus_count": 2, "parameter_count": 14},
            "coverage_manifest": {"coverage_path": str(coverage_path)},
        },
    )

    analytics_root = tmp_path / "analytics"
    snapshot_root = analytics_root / snapshot_id
    result = {
        "snapshot_id": snapshot_id,
        "indicator_id": "indicator.test",
        "indicator_version": "1.0.0",
        "methodology_version": "1.0.0",
        "value": 1,
    }
    indicators = {
        "snapshot_id": snapshot_id,
        "methodology_version": "1.0.0",
        "status": "completed",
        "indicator_count": 1,
        "results": [result],
    }
    indicators_path = snapshot_root / "snapshot_indicators.json"
    write_json(indicators_path, indicators)
    write_json(
        snapshot_root / "manifest.json",
        {
            "snapshot_id": snapshot_id,
            "methodology_version": "1.0.0",
            "indicators_path": str(indicators_path),
            "indicators_sha256": canonical_digest(indicators),
            "indicator_count": 1,
            "result_keys": [f"{snapshot_id}|indicator.test|1.0.0|1.0.0"],
            "generated_at": "2026-08-05T00:00:00Z",
        },
    )
    write_json(
        snapshot_root / "run.json",
        {"snapshot_id": snapshot_id, "status": "completed", "indicator_count": 1},
    )
    write_json(snapshot_root / "interoperability_sensitivity.json", {"status": "completed"})
    (analytics_root / "indicator_history.jsonl").write_text(
        json.dumps(result, sort_keys=True) + "\n", encoding="utf-8"
    )

    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(
        "\n".join(
            json.dumps({"transaction_id": transaction_id, "records": [{"id": transaction_id}]})
            for transaction_id in ("t1", "t2")
        )
        + "\n",
        encoding="utf-8",
    )
    batches = tmp_path / "batches.jsonl"
    batches.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {"batch_id": "b1", "status": "running"},
                {"batch_id": "b1", "status": "completed"},
                {"batch_id": "b2", "status": "completed"},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "t1_gate": t1_gate,
        "audit_summary": audit_summary,
        "analytics_root": analytics_root,
        "ledger": ledger,
        "batches": batches,
        "output": tmp_path / "operational_manifest.json",
    }


def test_materializes_official_baseline_with_ai_disabled(tmp_path, monkeypatch):
    paths = build_fixture(tmp_path)
    for name in (
        "MAR_AI_EXPERIMENTS_ENABLED",
        "MAR_AI_INSTITUTIONAL_USE_ENABLED",
        "MAR_AI_COLLECTION_DETECTION_ENABLED",
        "MAR_AI_VIDEO_PRESENCE_ENABLED",
        "MAR_AI_SYNTHETIC_VIDEO_ENABLED",
    ):
        monkeypatch.setenv(name, "false")

    manifest = materialize(
        snapshot_id="operational-test",
        t1_gate_path=paths["t1_gate"],
        audit_summary_path=paths["audit_summary"],
        analytics_root=paths["analytics_root"],
        ledger_path=paths["ledger"],
        batch_manifest_path=paths["batches"],
        output_path=paths["output"],
        expected_corpora=2,
        expected_parameters=14,
        expected_indicators=1,
        pipeline_commit="deadbeef",
    )

    assert manifest["status"] == "completed"
    assert manifest["official_baseline"] is True
    assert manifest["ai"]["is_official_baseline_dependency"] is False
    assert manifest["counts"]["ingestion_batches"] == 2
    assert paths["output"].exists()


def test_rejects_official_baseline_when_experimental_ai_is_enabled(tmp_path, monkeypatch):
    paths = build_fixture(tmp_path)
    monkeypatch.setenv("MAR_AI_EXPERIMENTS_ENABLED", "true")

    with pytest.raises(ValueError, match="flags experimentais de IA desligadas"):
        materialize(
            snapshot_id="operational-test",
            t1_gate_path=paths["t1_gate"],
            audit_summary_path=paths["audit_summary"],
            analytics_root=paths["analytics_root"],
            ledger_path=paths["ledger"],
            batch_manifest_path=paths["batches"],
            output_path=paths["output"],
            expected_corpora=2,
            expected_parameters=14,
            expected_indicators=1,
            pipeline_commit="deadbeef",
        )


def test_rejects_baseline_when_t1_does_not_record_full_denominator(tmp_path, monkeypatch):
    paths = build_fixture(tmp_path)
    gate = json.loads(paths["t1_gate"].read_text(encoding="utf-8"))
    gate["recorded_results_total"] = 1
    write_json(paths["t1_gate"], gate)
    monkeypatch.setenv("MAR_AI_EXPERIMENTS_ENABLED", "false")

    with pytest.raises(ValueError, match="T1 não registra resultado para todos"):
        materialize(
            snapshot_id="operational-test",
            t1_gate_path=paths["t1_gate"],
            audit_summary_path=paths["audit_summary"],
            analytics_root=paths["analytics_root"],
            ledger_path=paths["ledger"],
            batch_manifest_path=paths["batches"],
            output_path=paths["output"],
            expected_corpora=2,
            expected_parameters=14,
            expected_indicators=1,
            pipeline_commit="deadbeef",
        )
