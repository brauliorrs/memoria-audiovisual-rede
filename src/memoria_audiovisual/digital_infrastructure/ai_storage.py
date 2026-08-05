"""Persistência separada e append-only para experimentos de IA."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .ai_contracts import (
    AIExperimentDimension,
    AIExperimentRecord,
    AIExperimentRunManifest,
    AIExperimentTask,
    TASK_DIMENSIONS,
)
from .persistence import JsonlRepository

RUN_COLLECTION = "ai_experiment_runs"
REVIEW_COLLECTION = "ai_human_reviews"

DIMENSION_COLLECTIONS: dict[AIExperimentDimension, str] = {
    "institutional_ai_use": "ai_institutional_use",
    "observatory_ai_triage": "ai_observatory_triage",
    "synthetic_audiovisual_content": "ai_synthetic_audiovisual_content",
}


class AIExperimentStore:
    """Armazena IA fora dos registros usados pelo baseline oficial."""

    def __init__(self, root: str | Path) -> None:
        self.repository = JsonlRepository(root)

    @staticmethod
    def collection_for_task(task: AIExperimentTask) -> str:
        try:
            dimension = TASK_DIMENSIONS[task]
        except KeyError as exc:
            raise ValueError(f"task inválida: {task}") from exc
        return DIMENSION_COLLECTIONS[dimension]

    def append_record(self, record: AIExperimentRecord) -> Path:
        return self.repository.append(
            self.collection_for_task(record.task),
            record.to_dict(),
        )

    def append_run_manifest(self, manifest: AIExperimentRunManifest) -> Path:
        return self.repository.append(RUN_COLLECTION, manifest.to_dict())

    def append_human_review(self, review: dict[str, Any]) -> Path:
        required = {"experiment_id", "record_version_id", "review_status", "reviewed_at"}
        missing = required - set(review)
        if missing:
            raise ValueError(f"revisão sem campos obrigatórios: {sorted(missing)}")
        return self.repository.append(REVIEW_COLLECTION, review)

    def read_records(self, task: AIExperimentTask | None = None) -> list[dict[str, Any]]:
        if task is not None:
            return self.repository.read_all(self.collection_for_task(task))
        records: list[dict[str, Any]] = []
        for collection in DIMENSION_COLLECTIONS.values():
            records.extend(self.repository.read_all(collection))
        return records

    def read_run_manifests(self) -> list[dict[str, Any]]:
        return self.repository.read_all(RUN_COLLECTION)

    def latest_records(self, task: AIExperimentTask | None = None) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for record in self.read_records(task):
            experiment_id = record.get("experiment_id")
            if experiment_id is not None:
                latest[str(experiment_id)] = record
        return latest
