"""Integração fail-open da coleta experimental de IA com ciclos oficiais."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .ai_baseline_handlers import build_entity_baseline_handlers
from .ai_contracts import AIExperimentRecord
from .ai_flags import AIExperimentFlags
from .ai_runtime import AIExperimentContext, AIShadowRunner
from .ai_storage import AIExperimentStore
from .ai_surface_discovery import (
    SurfaceDiscoveryPolicy,
    discover_and_materialize_public_surfaces,
)


@dataclass(frozen=True, slots=True)
class AIShadowCollectionReport:
    entity_id: str
    records: tuple[AIExperimentRecord, ...] = ()
    error: str | None = None
    surface_discovery_artifact: str | None = None
    surface_classifier_artifact: str | None = None
    surface_pages_fetched: int = 0

    @property
    def successful(self) -> bool:
        return self.error is None


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _surface_policy_from_env() -> SurfaceDiscoveryPolicy:
    return SurfaceDiscoveryPolicy(
        max_depth=int(os.getenv("AI_SURFACE_MAX_DEPTH", "2")),
        max_pages=int(os.getenv("AI_SURFACE_MAX_PAGES", "24")),
        timeout_seconds=float(os.getenv("AI_SURFACE_TIMEOUT_SECONDS", "12")),
        max_response_bytes=int(os.getenv("AI_SURFACE_MAX_RESPONSE_BYTES", "1500000")),
        max_text_chars=int(os.getenv("AI_SURFACE_MAX_TEXT_CHARS", "120000")),
        respect_robots_txt=_env_bool("AI_SURFACE_RESPECT_ROBOTS", True),
    )


def _relative_or_absolute(path: Path, output_dir: str | Path) -> str:
    output_path = Path(output_dir)
    try:
        return str(path.relative_to(output_path))
    except ValueError:
        return str(path)


def _with_surface_classifier_artifact(
    corpus_definition: Mapping[str, Any],
    classifier_path: Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    augmented = dict(corpus_definition)
    current_outputs = corpus_definition.get("output_files", {})
    if isinstance(current_outputs, Mapping):
        output_files: dict[str, Any] = dict(current_outputs)
    else:
        output_files = {"official_outputs": current_outputs}
    output_files["_ai_surface_classifier_text"] = _relative_or_absolute(
        classifier_path,
        output_dir,
    )
    augmented["output_files"] = output_files
    return augmented


def collect_entity_shadow_signals(
    *,
    run_id: str,
    corpus_definition: Mapping[str, Any],
    snapshot_metadata: Mapping[str, Any],
    output_dir: str | Path,
    flags: AIExperimentFlags,
    store: AIExperimentStore,
) -> AIShadowCollectionReport:
    """Coleta sinais experimentais sem propagar falhas para o ciclo oficial.

    Quando existe ``source_url``, o T2A pode ampliar a observação para páginas
    internas e subdomínios institucionais públicos. Essa exploração é limitada,
    auditável e separada do baseline oficial. Falhas nessa etapa são registradas,
    mas não bloqueiam nem o baseline nem a coleta dos sinais já disponíveis.
    """

    entity_id = str(corpus_definition.get("code") or "").strip()
    if not entity_id:
        return AIShadowCollectionReport(
            entity_id="unknown",
            error="corpus_definition sem code",
        )
    if not flags.enabled_tasks:
        return AIShadowCollectionReport(entity_id=entity_id)

    observation_id = str(snapshot_metadata.get("observation_key") or "").strip() or None
    working_corpus: Mapping[str, Any] = corpus_definition
    surface_report_path: Path | None = None
    surface_classifier_path: Path | None = None
    surface_pages_fetched = 0
    surface_error: str | None = None

    source_url = str(corpus_definition.get("source_url") or "").strip()
    if source_url and _env_bool("AI_SURFACE_DISCOVERY_ENABLED", True):
        try:
            surface_report, surface_report_path, surface_classifier_path = (
                discover_and_materialize_public_surfaces(
                    source_url,
                    output_dir=output_dir,
                    run_id=run_id,
                    entity_id=entity_id,
                    policy=_surface_policy_from_env(),
                )
            )
            surface_pages_fetched = surface_report.fetched_pages
            working_corpus = _with_surface_classifier_artifact(
                corpus_definition,
                surface_classifier_path,
                output_dir,
            )
            if surface_report.errors:
                surface_error = (
                    "surface_discovery_partial: "
                    + " | ".join(surface_report.errors[:5])
                )
        except Exception as exc:
            # Fail-open deliberado: profundidade adicional nunca bloqueia o baseline.
            surface_error = f"surface_discovery: {type(exc).__name__}: {exc}"

    try:
        handlers = build_entity_baseline_handlers(
            corpus_definition=working_corpus,
            snapshot_metadata=snapshot_metadata,
            output_dir=output_dir,
        )
        runner = AIShadowRunner(flags=flags, store=store, handlers=handlers)
        records = runner.run(
            AIExperimentContext(
                run_id=run_id,
                entity_id=entity_id,
                observation_id=observation_id,
                source_urls=(source_url,) if source_url else (),
                artifacts=(
                    _relative_or_absolute(surface_report_path, output_dir),
                    _relative_or_absolute(surface_classifier_path, output_dir),
                )
                if surface_report_path is not None and surface_classifier_path is not None
                else (),
            )
        )
        return AIShadowCollectionReport(
            entity_id=entity_id,
            records=records,
            error=surface_error,
            surface_discovery_artifact=(
                _relative_or_absolute(surface_report_path, output_dir)
                if surface_report_path is not None
                else None
            ),
            surface_classifier_artifact=(
                _relative_or_absolute(surface_classifier_path, output_dir)
                if surface_classifier_path is not None
                else None
            ),
            surface_pages_fetched=surface_pages_fetched,
        )
    except Exception as exc:  # armazenamento ou configuração também não bloqueiam o baseline
        error = f"{type(exc).__name__}: {exc}"
        if surface_error:
            error = f"{surface_error}; signal_collection: {error}"
        return AIShadowCollectionReport(
            entity_id=entity_id,
            error=error,
            surface_discovery_artifact=(
                _relative_or_absolute(surface_report_path, output_dir)
                if surface_report_path is not None
                else None
            ),
            surface_classifier_artifact=(
                _relative_or_absolute(surface_classifier_path, output_dir)
                if surface_classifier_path is not None
                else None
            ),
            surface_pages_fetched=surface_pages_fetched,
        )
