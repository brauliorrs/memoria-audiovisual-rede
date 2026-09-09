"""Executor fail-open para tarefas experimentais de IA em modo sombra."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter

from .ai_contracts import (
    AIExperimentRecord,
    AIExperimentTask,
    AI_EXPERIMENT_TASKS,
    ITEM_LEVEL_AI_TASKS,
)
from .ai_flags import AIExperimentFlags
from .ai_storage import AIExperimentStore

AIExperimentHandler = Callable[["AIExperimentContext"], AIExperimentRecord]


@dataclass(frozen=True, slots=True)
class AIExperimentContext:
    """Contexto mínimo compartilhado com uma tarefa experimental."""

    run_id: str
    entity_id: str
    observation_id: str | None = None
    item_id: str | None = None
    item_version_id: str | None = None
    segment_id: str | None = None
    language: str | None = None
    source_urls: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()


class AIShadowRunner:
    """Executa somente tarefas habilitadas e nunca propaga falhas ao ciclo oficial."""

    def __init__(
        self,
        *,
        flags: AIExperimentFlags,
        store: AIExperimentStore,
        handlers: Mapping[AIExperimentTask, AIExperimentHandler] | None = None,
    ) -> None:
        self.flags = flags
        self.store = store
        self.handlers = dict(handlers or {})
        unknown = set(self.handlers) - set(AI_EXPERIMENT_TASKS)
        if unknown:
            raise ValueError(f"handlers contém tarefas inválidas: {sorted(unknown)}")

    def run(self, context: AIExperimentContext) -> tuple[AIExperimentRecord, ...]:
        records: list[AIExperimentRecord] = []
        for task in self.flags.enabled_tasks:
            if task in ITEM_LEVEL_AI_TASKS and not any(
                (context.item_id, context.item_version_id, context.segment_id)
            ):
                continue
            record = self._execute_task(task, context)
            self.store.append_record(record)
            records.append(record)
        return tuple(records)

    def _execute_task(
        self,
        task: AIExperimentTask,
        context: AIExperimentContext,
    ) -> AIExperimentRecord:
        handler = self.handlers.get(task)
        if handler is None:
            return self._not_executed(task, context, "handler_not_registered")

        started = perf_counter()
        try:
            record = handler(context)
            duration_ms = int((perf_counter() - started) * 1000)
            self._validate_handler_record(task, context, record)
            if record.duration_ms is None:
                record = self._with_duration(record, duration_ms)
            return record
        except Exception as exc:  # fail-open deliberado: a IA não bloqueia o baseline
            duration_ms = int((perf_counter() - started) * 1000)
            return AIExperimentRecord(
                run_id=context.run_id,
                entity_id=context.entity_id,
                task=task,
                status="error",
                observation_id=context.observation_id,
                item_id=context.item_id,
                item_version_id=context.item_version_id,
                segment_id=context.segment_id,
                language=context.language,
                duration_ms=duration_ms,
                error_code=type(exc).__name__,
                error_message=str(exc),
                notes="Falha experimental isolada do ciclo oficial.",
            )

    @staticmethod
    def _validate_handler_record(
        task: AIExperimentTask,
        context: AIExperimentContext,
        record: AIExperimentRecord,
    ) -> None:
        if record.task != task:
            raise ValueError("handler retornou uma tarefa diferente da registrada")
        if record.run_id != context.run_id:
            raise ValueError("handler retornou run_id incompatível")
        if record.entity_id != context.entity_id:
            raise ValueError("handler retornou entity_id incompatível")

    @staticmethod
    def _with_duration(record: AIExperimentRecord, duration_ms: int) -> AIExperimentRecord:
        data = {
            field_name: getattr(record, field_name)
            for field_name in record.__dataclass_fields__
        }
        data["duration_ms"] = duration_ms
        return AIExperimentRecord(**data)

    @staticmethod
    def _not_executed(
        task: AIExperimentTask,
        context: AIExperimentContext,
        reason: str,
    ) -> AIExperimentRecord:
        return AIExperimentRecord(
            run_id=context.run_id,
            entity_id=context.entity_id,
            task=task,
            status="not_executed",
            observation_id=context.observation_id,
            item_id=context.item_id,
            item_version_id=context.item_version_id,
            segment_id=context.segment_id,
            language=context.language,
            notes=reason,
        )
