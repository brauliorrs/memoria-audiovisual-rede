"""Integração fail-open da coleta experimental de IA com ciclos oficiais."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .ai_baseline_handlers import build_entity_baseline_handlers
from .ai_contracts import AIExperimentRecord
from .ai_flags import AIExperimentFlags
from .ai_runtime import AIExperimentContext, AIShadowRunner
from .ai_storage import AIExperimentStore


@dataclass(frozen=True, slots=True)
class AIShadowCollectionReport:
    entity_id: str
    records: tuple[AIExperimentRecord, ...] = ()
    error: str | None = None

    @property
    def successful(self) -> bool:
        return self.error is None


def collect_entity_shadow_signals(
    *,
    run_id: str,
    corpus_definition: Mapping[str, Any],
    snapshot_metadata: Mapping[str, Any],
    output_dir: str | Path,
    flags: AIExperimentFlags,
    store: AIExperimentStore,
) -> AIShadowCollectionReport:
    """Coleta sinais experimentais sem propagar falhas para o ciclo oficial."""

    entity_id = str(corpus_definition.get("code") or "").strip()
    if not entity_id:
        return AIShadowCollectionReport(
            entity_id="unknown",
            error="corpus_definition sem code",
        )
    if not flags.enabled_tasks:
        return AIShadowCollectionReport(entity_id=entity_id)

    observation_id = str(snapshot_metadata.get("observation_key") or "").strip() or None
    try:
        handlers = build_entity_baseline_handlers(
            corpus_definition=corpus_definition,
            snapshot_metadata=snapshot_metadata,
            output_dir=output_dir,
        )
        runner = AIShadowRunner(flags=flags, store=store, handlers=handlers)
        records = runner.run(
            AIExperimentContext(
                run_id=run_id,
                entity_id=entity_id,
                observation_id=observation_id,
                source_urls=(
                    str(corpus_definition.get("source_url")),
                )
                if corpus_definition.get("source_url")
                else (),
            )
        )
        return AIShadowCollectionReport(entity_id=entity_id, records=records)
    except Exception as exc:  # armazenamento ou configuração também não bloqueiam o baseline
        return AIShadowCollectionReport(
            entity_id=entity_id,
            error=f"{type(exc).__name__}: {exc}",
        )
