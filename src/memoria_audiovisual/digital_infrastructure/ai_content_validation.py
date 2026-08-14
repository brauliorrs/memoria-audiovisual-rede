"""Amostra item a item para calibrar IA na produção audiovisual.

A amostra é deliberadamente pequena e contrastiva. Ela não estima prevalência no
corpus: serve para testar se o motor distingue classes de participação de IA e
casos sem evidência verificável antes de qualquer execução em escala.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .ai_content_production import (
    AIContentUsageClass,
    POSITIVE_CONTENT_CLASSES,
    classify_ai_content_usage,
)

AI_CONTENT_VALIDATION_SAMPLE_ID = "ai-content-validation-sample-v1"
AI_CONTENT_VALIDATION_SAMPLE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class AIContentValidationControl:
    control_id: str
    entity_id: str
    item_id: str
    item_url: str
    evidence_url: str
    evidence_text: str
    expected_usage_class: AIContentUsageClass
    language: str
    control_type: str
    evidence_source_role: str
    date_bucket: str | None = None
    rationale: str = ""

    @property
    def expected_positive(self) -> bool:
        return self.expected_usage_class in POSITIVE_CONTENT_CLASSES

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["expected_positive"] = self.expected_positive
        return data


CONTROLS: tuple[AIContentValidationControl, ...] = (
    AIContentValidationControl(
        control_id="rtve-telediario-futuro-2026",
        entity_id="rtve_external_control",
        item_id="rtve-play-17127011",
        item_url="https://www.rtve.es/play/videos/telediario-2/td-explora-riesgos-oportunidades-ia-telediario-del-futuro/17127011/",
        evidence_url="https://www.rtve.es/noticias/20260623/telediario-futuro-ia-rtve-pepa-bueno-making-of/17127637.shtml",
        evidence_text=(
            "El especial contiene escenas generadas por IA y una versión de Pepa Bueno hecha con IA; "
            "RTVE documenta que partes del programa fueron realizadas con inteligencia artificial."
        ),
        expected_usage_class="partially_synthetic",
        language="es",
        control_type="positive_external",
        evidence_source_role="producer_disclosure",
        date_bucket="2026",
        rationale="Programa real que mezcla producción convencional con elementos audiovisuales generados por IA.",
    ),
    AIContentValidationControl(
        control_id="bfi-tokinokawa-2021",
        entity_id="bfi",
        item_id="tokinokawa-2021",
        item_url="https://www.bfi.org.uk/interviews/light-surgeons-tokinokawa",
        evidence_url="https://www.bfi.org.uk/interviews/light-surgeons-tokinokawa",
        evidence_text=(
            "The audiovisual installation used images analysed by bespoke artificial intelligence software "
            "and presented the analysis through an animated infographic layer."
        ),
        expected_usage_class="ai_assisted_production",
        language="en",
        control_type="positive_corpus_related",
        evidence_source_role="commissioner_creator_interview",
        date_bucket="2021",
        rationale="Uso de IA no processo criativo sem evidência de que o conteúdo inteiro seja sintético.",
    ),
    AIContentValidationControl(
        control_id="dreadclub-vampires-verdict-2024",
        entity_id="external_film_control",
        item_id="dreadclub-vampires-verdict",
        item_url="https://www.bfi.org.uk/sight-and-sound/features/2024-year-ai",
        evidence_url="https://www.bfi.org.uk/sight-and-sound/features/2024-year-ai",
        evidence_text="BFI describes DreadClub: Vampire's Verdict as a fully AI-generated animated feature.",
        expected_usage_class="fully_synthetic",
        language="en",
        control_type="positive_external",
        evidence_source_role="authoritative_independent_description",
        date_bucket="2024",
        rationale="Controle positivo forte para a classe integralmente sintética.",
    ),
    AIContentValidationControl(
        control_id="rtve-telediario-2025-negative",
        entity_id="rtve_external_control",
        item_id="rtve-play-16856409",
        item_url="https://www.rtve.es/play/videos/telediario-1/1-en-cuatro-minutos-12-12-25/16856409/",
        evidence_url="https://www.rtve.es/play/videos/telediario-1/1-en-cuatro-minutos-12-12-25/16856409/",
        evidence_text=(
            "Telediario 1 en cuatro minutos, 12/12/2025. Resumen informativo de actualidad con ficha técnica, "
            "sin declaración verificável de IA aplicada a la producción del ítem."
        ),
        expected_usage_class="no_verified_ai_evidence",
        language="es",
        control_type="negative_external",
        evidence_source_role="official_item_page",
        date_bucket="2025",
        rationale="Controle negativo contemporâneo da mesma organização do positivo espanhol.",
    ),
    AIContentValidationControl(
        control_id="bfi-japanese-dancers-1894-negative",
        entity_id="bfi",
        item_id="japanese-dancers-1894",
        item_url="https://player.bfi.org.uk/free/film/watch-japanese-dancers-1894-online",
        evidence_url="https://player.bfi.org.uk/free/film/watch-japanese-dancers-1894-online",
        evidence_text=(
            "Japanese Dancers, produced in 1894 for Edison's Kinetoscope; BFI item metadata describes the "
            "historical production and does not disclose AI involvement in the audiovisual content."
        ),
        expected_usage_class="no_verified_ai_evidence",
        language="en",
        control_type="negative_corpus_related",
        evidence_source_role="official_item_page",
        date_bucket="1894",
        rationale="Controle histórico forte para ausência de evidência verificável de IA na produção original.",
    ),
    AIContentValidationControl(
        control_id="bfi-japanese-procession-1904-negative",
        entity_id="bfi",
        item_id="japanese-procession-of-state-1904",
        item_url="https://player.bfi.org.uk/free/film/watch-japanese-procession-of-state-1904-online",
        evidence_url="https://player.bfi.org.uk/free/film/watch-japanese-procession-of-state-1904-online",
        evidence_text=(
            "Japanese Procession of State, issued by the Hepworth Manufacturing Company in 1904; the BFI "
            "item description contains no verified disclosure of AI involvement in content production."
        ),
        expected_usage_class="no_verified_ai_evidence",
        language="en",
        control_type="negative_corpus_related",
        evidence_source_role="official_item_page",
        date_bucket="1904",
        rationale="Segundo negativo histórico para evitar dependência de um único item de controle.",
    ),
)


def build_ai_content_validation_sample() -> dict[str, Any]:
    positives = sum(control.expected_positive for control in CONTROLS)
    negatives = len(CONTROLS) - positives
    return {
        "sample": {
            "sample_id": AI_CONTENT_VALIDATION_SAMPLE_ID,
            "version": AI_CONTENT_VALIDATION_SAMPLE_VERSION,
            "stage": "t2a_content_ai_calibration",
            "status": "reference_controls_defined",
            "is_prevalence_sample": False,
            "does_not_modify_official_baseline": True,
            "purpose": (
                "Calibrar a classificação item a item de IA na produção audiovisual antes de executar "
                "a dimensão automaticamente sobre o corpus."
            ),
        },
        "summary": {
            "controls": len(CONTROLS),
            "positive_controls": positives,
            "negative_controls": negatives,
            "languages": sorted({control.language for control in CONTROLS}),
            "expected_classes": sorted({control.expected_usage_class for control in CONTROLS}),
        },
        "controls": [control.to_dict() for control in CONTROLS],
    }


def evaluate_ai_content_validation_sample() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    tp = fp = tn = fn = exact = 0
    for control in CONTROLS:
        observed = classify_ai_content_usage(
            entity_id=control.entity_id,
            item_id=control.item_id,
            texts=[control.evidence_text],
            source_url=control.evidence_url,
            language=control.language,
            date_bucket=control.date_bucket,
        )
        predicted_positive = observed.is_ai_positive
        expected_positive = control.expected_positive
        if predicted_positive and expected_positive:
            tp += 1
        elif predicted_positive and not expected_positive:
            fp += 1
        elif not predicted_positive and expected_positive:
            fn += 1
        else:
            tn += 1
        class_match = observed.usage_class == control.expected_usage_class
        exact += int(class_match)
        rows.append(
            {
                "control_id": control.control_id,
                "expected_usage_class": control.expected_usage_class,
                "predicted_usage_class": observed.usage_class,
                "class_match": class_match,
                "expected_positive": expected_positive,
                "predicted_positive": predicted_positive,
                "evidence_strength": observed.evidence_strength,
            }
        )

    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    return {
        "sample_id": AI_CONTENT_VALIDATION_SAMPLE_ID,
        "sample_version": AI_CONTENT_VALIDATION_SAMPLE_VERSION,
        "controls": len(CONTROLS),
        "exact_class_matches": exact,
        "exact_class_accuracy": exact / len(CONTROLS) if CONTROLS else None,
        "binary": {
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "rows": rows,
    }


__all__ = [
    "AI_CONTENT_VALIDATION_SAMPLE_ID",
    "AI_CONTENT_VALIDATION_SAMPLE_VERSION",
    "AIContentValidationControl",
    "CONTROLS",
    "build_ai_content_validation_sample",
    "evaluate_ai_content_validation_sample",
]
