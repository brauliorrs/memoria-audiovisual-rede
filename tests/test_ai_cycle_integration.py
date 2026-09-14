from memoria_audiovisual.digital_infrastructure.ai_cycle import (
    collect_entity_shadow_signals,
)
from memoria_audiovisual.digital_infrastructure.ai_flags import AIExperimentFlags
from memoria_audiovisual.digital_infrastructure.ai_storage import AIExperimentStore


def test_disabled_shadow_collection_is_a_noop(tmp_path):
    report = collect_entity_shadow_signals(
        run_id="run-1",
        corpus_definition={"code": "ina"},
        snapshot_metadata={},
        output_dir=tmp_path,
        flags=AIExperimentFlags(),
        store=AIExperimentStore(tmp_path / "ai"),
    )
    assert report.successful
    assert report.records == ()
    assert not (tmp_path / "ai").exists() or list((tmp_path / "ai").iterdir()) == []


def test_storage_failure_is_isolated_from_official_cycle(tmp_path):
    class BrokenStore:
        def append_record(self, _record):
            raise OSError("read-only storage")

    flags = AIExperimentFlags(
        experiments_enabled=True,
        audiovisual_collection_detection=True,
    )
    report = collect_entity_shadow_signals(
        run_id="run-1",
        corpus_definition={"code": "ina", "output_files": {}},
        snapshot_metadata={"observation_key": "obs-1", "counts": {}},
        output_dir=tmp_path,
        flags=flags,
        store=BrokenStore(),
    )
    assert not report.successful
    assert "read-only storage" in report.error
