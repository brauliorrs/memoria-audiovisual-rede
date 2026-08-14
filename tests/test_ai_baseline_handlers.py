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


def test_nfsa_external_positive_control_detects_explicit_institutional_ai(tmp_path):
    output_file = tmp_path / "nfsa_positive_control.json"
    output_file.write_text(
        '{"evidence":"NFSA declares Bowerbird a machine learning-enabled audio and video '
        'transcription engine applied to audiovisual collection material."}',
        encoding="utf-8",
    )
    handlers = build_entity_baseline_handlers(
        corpus_definition={
            "code": "nfsa_external_control",
            "source_url": "https://www.nfsa.gov.au/stories/articles/bowerbird",
            "output_files": {"evidence": output_file.name},
        },
        snapshot_metadata={"observation_key": "nfsa-control-v1", "counts": {}},
        output_dir=tmp_path,
    )

    record = handlers["institutional_ai_use"](
        AIExperimentContext(
            run_id="t2a-external-control-v1",
            entity_id="nfsa_external_control",
            observation_id="nfsa-control-v1",
            language="en",
        )
    )

    assert record.status == "detected_pending_review"
    assert record.prediction == "public_institutional_ai_signal"
    assert record.human_review_status == "pending"
    assert record.evidence
    assert "machine learning" in (record.evidence[0].excerpt or "")
