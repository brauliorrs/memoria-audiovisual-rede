from memoria_audiovisual.digital_infrastructure.ai_contracts import (
    AIExperimentRecord,
)
from memoria_audiovisual.digital_infrastructure.ai_flags import AIExperimentFlags
from memoria_audiovisual.digital_infrastructure.ai_runtime import (
    AIExperimentContext,
    AIShadowRunner,
)
from memoria_audiovisual.digital_infrastructure.ai_storage import AIExperimentStore


def test_shadow_runner_separates_collections_and_is_fail_open(tmp_path):
    flags = AIExperimentFlags(
        experiments_enabled=True,
        institutional_ai_use=True,
        audiovisual_collection_detection=True,
    )
    store = AIExperimentStore(tmp_path)

    def institutional_handler(context):
        return AIExperimentRecord(
            run_id=context.run_id,
            entity_id=context.entity_id,
            task="institutional_ai_use",
            status="experimental",
            prediction="declared_tool_use",
        )

    def broken_handler(_context):
        raise RuntimeError("provider unavailable")

    runner = AIShadowRunner(
        flags=flags,
        store=store,
        handlers={
            "institutional_ai_use": institutional_handler,
            "audiovisual_collection_detection": broken_handler,
        },
    )
    records = runner.run(AIExperimentContext(run_id="run-1", entity_id="ina"))

    assert [record.status for record in records] == ["experimental", "error"]
    assert (tmp_path / "ai_institutional_use.jsonl").exists()
    assert (tmp_path / "ai_observatory_triage.jsonl").exists()
    assert store.read_records("institutional_ai_use")[0]["prediction"] == "declared_tool_use"
    assert store.read_records("audiovisual_collection_detection")[0]["error_code"] == "RuntimeError"


def test_disabled_tasks_are_not_executed_or_persisted(tmp_path):
    called = False

    def handler(_context):
        nonlocal called
        called = True
        raise AssertionError("should not run")

    runner = AIShadowRunner(
        flags=AIExperimentFlags(),
        store=AIExperimentStore(tmp_path),
        handlers={"institutional_ai_use": handler},
    )
    assert runner.run(AIExperimentContext(run_id="run-1", entity_id="ina")) == ()
    assert called is False
    assert list(tmp_path.iterdir()) == []


def test_item_level_task_is_skipped_for_entity_context(tmp_path):
    flags = AIExperimentFlags(
        experiments_enabled=True,
        synthetic_video_detection=True,
    )
    runner = AIShadowRunner(
        flags=flags,
        store=AIExperimentStore(tmp_path),
    )
    assert runner.run(AIExperimentContext(run_id="run-1", entity_id="ina")) == ()
