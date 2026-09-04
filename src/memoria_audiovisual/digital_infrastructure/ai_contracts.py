"""Contratos versionados para experimentos de IA em modo sombra."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .ids import stable_id, version_id
from .models import utc_now_iso

AI_SCHEMA_VERSION = "1.1.0"

AIExperimentDimension = Literal[
    "institutional_ai_use",
    "observatory_ai_triage",
    "ai_audiovisual_content_production",
    "synthetic_audiovisual_content",
]

AIExperimentTask = Literal[
    "institutional_ai_use",
    "audiovisual_collection_detection",
    "public_video_presence_detection",
    "ai_content_production_detection",
    "synthetic_video_detection",
]

AIExperimentStatus = Literal[
    "not_executed",
    "experimental",
    "detected_pending_review",
    "verified_public_evidence",
    "ambiguous",
    "not_identified_on_assessed_surfaces",
    "not_assessable",
    "error",
    "withdrawn_or_corrected",
]

HumanReviewStatus = Literal[
    "not_requested",
    "pending",
    "confirmed",
    "corrected",
    "rejected",
]

EvidenceType = Literal[
    "textual",
    "structural",
    "metadata",
    "documentary",
    "visual",
    "audio",
    "deterministic",
]

TASK_DIMENSIONS: dict[AIExperimentTask, AIExperimentDimension] = {
    "institutional_ai_use": "institutional_ai_use",
    "audiovisual_collection_detection": "observatory_ai_triage",
    "public_video_presence_detection": "observatory_ai_triage",
    "ai_content_production_detection": "ai_audiovisual_content_production",
    "synthetic_video_detection": "synthetic_audiovisual_content",
}
AI_EXPERIMENT_TASKS: tuple[AIExperimentTask, ...] = tuple(TASK_DIMENSIONS)
ITEM_LEVEL_AI_TASKS = {
    "ai_content_production_detection",
    "synthetic_video_detection",
}

VALID_STATUSES = {
    "not_executed",
    "experimental",
    "detected_pending_review",
    "verified_public_evidence",
    "ambiguous",
    "not_identified_on_assessed_surfaces",
    "not_assessable",
    "error",
    "withdrawn_or_corrected",
}
VALID_REVIEW_STATUSES = {"not_requested", "pending", "confirmed", "corrected", "rejected"}


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} é obrigatório")


@dataclass(frozen=True, slots=True)
class AIModelDescriptor:
    """Identifica de forma reprodutível o modelo ou classificador executado."""

    provider: str
    model_name: str
    model_version: str
    configuration: dict[str, Any] = field(default_factory=dict)
    prompt_version: str | None = None
    classifier_version: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.provider, "provider")
        _require_text(self.model_name, "model_name")
        _require_text(self.model_version, "model_version")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AIEvidenceReference:
    """Referência mínima à evidência reutilizável que sustentou uma previsão."""

    evidence_id: str
    evidence_type: EvidenceType
    source_url: str | None = None
    artifact_id: str | None = None
    excerpt: str | None = None
    language: str | None = None
    observed_at: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        if self.source_url is None and self.artifact_id is None:
            raise ValueError("source_url ou artifact_id é obrigatório para a evidência")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AIExperimentRecord:
    """Resultado imutável de uma tarefa experimental de IA.

    O registro nunca representa, por si só, um resultado científico publicado.
    """

    run_id: str
    entity_id: str
    task: AIExperimentTask
    status: AIExperimentStatus
    prediction: str | None = None
    confidence: float | None = None
    observation_id: str | None = None
    item_id: str | None = None
    item_version_id: str | None = None
    segment_id: str | None = None
    language: str | None = None
    evidence: tuple[AIEvidenceReference, ...] = ()
    model: AIModelDescriptor | None = None
    attempt: int = 1
    duration_ms: int | None = None
    estimated_cost_usd: float | None = None
    error_code: str | None = None
    error_message: str | None = None
    human_review_status: HumanReviewStatus = "not_requested"
    human_decision: str | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    notes: str | None = None
    recorded_at: str = field(default_factory=utc_now_iso)
    schema_version: str = AI_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_text(self.entity_id, "entity_id")
        if self.task not in TASK_DIMENSIONS:
            raise ValueError(f"task inválida: {self.task}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status inválido: {self.status}")
        if self.human_review_status not in VALID_REVIEW_STATUSES:
            raise ValueError(f"human_review_status inválido: {self.human_review_status}")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence deve estar entre 0 e 1")
        if self.attempt < 1:
            raise ValueError("attempt deve ser maior ou igual a 1")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("duration_ms não pode ser negativo")
        if self.estimated_cost_usd is not None and self.estimated_cost_usd < 0:
            raise ValueError("estimated_cost_usd não pode ser negativo")
        if self.task in ITEM_LEVEL_AI_TASKS and not any(
            (self.item_id, self.item_version_id, self.segment_id)
        ):
            raise ValueError(
                f"{self.task} exige item_id, item_version_id ou segment_id"
            )
        if self.status == "error" and not (self.error_code or self.error_message):
            raise ValueError("registros com status error exigem error_code ou error_message")
        if self.human_review_status in {"confirmed", "corrected", "rejected"} and not self.reviewed_at:
            raise ValueError("revisão concluída exige reviewed_at")

    @property
    def dimension(self) -> AIExperimentDimension:
        return TASK_DIMENSIONS[self.task]

    @property
    def experiment_id(self) -> str:
        target = self.segment_id or self.item_version_id or self.item_id or self.observation_id or "entity"
        natural_key = f"{self.run_id}:{self.entity_id}:{self.task}:{target}:{self.attempt}"
        return stable_id("ai-experiment", natural_key)

    @property
    def record_version_id(self) -> str:
        return version_id(self.experiment_id, self._version_payload())

    def _version_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "entity_id": self.entity_id,
            "task": self.task,
            "status": self.status,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "observation_id": self.observation_id,
            "item_id": self.item_id,
            "item_version_id": self.item_version_id,
            "segment_id": self.segment_id,
            "language": self.language,
            "evidence": [item.to_dict() for item in self.evidence],
            "model": self.model.to_dict() if self.model else None,
            "attempt": self.attempt,
            "human_review_status": self.human_review_status,
            "human_decision": self.human_decision,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["dimension"] = self.dimension
        data["experiment_id"] = self.experiment_id
        data["record_version_id"] = self.record_version_id
        data["evidence"] = [item.to_dict() for item in self.evidence]
        data["model"] = self.model.to_dict() if self.model else None
        return data


@dataclass(frozen=True, slots=True)
class AIExperimentRunManifest:
    """Manifesto de uma execução experimental desacoplada do baseline oficial."""

    run_id: str
    official_cycle_id: str | None
    corpus_version: str
    enabled_tasks: tuple[AIExperimentTask, ...]
    shadow_mode: bool = True
    baseline_dependency: bool = False
    status: Literal["planned", "running", "completed", "partial", "failed"] = "planned"
    feature_flags: dict[str, bool] = field(default_factory=dict)
    code_commit_sha: str | None = None
    started_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None
    notes: str | None = None
    schema_version: str = AI_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_text(self.corpus_version, "corpus_version")
        unknown = set(self.enabled_tasks) - set(AI_EXPERIMENT_TASKS)
        if unknown:
            raise ValueError(f"enabled_tasks contém tarefas inválidas: {sorted(unknown)}")
        if not self.shadow_mode:
            raise ValueError("T0A permite somente execuções em modo sombra")
        if self.baseline_dependency:
            raise ValueError("o baseline oficial não pode depender da IA experimental")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["enabled_tasks"] = list(self.enabled_tasks)
        return data
