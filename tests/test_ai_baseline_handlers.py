from memoria_audiovisual.digital_infrastructure.ai_baseline_handlers import (
    build_entity_baseline_handlers,
)
from memoria_audiovisual.digital_infrastructure.ai_flags import AIExperimentFlags
from memoria_audiovisual.digital_infrastructure.ai_runtime import (
    AIExperimentContext,
    AIShadowRunner,
)
from memoria_audiovisual.digital_infrastructure.ai_storage import AIExperimentStore


def test_deterministic_baselines_collect_reviewable_signals(tmp_path):
    output_file = tmp_path / "sample.json"
    output_file.write_text(
        '{"description":"Artificial intelligence transcription",'
        '"video":"https://example.org/item.mp4",'
        '"collection":"audiovisual collection"}',
        encoding="utf-8",
    )
    corpus = {
        "code": "example",
        "source_url": "https://example.org",
        "output_files": {"sample": output_file.name},
    }
    snapshot = {
        "observation_key": "obs-1",
        "counts": {"video_links_total": 1, "videos_in_curatorial_catalog": 1},
    }
    handlers = build_entity_baseline_handlers(
        corpus_definition=corpus,
        snapshot_metadata=snapshot,
        output_dir=tmp_path,
    )
    flags = AIExperimentFlags(
        experiments_enabled=True,
        institutional_ai_use=True,
        audiovisual_collection_detection=True,
        public_video_presence_detection=True,
    )
    records = AIShadowRunner(
        flags=flags,
        store=AIExperimentStore(tmp_path / "ai"),
        handlers=handlers,
    ).run(
        AIExperimentContext(
            run_id="run-1",
            entity_id="example",
            observation_id="obs-1",
        )
    )

    assert [record.status for record in records] == [
        "detected_pending_review",
        "detected_pending_review",
        "detected_pending_review",
    ]
    assert all(record.model.model_name == "deterministic-evidence-baseline" for record in records)
    assert all(record.human_review_status == "pending" for record in records)


def test_corpus_policy_text_is_not_used_as_observed_evidence(tmp_path):
    handlers = build_entity_baseline_handlers(
        corpus_definition={
            "code": "example",
            "audiovisual_scope_note": "acervo audiovisual com vídeo",
            "output_files": {},
        },
        snapshot_metadata={"counts": {}},
        output_dir=tmp_path,
    )
    flags = AIExperimentFlags(
        experiments_enabled=True,
        audiovisual_collection_detection=True,
        public_video_presence_detection=True,
    )
    records = AIShadowRunner(
        flags=flags,
        store=AIExperimentStore(tmp_path / "ai"),
        handlers=handlers,
    ).run(AIExperimentContext(run_id="run-1", entity_id="example"))

    assert [record.status for record in records] == [
        "not_identified_on_assessed_surfaces",
        "not_identified_on_assessed_surfaces",
    ]
