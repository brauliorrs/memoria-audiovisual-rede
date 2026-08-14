"""Amostra inicial canônica para validação dos componentes experimentais de IA."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .ai_contracts import AIExperimentTask

AI_VALIDATION_SAMPLE_VERSION = "1.0.0"
AI_VALIDATION_SAMPLE_ID = "ai-validation-sample-v1"

# A amostra v1 é um artefato histórico versionado. Novas tarefas experimentais
# não são inseridas retroativamente nela. A dimensão ai_content_production_detection
# exige uma amostra item/versão/segmento própria.
INITIAL_VALIDATION_TASKS: tuple[AIExperimentTask, ...] = (
    "institutional_ai_use",
    "audiovisual_collection_detection",
    "public_video_presence_detection",
    "synthetic_video_detection",
)

# O corpus atual é majoritariamente europeu. A amostra inicial cobre idiomas,
# tipos de superfície e o primeiro corpus norte-americano sem alegar
# representatividade global.
_SAMPLE_PLAN = (
    {
        "entity_code": "ape",
        "language_group": "multilingual",
        "geographic_group": "Europe",
        "analytical_stratum": "continental_aggregator",
        "selection_rationale": "Agregador continental e superfície geral de arquivos.",
    },
    {
        "entity_code": "europeana",
        "language_group": "multilingual",
        "geographic_group": "Europe",
        "analytical_stratum": "continental_aggregator",
        "selection_rationale": "Agregador europeu com metadados heterogêneos.",
    },
    {
        "entity_code": "ina",
        "language_group": "fr",
        "geographic_group": "Europe",
        "analytical_stratum": "specialised_audiovisual_institution",
        "selection_rationale": "Instituição audiovisual especializada com superfícies públicas próprias.",
    },
    {
        "entity_code": "bfi",
        "language_group": "en",
        "geographic_group": "Europe",
        "analytical_stratum": "national_audiovisual_institution",
        "selection_rationale": "Instituição audiovisual de língua inglesa e catálogo público.",
    },
    {
        "entity_code": "archipop",
        "language_group": "fr",
        "geographic_group": "Europe",
        "analytical_stratum": "regional_archive_with_public_player",
        "selection_rationale": "Arquivo regional com fichas de filmes e player incorporado.",
    },
    {
        "entity_code": "aapb",
        "language_group": "en",
        "geographic_group": "North America",
        "analytical_stratum": "extraeuropean_contrast",
        "selection_rationale": "Primeiro corpus extraeuropeu e contraste continental inicial.",
    },
)


@dataclass(frozen=True, slots=True)
class AIValidationSampleEntry:
    entity_code: str
    language_group: str
    geographic_group: str
    analytical_stratum: str
    selected_tasks: tuple[AIExperimentTask, ...] = INITIAL_VALIDATION_TASKS
    annotation_status: str = "pending_annotation"
    selection_rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["selected_tasks"] = list(self.selected_tasks)
        return data


def build_initial_validation_sample(
    corpora: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    entries: list[AIValidationSampleEntry] = []
    for plan in _SAMPLE_PLAN:
        entity_code = plan["entity_code"]
        if entity_code not in corpora:
            raise ValueError(f"corpus esperado ausente: {entity_code}")
        corpus = corpora[entity_code]
        if not corpus.get("organism_active"):
            raise ValueError(f"corpus da amostra não está ativo: {entity_code}")
        entries.append(AIValidationSampleEntry(**plan))

    return {
        "sample": {
            "sample_id": AI_VALIDATION_SAMPLE_ID,
            "version": AI_VALIDATION_SAMPLE_VERSION,
            "status": "initial_pending_human_annotation",
            "purpose": (
                "Validar separadamente uso institucional de IA, triagem do observatório "
                "e detecção de conteúdo audiovisual sintético."
            ),
            "is_gold_standard": False,
            "does_not_activate_indicators": True,
            "selection_limitations": (
                "Amostra inicial restrita ao corpus ativo atual; não representa ainda "
                "África, Ásia, Oceania ou América Latina e Caribe. A tarefa de IA na produção "
                "de conteúdo foi introduzida posteriormente e requer amostra item a item própria."
            ),
        },
        "summary": {
            "entities": len(entries),
            "language_groups": sorted({entry.language_group for entry in entries}),
            "geographic_groups": sorted({entry.geographic_group for entry in entries}),
            "analytical_strata": sorted({entry.analytical_stratum for entry in entries}),
            "tasks": list(INITIAL_VALIDATION_TASKS),
        },
        "entries": [entry.to_dict() for entry in entries],
    }
