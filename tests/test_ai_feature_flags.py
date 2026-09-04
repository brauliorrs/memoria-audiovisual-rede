import pytest

from memoria_audiovisual.digital_infrastructure.ai_flags import AIExperimentFlags


def test_ai_flags_are_off_by_default():
    flags = AIExperimentFlags.from_env({})
    assert flags.enabled_tasks == ()
    assert flags.shadow_mode is True


def test_master_and_task_flags_are_both_required():
    task_only = AIExperimentFlags.from_env(
        {"MAR_AI_INSTITUTIONAL_USE_ENABLED": "true"}
    )
    assert task_only.enabled_tasks == ()

    enabled = AIExperimentFlags.from_env(
        {
            "MAR_AI_EXPERIMENTS_ENABLED": "true",
            "MAR_AI_INSTITUTIONAL_USE_ENABLED": "true",
            "MAR_AI_COLLECTION_DETECTION_ENABLED": "1",
        }
    )
    assert enabled.enabled_tasks == (
        "institutional_ai_use",
        "audiovisual_collection_detection",
    )


def test_non_shadow_execution_is_blocked():
    with pytest.raises(ValueError, match="modo sombra"):
        AIExperimentFlags.from_env(
            {
                "MAR_AI_EXPERIMENTS_ENABLED": "true",
                "MAR_AI_SHADOW_MODE": "false",
            }
        )


def test_invalid_boolean_is_rejected():
    with pytest.raises(ValueError, match="MAR_AI_EXPERIMENTS_ENABLED"):
        AIExperimentFlags.from_env({"MAR_AI_EXPERIMENTS_ENABLED": "perhaps"})
