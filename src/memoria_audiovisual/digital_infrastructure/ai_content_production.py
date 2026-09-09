"""Classificação e quantificação de IA aplicada ao próprio conteúdo audiovisual.

Esta dimensão é distinta de ``institutional_ai_use``: aqui a unidade é um item,
versão ou segmento audiovisual. Uma instituição pode usar IA para pesquisar ou
catalogar um acervo sem que seus conteúdos tenham sido produzidos com IA, e o
inverso também é possível.

O baseline abaixo é deliberadamente conservador: só produz classificação positiva
quando existe evidência textual/estruturada verificável. Aparência visual isolada
ou um score de detector não são prova suficiente para publicação científica.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Iterable, Literal, Mapping, Sequence

from .ai_contracts import AIEvidenceReference, AIExperimentRecord, AIModelDescriptor

AI_CONTENT_PROTOCOL_VERSION = "1.0.0"

AIContentUsageClass = Literal[
    "no_verified_ai_evidence",
    "ai_assisted_production",
    "materially_ai_modified",
    "partially_synthetic",
    "fully_synthetic",
    "not_assessable",
]

AIContentEvidenceStrength = Literal[
    "verified_disclosure",
    "structured_provenance",
    "technical_metadata",
    "supporting_signal_only",
    "none",
]

POSITIVE_CONTENT_CLASSES: tuple[AIContentUsageClass, ...] = (
    "ai_assisted_production",
    "materially_ai_modified",
    "partially_synthetic",
    "fully_synthetic",
)
SYNTHETIC_CONTENT_CLASSES: tuple[AIContentUsageClass, ...] = (
    "partially_synthetic",
    "fully_synthetic",
)
MATERIAL_AI_CLASSES: tuple[AIContentUsageClass, ...] = (
    "materially_ai_modified",
    "partially_synthetic",
    "fully_synthetic",
)

# Termos fortes devem expressar papel da IA na criação/modificação do item.
_FULLY_SYNTHETIC_TERMS = (
    "fully ai-generated",
    "fully ai generated",
    "entirely ai-generated",
    "entirely ai generated",
    "100% ai-generated",
    "100% ai generated",
    "entièrement généré par intelligence artificielle",
    "entièrement générée par intelligence artificielle",
    "entièrement généré par l'ia",
    "entièrement générée par l'ia",
    "totalmente generado por inteligencia artificial",
    "totalmente generada por inteligencia artificial",
    "totalmente gerado por inteligência artificial",
    "totalmente gerada por inteligência artificial",
)

_PARTIALLY_SYNTHETIC_TERMS = (
    "ai-generated imagery",
    "ai generated imagery",
    "ai-generated images",
    "ai generated images",
    "ai-generated scenes",
    "ai generated scenes",
    "ai-generated voice",
    "ai generated voice",
    "synthetic voice",
    "synthetic media",
    "generative ai visuals",
    "images générées par ia",
    "voix synthétique",
    "escenas generadas por ia",
    "imágenes generadas por ia",
    "voz sintética",
    "cenas geradas por ia",
    "imagens geradas por ia",
    "voz sintética",
)

_MATERIAL_MODIFICATION_TERMS = (
    "deepfake",
    "face swap",
    "voice clone",
    "voice cloning",
    "cloned voice",
    "ai dubbing",
    "ai-dubbed",
    "generative fill",
    "ai-generated background",
    "ai generated background",
    "ai-altered video",
    "ai altered video",
    "ai-manipulated video",
    "ai manipulated video",
    "vidéo modifiée par ia",
    "voix clonée",
    "vídeo modificado con ia",
    "voz clonada",
    "vídeo modificado por ia",
    "voz clonada por ia",
)

_ASSISTED_PRODUCTION_TERMS = (
    "ai-assisted editing",
    "ai assisted editing",
    "ai-assisted production",
    "ai assisted production",
    "ai-assisted animation",
    "ai assisted animation",
    "ai-assisted colour",
    "ai assisted colour",
    "ai-assisted subtitles",
    "ai assisted subtitles",
    "ai-generated subtitles",
    "montage assisté par ia",
    "production assistée par ia",
    "sous-titres générés par ia",
    "edición asistida por ia",
    "producción asistida por ia",
    "subtítulos generados por ia",
    "edição assistida por ia",
    "produção assistida por ia",
    "legendas geradas por ia",
)

_AI_DISCLOSURE_TERMS = (
    "artificial intelligence",
    "intelligence artificielle",
    "inteligencia artificial",
    "inteligência artificial",
    "generative ai",
    "ia generativa",
    "machine learning",
)

_PRODUCTION_CONTEXT_TERMS = (
    "created",
    "generated",
    "produced",
    "production",
    "edited",
    "modified",
    "altered",
    "animation",
    "voice",
    "image",
    "video",
    "audio",
    "créé",
    "généré",
    "produit",
    "production",
    "modifié",
    "voix",
    "image",
    "vidéo",
    "creado",
    "generado",
    "producido",
    "producción",
    "modificado",
    "voz",
    "imagen",
    "vídeo",
    "criado",
    "gerado",
    "produzido",
    "produção",
    "modificado",
    "voz",
    "imagem",
    "vídeo",
)

_MODEL = AIModelDescriptor(
    provider="local",
    model_name="deterministic-content-ai-evidence-baseline",
    model_version="1.0.0",
    classifier_version="explicit-disclosure-v1",
)


@dataclass(frozen=True, slots=True)
class AIContentUsageObservation:
    entity_id: str
    item_id: str
    usage_class: AIContentUsageClass
    evidence_strength: AIContentEvidenceStrength
    source_url: str | None = None
    excerpt: str | None = None
    item_version_id: str | None = None
    segment_id: str | None = None
    language: str | None = None
    date_bucket: str | None = None
    confidence: float | None = None
    protocol_version: str = AI_CONTENT_PROTOCOL_VERSION

    @property
    def is_ai_positive(self) -> bool:
        return self.usage_class in POSITIVE_CONTENT_CLASSES

    @property
    def is_synthetic(self) -> bool:
        return self.usage_class in SYNTHETIC_CONTENT_CLASSES

    @property
    def is_materially_changed(self) -> bool:
        return self.usage_class in MATERIAL_AI_CLASSES

    @property
    def is_evaluable(self) -> bool:
        return self.usage_class != "not_assessable"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AIContentQuantification:
    scope: str
    items_total: int
    items_evaluable: int
    items_not_assessable: int
    items_with_ai_evidence: int
    items_materially_ai_changed: int
    items_synthetic: int
    share_with_ai_evidence: float | None
    share_materially_ai_changed: float | None
    share_synthetic: float | None
    class_counts: Mapping[str, int]
    protocol_version: str = AI_CONTENT_PROTOCOL_VERSION

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["class_counts"] = dict(self.class_counts)
        return data


def _normalize_text(parts: Iterable[str | None]) -> str:
    return "\n".join(part.strip() for part in parts if isinstance(part, str) and part.strip()).lower()


def _first_match(text: str, terms: Sequence[str]) -> str | None:
    for term in terms:
        if term in text:
            return term
    return None


def _generic_explicit_ai_production_signal(text: str, *, window: int = 700) -> str | None:
    """Fallback para declarações explícitas não cobertas pelo vocabulário forte."""
    for ai_term in _AI_DISCLOSURE_TERMS:
        start = 0
        while True:
            position = text.find(ai_term, start)
            if position < 0:
                break
            left = max(0, position - window)
            right = min(len(text), position + len(ai_term) + window)
            context = text[left:right]
            production = _first_match(context, _PRODUCTION_CONTEXT_TERMS)
            if production:
                return f"{ai_term} + {production}"
            start = position + len(ai_term)
    return None


def classify_ai_content_usage(
    *,
    entity_id: str,
    item_id: str,
    texts: Sequence[str] = (),
    source_url: str | None = None,
    item_version_id: str | None = None,
    segment_id: str | None = None,
    language: str | None = None,
    date_bucket: str | None = None,
    structured_provenance_ai: bool = False,
    technical_metadata_ai: bool = False,
    supporting_model_score: float | None = None,
) -> AIContentUsageObservation:
    """Classifica papel da IA no item usando evidência verificável.

    ``supporting_model_score`` nunca torna um caso positivo sozinho. Ele pode ser
    preservado como sinal auxiliar para triagem humana.
    """
    if not entity_id.strip() or not item_id.strip():
        raise ValueError("entity_id e item_id são obrigatórios")
    if supporting_model_score is not None and not 0 <= supporting_model_score <= 1:
        raise ValueError("supporting_model_score deve estar entre 0 e 1")

    text = _normalize_text(texts)
    matched: str | None = None
    usage_class: AIContentUsageClass = "no_verified_ai_evidence"
    evidence_strength: AIContentEvidenceStrength = "none"

    if (matched := _first_match(text, _FULLY_SYNTHETIC_TERMS)) is not None:
        usage_class = "fully_synthetic"
        evidence_strength = "verified_disclosure"
    elif (matched := _first_match(text, _PARTIALLY_SYNTHETIC_TERMS)) is not None:
        usage_class = "partially_synthetic"
        evidence_strength = "verified_disclosure"
    elif (matched := _first_match(text, _MATERIAL_MODIFICATION_TERMS)) is not None:
        usage_class = "materially_ai_modified"
        evidence_strength = "verified_disclosure"
    elif (matched := _first_match(text, _ASSISTED_PRODUCTION_TERMS)) is not None:
        usage_class = "ai_assisted_production"
        evidence_strength = "verified_disclosure"
    elif structured_provenance_ai:
        usage_class = "ai_assisted_production"
        evidence_strength = "structured_provenance"
        matched = "structured provenance declares AI involvement"
    elif technical_metadata_ai:
        usage_class = "ai_assisted_production"
        evidence_strength = "technical_metadata"
        matched = "technical metadata declares AI involvement"
    elif (matched := _generic_explicit_ai_production_signal(text)) is not None:
        usage_class = "ai_assisted_production"
        evidence_strength = "verified_disclosure"
    elif supporting_model_score is not None:
        evidence_strength = "supporting_signal_only"
        matched = f"supporting model score={supporting_model_score:.4f}; not sufficient for positive classification"

    return AIContentUsageObservation(
        entity_id=entity_id,
        item_id=item_id,
        item_version_id=item_version_id,
        segment_id=segment_id,
        usage_class=usage_class,
        evidence_strength=evidence_strength,
        source_url=source_url,
        excerpt=matched,
        language=language,
        date_bucket=date_bucket,
        confidence=supporting_model_score,
    )


def observation_to_experiment_record(
    observation: AIContentUsageObservation,
    *,
    run_id: str,
    observation_id: str | None = None,
) -> AIExperimentRecord:
    positive = observation.is_ai_positive
    evidence: tuple[AIEvidenceReference, ...] = ()
    if observation.excerpt and (observation.source_url or observation.item_id):
        evidence = (
            AIEvidenceReference(
                evidence_id=f"{observation.entity_id}:{observation.item_id}:ai-content-production",
                evidence_type=(
                    "metadata"
                    if observation.evidence_strength in {"structured_provenance", "technical_metadata"}
                    else "textual"
                ),
                source_url=observation.source_url,
                artifact_id=None if observation.source_url else f"item:{observation.item_id}",
                excerpt=observation.excerpt,
                language=observation.language,
            ),
        )
    return AIExperimentRecord(
        run_id=run_id,
        entity_id=observation.entity_id,
        task="ai_content_production_detection",
        status="detected_pending_review" if positive else "not_identified_on_assessed_surfaces",
        prediction=observation.usage_class if positive else None,
        confidence=observation.confidence,
        observation_id=observation_id,
        item_id=observation.item_id,
        item_version_id=observation.item_version_id,
        segment_id=observation.segment_id,
        language=observation.language,
        evidence=evidence,
        model=_MODEL,
        human_review_status="pending" if positive else "not_requested",
        notes=(
            "Classificação de IA na produção do conteúdo; distinta de uso institucional de IA. "
            "Sinais visuais/model scores sem evidência verificável não geram positivo científico."
        ),
    )


def quantify_ai_content_usage(
    observations: Sequence[AIContentUsageObservation],
    *,
    scope: str = "all",
) -> AIContentQuantification:
    class_counts = Counter(item.usage_class for item in observations)
    evaluable = [item for item in observations if item.is_evaluable]
    positive = [item for item in evaluable if item.is_ai_positive]
    material = [item for item in evaluable if item.is_materially_changed]
    synthetic = [item for item in evaluable if item.is_synthetic]
    denominator = len(evaluable)

    def share(numerator: int) -> float | None:
        return numerator / denominator if denominator else None

    return AIContentQuantification(
        scope=scope,
        items_total=len(observations),
        items_evaluable=denominator,
        items_not_assessable=len(observations) - denominator,
        items_with_ai_evidence=len(positive),
        items_materially_ai_changed=len(material),
        items_synthetic=len(synthetic),
        share_with_ai_evidence=share(len(positive)),
        share_materially_ai_changed=share(len(material)),
        share_synthetic=share(len(synthetic)),
        class_counts=dict(class_counts),
    )


def quantify_ai_content_by(
    observations: Sequence[AIContentUsageObservation],
    *,
    attribute: Literal["entity_id", "language", "date_bucket"] = "entity_id",
) -> dict[str, AIContentQuantification]:
    groups: dict[str, list[AIContentUsageObservation]] = defaultdict(list)
    for item in observations:
        value = getattr(item, attribute)
        groups[str(value or "unknown")].append(item)
    return {
        key: quantify_ai_content_usage(values, scope=f"{attribute}:{key}")
        for key, values in sorted(groups.items())
    }


__all__ = [
    "AI_CONTENT_PROTOCOL_VERSION",
    "AIContentEvidenceStrength",
    "AIContentQuantification",
    "AIContentUsageClass",
    "AIContentUsageObservation",
    "MATERIAL_AI_CLASSES",
    "POSITIVE_CONTENT_CLASSES",
    "SYNTHETIC_CONTENT_CLASSES",
    "classify_ai_content_usage",
    "observation_to_experiment_record",
    "quantify_ai_content_by",
    "quantify_ai_content_usage",
]
