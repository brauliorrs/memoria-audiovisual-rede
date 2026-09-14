"""Feature flags seguras para a camada experimental de IA."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from .ai_contracts import AIExperimentTask, AI_EXPERIMENT_TASKS

MASTER_FLAG = "MAR_AI_EXPERIMENTS_ENABLED"
SHADOW_FLAG = "MAR_AI_SHADOW_MODE"

TASK_ENV_FLAGS: dict[AIExperimentTask, str] = {
    "institutional_ai_use": "MAR_AI_INSTITUTIONAL_USE_ENABLED",
    "audiovisual_collection_detection": "MAR_AI_COLLECTION_DETECTION_ENABLED",
    "public_video_presence_detection": "MAR_AI_VIDEO_PRESENCE_ENABLED",
    "ai_content_production_detection": "MAR_AI_CONTENT_PRODUCTION_ENABLED",
    "synthetic_video_detection": "MAR_AI_SYNTHETIC_VIDEO_ENABLED",
}

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off", ""}


def parse_bool(value: str | bool | None, *, default: bool = False, name: str = "flag") -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"{name} deve usar true/false, 1/0, yes/no ou on/off")


@dataclass(frozen=True, slots=True)
class AIExperimentFlags:
    """Configuração imutável. Todas as tarefas ficam desligadas por padrão."""

    experiments_enabled: bool = False
    shadow_mode: bool = True
    institutional_ai_use: bool = False
    audiovisual_collection_detection: bool = False
    public_video_presence_detection: bool = False
    ai_content_production_detection: bool = False
    synthetic_video_detection: bool = False

    def __post_init__(self) -> None:
        if self.experiments_enabled and not self.shadow_mode:
            raise ValueError("a camada experimental só pode executar em modo sombra no T0A")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "AIExperimentFlags":
        values = os.environ if env is None else env
        kwargs = {
            "experiments_enabled": parse_bool(
                values.get(MASTER_FLAG), default=False, name=MASTER_FLAG
            ),
            "shadow_mode": parse_bool(
                values.get(SHADOW_FLAG), default=True, name=SHADOW_FLAG
            ),
        }
        for task, env_name in TASK_ENV_FLAGS.items():
            kwargs[task] = parse_bool(values.get(env_name), default=False, name=env_name)
        return cls(**kwargs)

    def is_enabled(self, task: AIExperimentTask) -> bool:
        if task not in AI_EXPERIMENT_TASKS:
            raise ValueError(f"task inválida: {task}")
        return self.experiments_enabled and bool(getattr(self, task))

    @property
    def enabled_tasks(self) -> tuple[AIExperimentTask, ...]:
        return tuple(task for task in AI_EXPERIMENT_TASKS if self.is_enabled(task))

    def to_dict(self) -> dict[str, bool]:
        return {
            "experiments_enabled": self.experiments_enabled,
            "shadow_mode": self.shadow_mode,
            **{task: bool(getattr(self, task)) for task in AI_EXPERIMENT_TASKS},
        }
