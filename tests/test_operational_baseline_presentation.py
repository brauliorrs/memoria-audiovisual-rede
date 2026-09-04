from pathlib import Path

from memoria_audiovisual.scientific_infrastructure import ArtifactState, LoadedArtifact
from memoria_audiovisual.ui.operational_baseline import (
    build_operational_baseline_view_model,
)


def artifact(
    key: str,
    *,
    state: ArtifactState = ArtifactState.FOUND,
    payload=None,
    error: str = "",
) -> LoadedArtifact:
    return LoadedArtifact(
        key=key,
        name=key,
        path=Path(f"/{key}.json"),
        state=state,
        payload=payload,
        error=error,
    )


def test_missing_operational_pointer_is_pending_not_negative_result():
    view = build_operational_baseline_view_model(
        {
            "pointer": artifact(
                "pointer",
                state=ArtifactState.MISSING,
            )
        },
        language="pt",
    )

    assert view["state"] == "pending"
    assert "não constitui resultado empírico negativo" in view["message"]


def test_completed_operational_baseline_exposes_counts_and_results():
    view = build_operational_baseline_view_model(
        {
            "pointer": artifact(
                "pointer",
                payload={
                    "snapshot_id": "operational-baseline-v1-123",
                    "manifest_path": "data/output/analytics/snapshot/operational_baseline_manifest.json",
                    "manifest_sha256": "abc123",
                },
            ),
            "snapshot": artifact(
                "snapshot",
                payload={"snapshot_id": "operational-baseline-v1-123"},
            ),
            "operational_manifest": artifact(
                "operational_manifest",
                payload={
                    "status": "completed",
                    "official_baseline": True,
                    "pipeline_commit": "deadbeef",
                    "generated_at": "2026-08-05T00:00:00Z",
                    "counts": {
                        "active_corpora": 55,
                        "indicators": 9,
                        "non_successful_t1_corpora": 6,
                    },
                    "ai": {"is_official_baseline_dependency": False},
                },
            ),
            "indicators": artifact(
                "indicators",
                payload={
                    "results": [
                        {
                            "indicator_id": "interoperability",
                            "indicator_version": "1.0.0",
                            "status": "completed",
                            "value": 42,
                        }
                    ]
                },
            ),
        },
        language="en",
    )

    assert view["state"] == "completed"
    assert view["active_corpora"] == 55
    assert view["indicator_count"] == 9
    assert view["t1_occurrences"] == 6
    assert view["manifest_sha256"] == "abc123"
    assert view["results"][0]["indicator_id"] == "interoperability"
    assert view["ai_independent"] is True


def test_ai_dependent_manifest_is_not_presented_as_official():
    view = build_operational_baseline_view_model(
        {
            "pointer": artifact("pointer", payload={"snapshot_id": "snapshot"}),
            "snapshot": artifact("snapshot", payload={"snapshot_id": "snapshot"}),
            "operational_manifest": artifact(
                "operational_manifest",
                payload={
                    "status": "completed",
                    "official_baseline": True,
                    "ai": {"is_official_baseline_dependency": True},
                },
            ),
        },
        language="es",
    )

    assert view["state"] == "invalid"
