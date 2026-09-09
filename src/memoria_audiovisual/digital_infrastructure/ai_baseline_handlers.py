"""Baselines determinísticos para comparar futuros classificadores de IA."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .ai_contracts import AIEvidenceReference, AIExperimentRecord, AIModelDescriptor
from .ai_runtime import AIExperimentContext, AIExperimentHandler

_TEXT_EXTENSIONS = {".csv", ".html", ".htm", ".json", ".jsonl", ".md", ".txt"}
_MAX_FILE_BYTES = 2_000_000
_MAX_FILES = 40

_INSTITUTIONAL_AI_TERMS = (
    "artificial intelligence",
    "intelligence artificielle",
    "inteligência artificial",
    "inteligencia artificial",
    "machine learning",
    "aprendizado de máquina",
    "apprentissage automatique",
    "aprendizaje automático",
    "deep learning",
    "computer vision",
    "reconhecimento automático",
    "reconocimiento automático",
    "automatic transcription",
    "transcription automatique",
    "transcripción automática",
    "transcrição automática",
    "speech-to-text",
    "whisper",
    "transkribus",
    "google cloud vision",
    "azure ai",
    "aws rekognition",
)

# O uso institucional de IA exige relação observável com o acervo audiovisual.
_AI_COLLECTION_CONTEXT_TERMS = (
    "audiovisual",
    "audio-visual",
    "moving image",
    "moving-image",
    "film",
    "filme",
    "película",
    "video",
    "vídeo",
    "archive",
    "archives",
    "arquivo",
    "archivo",
    "acervo",
    "collection",
    "collections",
    "coleção",
    "colección",
    "fonds",
    "patrimoine",
)

_AI_OPERATION_TERMS = (
    "catalog",
    "catalogue",
    "cataloging",
    "cataloguing",
    "catalogação",
    "catalogación",
    "catalogage",
    "metadata",
    "metadados",
    "metadatos",
    "métadonnées",
    "metadatado",
    "indexing",
    "indexação",
    "indexación",
    "indexation",
    "transcription",
    "transcrição",
    "transcripción",
    "translation",
    "tradução",
    "traducción",
    "traduction",
    "subtitle",
    "subtitling",
    "legendagem",
    "sous-titrage",
    "subtitulado",
    "recognition",
    "reconhecimento",
    "reconocimiento",
    "reconnaissance",
    "identification",
    "identificação",
    "identificación",
    "classification",
    "classificação",
    "clasificación",
    "restoration",
    "restauração",
    "restauración",
    "restauration",
    "preservation",
    "preservação",
    "preservación",
    "préservation",
    "search",
    "busca",
    "búsqueda",
    "recherche",
    "recommendation",
    "recomendação",
    "recomendación",
    "recommandation",
    "segmentation",
    "segmentação",
    "segmentación",
    "speech recognition",
    "face recognition",
    "facial recognition",
    "reconhecimento facial",
    "reconocimiento facial",
    "named entity",
    "entités nommées",
    "entidades nombradas",
    "resumo",
    "resumen",
    "summary",
)

_AUDIOVISUAL_COLLECTION_TERMS = (
    "audiovisual collection",
    "audiovisual archive",
    "audiovisual heritage",
    "moving image",
    "moving-image",
    "film collection",
    "video collection",
    "collection audiovisuelle",
    "archives audiovisuelles",
    "patrimoine audiovisuel",
    "acervo audiovisual",
    "arquivo audiovisual",
    "archivo audiovisual",
    "coleção audiovisual",
    "colección audiovisual",
    "cinematheque",
    "cinémathèque",
    "film archive",
)

_PUBLIC_VIDEO_TERMS = (
    "youtube.com/watch",
    "youtu.be/",
    "vimeo.com/",
    "<video",
    "player.vimeo",
    "youtube-nocookie",
    ".m3u8",
    ".mpd",
    ".mp4",
    ".webm",
    "hls",
    "dash",
    "embedded player",
    "player incorporado",
)

_MODEL = AIModelDescriptor(
    provider="local",
    model_name="deterministic-evidence-baseline",
    model_version="1.1.0",
    classifier_version="keyword-structure-context-v2",
)


def _flatten_paths(value: Any) -> Iterable[Path]:
    if isinstance(value, (str, Path)):
        yield Path(value)
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _flatten_paths(item)
    elif isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            yield from _flatten_paths(item)


def _resolve_artifact_paths(
    corpus_definition: Mapping[str, Any],
    output_dir: Path,
) -> tuple[Path, ...]:
    candidates: list[Path] = []
    for path in _flatten_paths(corpus_definition.get("output_files", ())):
        resolved = path if path.is_absolute() else output_dir / path
        if resolved.exists() and resolved.is_file() and resolved.suffix.lower() in _TEXT_EXTENSIONS:
            candidates.append(resolved)
    return tuple(dict.fromkeys(candidates))[:_MAX_FILES]


def _read_artifact_text(paths: tuple[Path, ...], output_dir: Path) -> tuple[str, tuple[str, ...]]:
    chunks: list[str] = []
    artifact_ids: list[str] = []
    for path in paths:
        try:
            if path.stat().st_size > _MAX_FILE_BYTES:
                continue
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
            try:
                artifact_ids.append(str(path.relative_to(output_dir)))
            except ValueError:
                artifact_ids.append(str(path))
        except OSError:
            continue
    return "\n".join(chunks), tuple(artifact_ids)


def _normalized_text(
    corpus_definition: Mapping[str, Any],
    snapshot_metadata: Mapping[str, Any],
    output_dir: Path,
) -> tuple[str, tuple[str, ...]]:
    paths = _resolve_artifact_paths(corpus_definition, output_dir)
    artifact_text, artifact_ids = _read_artifact_text(paths, output_dir)
    metadata_text = json.dumps(
        {"snapshot": snapshot_metadata},
        ensure_ascii=False,
        default=str,
    )
    return f"{metadata_text}\n{artifact_text}".lower(), artifact_ids


def _find_terms(text: str, terms: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(term for term in terms if term in text)


def _find_contextual_ai_evidence(text: str, *, window: int = 900) -> tuple[str, ...]:
    """Exige IA + contexto de acervo + operação em proximidade textual.

    A regra evita considerar como uso institucional uma menção genérica a IA,
    automação ou tecnologia que não esteja ligada a uma atividade sobre o acervo.
    """
    evidence: list[str] = []
    for ai_term in _INSTITUTIONAL_AI_TERMS:
        start = 0
        while True:
            position = text.find(ai_term, start)
            if position < 0:
                break
            left = max(0, position - window)
            right = min(len(text), position + len(ai_term) + window)
            context = text[left:right]
            collection_matches = _find_terms(context, _AI_COLLECTION_CONTEXT_TERMS)
            operation_matches = _find_terms(context, _AI_OPERATION_TERMS)
            if collection_matches and operation_matches:
                evidence.extend(
                    (
                        ai_term,
                        f"collection-context:{collection_matches[0]}",
                        f"operation-context:{operation_matches[0]}",
                    )
                )
                break
            start = position + len(ai_term)
    return tuple(dict.fromkeys(evidence))


def _evidence(
    *,
    context: AIExperimentContext,
    artifact_ids: tuple[str, ...],
    matched_terms: tuple[str, ...],
    source_url: str | None,
    evidence_prefix: str,
) -> tuple[AIEvidenceReference, ...]:
    references: list[AIEvidenceReference] = []
    if matched_terms:
        references.append(
            AIEvidenceReference(
                evidence_id=f"{evidence_prefix}:terms",
                evidence_type="deterministic",
                source_url=source_url,
                artifact_id=artifact_ids[0] if artifact_ids else f"context:{context.entity_id}",
                excerpt=", ".join(matched_terms[:12]),
                language=context.language,
            )
        )
    if context.observation_id:
        references.append(
            AIEvidenceReference(
                evidence_id=f"{evidence_prefix}:snapshot",
                evidence_type="metadata",
                artifact_id=f"snapshot:{context.observation_id}",
                language=context.language,
            )
        )
    return tuple(references)


def build_entity_baseline_handlers(
    *,
    corpus_definition: Mapping[str, Any],
    snapshot_metadata: Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, AIExperimentHandler]:
    """Cria handlers locais. Eles são baselines, não classificadores científicos."""

    output_path = Path(output_dir)
    text, artifact_ids = _normalized_text(corpus_definition, snapshot_metadata, output_path)
    source_url = str(corpus_definition.get("source_url") or "") or None
    counts = snapshot_metadata.get("counts", {}) if isinstance(snapshot_metadata, Mapping) else {}
    video_count = int(counts.get("video_links_total", 0) or 0)
    catalogue_video_count = int(counts.get("videos_in_curatorial_catalog", 0) or 0)

    def institutional_ai_use(context: AIExperimentContext) -> AIExperimentRecord:
        matches = _find_contextual_ai_evidence(text)
        detected = bool(matches)
        return AIExperimentRecord(
            run_id=context.run_id,
            entity_id=context.entity_id,
            task="institutional_ai_use",
            status="detected_pending_review" if detected else "not_identified_on_assessed_surfaces",
            prediction="public_institutional_ai_signal" if detected else None,
            observation_id=context.observation_id,
            language=context.language,
            evidence=_evidence(
                context=context,
                artifact_ids=artifact_ids,
                matched_terms=matches,
                source_url=source_url,
                evidence_prefix=f"{context.entity_id}:institutional-ai",
            ),
            model=_MODEL,
            human_review_status="pending" if detected else "not_requested",
            notes=(
                "Baseline determinístico contextual; exige termo de IA próximo a contexto de acervo "
                "e atividade operacional. Ausência de sinal não prova ausência institucional."
            ),
        )

    def audiovisual_collection_detection(context: AIExperimentContext) -> AIExperimentRecord:
        matches = _find_terms(text, _AUDIOVISUAL_COLLECTION_TERMS)
        detected = bool(matches or video_count or catalogue_video_count)
        return AIExperimentRecord(
            run_id=context.run_id,
            entity_id=context.entity_id,
            task="audiovisual_collection_detection",
            status="detected_pending_review" if detected else "not_identified_on_assessed_surfaces",
            prediction="audiovisual_collection_signal" if detected else None,
            observation_id=context.observation_id,
            language=context.language,
            evidence=_evidence(
                context=context,
                artifact_ids=artifact_ids,
                matched_terms=matches,
                source_url=source_url,
                evidence_prefix=f"{context.entity_id}:audiovisual-collection",
            ),
            model=_MODEL,
            human_review_status="pending" if detected else "not_requested",
            notes="Baseline determinístico de comparação; não define elegibilidade.",
        )

    def public_video_presence_detection(context: AIExperimentContext) -> AIExperimentRecord:
        matches = _find_terms(text, _PUBLIC_VIDEO_TERMS)
        detected = bool(matches or video_count or catalogue_video_count)
        return AIExperimentRecord(
            run_id=context.run_id,
            entity_id=context.entity_id,
            task="public_video_presence_detection",
            status="detected_pending_review" if detected else "not_identified_on_assessed_surfaces",
            prediction="public_video_signal" if detected else None,
            observation_id=context.observation_id,
            language=context.language,
            evidence=_evidence(
                context=context,
                artifact_ids=artifact_ids,
                matched_terms=matches,
                source_url=source_url,
                evidence_prefix=f"{context.entity_id}:public-video",
            ),
            model=_MODEL,
            human_review_status="pending" if detected else "not_requested",
            notes=(
                f"Contagens do snapshot: video_links_total={video_count}; "
                f"videos_in_curatorial_catalog={catalogue_video_count}."
            ),
        )

    return {
        "institutional_ai_use": institutional_ai_use,
        "audiovisual_collection_detection": audiovisual_collection_detection,
        "public_video_presence_detection": public_video_presence_detection,
    }
