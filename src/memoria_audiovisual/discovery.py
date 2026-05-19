from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import OUTPUT_DIR
from .corpora import CORPORA, CORPUS_CATEGORIES, OBSERVATORY_PROFILE


DISCOVERY_REGISTRY_FILENAME = "observatorio_candidatos_descoberta.csv"
DISCOVERY_QUEUE_FILENAME = "observatorio_fila_expansao.csv"
DISCOVERY_SUMMARY_FILENAME = "observatorio_resumo_fila_expansao.csv"
DISCOVERY_RULE_VERSION = "2026-05-organismo-v1"
EUROPE_BASE_AGGREGATOR_CODE = "ape"
EUROPE_BASE_INCLUDED_INSTITUTION_DECISION = "lacuna_ou_excecao_na_base_europa"
EUROPEAN_GEOGRAPHIC_MARKERS = {
    "alemanha",
    "belgica",
    "espanha",
    "europa",
    "franca",
    "frança",
    "italia",
    "itália",
    "portugal",
    "reino unido",
}

DISCOVERY_COLUMNS = [
    "code",
    "label",
    "short_label",
    "category_code",
    "category_label",
    "entity_level",
    "coverage_level",
    "scope",
    "geographic_scope",
    "audiovisual_relevance",
    "methodological_fit",
    "discovery_origin",
    "source_url",
    "already_covered_by_active_aggregator",
    "organism_status",
    "automatic_decision",
    "automatic_priority",
    "automatic_reason",
    "next_step",
    "rule_version",
]

DISCOVERY_BASELINE_CANDIDATES = [
    {
        "code": "archivegrid",
        "label": "ArchiveGrid",
        "short_label": "ArchiveGrid",
        "category_code": "aggregator",
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador mundial",
        "scope": "portal geral de arquivos",
        "geographic_scope": "mundial",
        "audiovisual_relevance": "fonte geral com potencial audiovisual",
        "methodological_fit": "muito_alto",
        "discovery_origin": "linha de base metodológica do organismo",
        "source_url": "https://researchworks.oclc.org/archivegrid/about/",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "archives-hub",
        "label": "Archives Hub",
        "short_label": "Archives Hub",
        "category_code": "aggregator",
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador nacional",
        "scope": "portal geral de arquivos",
        "geographic_scope": "Reino Unido",
        "audiovisual_relevance": "fonte geral com potencial audiovisual",
        "methodological_fit": "alto",
        "discovery_origin": "linha de base metodológica do organismo",
        "source_url": "https://archiveshub.jisc.ac.uk/",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "francearchives",
        "label": "FranceArchives",
        "short_label": "FranceArchives",
        "category_code": "aggregator",
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador nacional",
        "scope": "portal geral de arquivos",
        "geographic_scope": "França",
        "audiovisual_relevance": "fonte geral com potencial audiovisual",
        "methodological_fit": "alto",
        "discovery_origin": "linha de base metodológica do organismo",
        "source_url": "https://francearchives.gouv.fr/",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "pares",
        "label": "PARES",
        "short_label": "PARES",
        "category_code": "aggregator",
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador nacional",
        "scope": "portal geral de arquivos",
        "geographic_scope": "Espanha",
        "audiovisual_relevance": "fonte geral com potencial audiovisual",
        "methodological_fit": "alto",
        "discovery_origin": "linha de base metodológica do organismo",
        "source_url": "https://pares.cultura.gob.es/",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "euscreen",
        "label": "EUscreen",
        "short_label": "EUscreen",
        "category_code": "aggregator",
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador continental",
        "scope": "agregador temático audiovisual",
        "geographic_scope": "Europa",
        "audiovisual_relevance": "especializado em audiovisual",
        "methodological_fit": "muito_alto",
        "discovery_origin": "linha de base metodológica do organismo",
        "source_url": "https://euscreen.eu/about/",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "european-film-gateway",
        "label": "European Film Gateway",
        "short_label": "EFG",
        "category_code": "aggregator",
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador continental",
        "scope": "agregador temático cinematográfico/audiovisual",
        "geographic_scope": "Europa",
        "audiovisual_relevance": "especializado em audiovisual",
        "methodological_fit": "muito_alto",
        "discovery_origin": "Europa 1.5 - fechamento empírico audiovisual",
        "source_url": "https://www.europeanfilmgateway.eu/",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "europeana",
        "label": "Europeana",
        "short_label": "Europeana",
        "category_code": "aggregator",
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador continental",
        "scope": "agregador cultural digital com superfícies audiovisuais",
        "geographic_scope": "Europa",
        "audiovisual_relevance": "fonte geral com potencial audiovisual",
        "methodological_fit": "alto",
        "discovery_origin": "Europa 1.5 - agregador europeu amplo a protocolar",
        "source_url": "https://www.europeana.eu/",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "ina-gap",
        "label": "Institut national de l'audiovisuel",
        "short_label": "INA",
        "category_code": "institution",
        "entity_level": "instituição custodial",
        "coverage_level": "instituição individual",
        "scope": "arquivo especializado em audiovisual",
        "geographic_scope": "França / Europa",
        "audiovisual_relevance": "especializado em audiovisual",
        "methodological_fit": "muito_alto",
        "discovery_origin": "lacuna europeia estratégica identificada após a base APE",
        "source_url": "https://www.ina.fr/institut-national-audiovisuel",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "aapb",
        "label": "American Archive of Public Broadcasting",
        "short_label": "AAPB",
        "category_code": "aggregator",
        "entity_level": "infraestrutura agregadora",
        "coverage_level": "agregador nacional",
        "scope": "agregador temático audiovisual",
        "geographic_scope": "Estados Unidos",
        "audiovisual_relevance": "especializado em audiovisual",
        "methodological_fit": "muito_alto",
        "discovery_origin": "linha de base metodológica do organismo",
        "source_url": "https://americanarchive.org/faq",
        "already_covered_by_active_aggregator": False,
    },
    {
        "code": "iberarchivos",
        "label": "Iberarchivos / Observatorio Iberoamericano de Archivos",
        "short_label": "Iberarchivos",
        "category_code": "aggregator",
        "entity_level": "rede/observatorio de políticas arquivísticas",
        "coverage_level": "rede ibero-americana",
        "scope": "observatório de políticas públicas arquivísticas",
        "geographic_scope": "Iberoamérica",
        "audiovisual_relevance": "fonte geral com potencial audiovisual indireto",
        "methodological_fit": "medio",
        "discovery_origin": "radar audiovisual mundial - sugestão de curadoria",
        "source_url": "https://iberarchivos.org/observatorio/",
        "already_covered_by_active_aggregator": False,
    },
]


def _fit_score(value: str) -> int:
    mapping = {
        "muito_alto": 4,
        "alto": 3,
        "medio": 2,
        "baixo": 1,
    }
    return mapping.get(str(value).strip().lower(), 0)


def _is_european_institution_candidate(candidate: dict) -> bool:
    if str(candidate.get("category_code", "")).strip() != "institution":
        return False
    scope_parts = [
        candidate.get("geographic_scope", ""),
        candidate.get("coverage_level", ""),
        candidate.get("scope", ""),
        candidate.get("discovery_origin", ""),
    ]
    normalized_scope = " ".join(str(value).lower() for value in scope_parts)
    return any(marker in normalized_scope for marker in EUROPEAN_GEOGRAPHIC_MARKERS)


def _evaluate_candidate(candidate: dict, active_codes: set[str]) -> dict:
    code = str(candidate.get("code", "")).strip().lower()
    category_code = str(candidate.get("category_code", "")).strip()
    fit_score = _fit_score(candidate.get("methodological_fit", ""))
    audiovisual_relevance = str(candidate.get("audiovisual_relevance", "")).strip().lower()
    covered_by_aggregator = bool(candidate.get("already_covered_by_active_aggregator", False))

    if code in active_codes:
        return {
            "organism_status": "ativo",
            "automatic_decision": "ja_incorporado",
            "automatic_priority": 0,
            "automatic_reason": (
                "A unidade já integra o organismo e segue em atualização periódica."
            ),
            "next_step": "manter_no_ciclo_mensal",
        }

    if category_code == "aggregator":
        if "observat" in str(candidate.get("scope", "")).strip().lower():
            return {
                "organism_status": "referencia",
                "automatic_decision": "monitoramento_estrategico",
                "automatic_priority": 5,
                "automatic_reason": (
                    "A unidade funciona como radar de políticas e instituições arquivísticas, "
                    "mas ainda não apresenta rota comparável para ingestão de acervo audiovisual."
                ),
                "next_step": "monitorar_como_fonte_de_descoberta_sem_pipeline_imediato",
            }
        if str(candidate.get("code", "")).strip().lower() in {"euscreen", "european-film-gateway"}:
            return {
                "organism_status": "candidato",
                "automatic_decision": "fechamento_europa_agregador_audiovisual",
                "automatic_priority": 1,
                "automatic_reason": (
                    "É um agregador audiovisual europeu aderente para complementar o APE "
                    "no fechamento metodológico da Europa."
                ),
                "next_step": "preparar_pipeline_do_agregador_europeu_audiovisual",
            }
        if str(candidate.get("code", "")).strip().lower() == "europeana":
            return {
                "organism_status": "candidato",
                "automatic_decision": "fechamento_europa_agregador_supranacional",
                "automatic_priority": 2,
                "automatic_reason": (
                    "É um agregador europeu amplo e precisa ser avaliado antes de abrir outro continente, "
                    "ainda que não seja arquivo audiovisual especializado."
                ),
                "next_step": "protocolar_europeana_antes_da_expansao_continental",
            }
        if fit_score >= 4:
            return {
                "organism_status": "candidato",
                "automatic_decision": "prioridade_imediata_etapa_1",
                "automatic_priority": 4,
                "automatic_reason": (
                    "É um agregador com forte aderência metodológica ao organismo e deve entrar antes das instituições avulsas."
                ),
                "next_step": "preparar_pipeline_do_agregador",
            }
        if fit_score >= 3:
            return {
                "organism_status": "candidato",
                "automatic_decision": "fechamento_europa_agregador_nacional",
                "automatic_priority": 2,
                "automatic_reason": (
                    "É um agregador europeu nacional relevante para completar a leitura regional após o APE."
                ),
                "next_step": "preparar_apos_agregador_audiovisual_europeu",
            }
        return {
            "organism_status": "referencia",
            "automatic_decision": "fora_do_recorte_atual",
            "automatic_priority": 9,
            "automatic_reason": (
                "A unidade não apresenta aderência metodológica suficiente ao desenho atual do organismo."
            ),
            "next_step": "reavaliar_se_o_protocolo_mudar",
        }

    if covered_by_aggregator:
        return {
            "organism_status": "coberto",
            "automatic_decision": "coberto_por_agregador_ativo",
            "automatic_priority": 7,
            "automatic_reason": (
                "A instituição aparece coberta por agregadores ativos, então sua entrada autônoma não é prioritária nesta etapa."
            ),
            "next_step": "aguardar_lacunas_identificadas_pelos_agregadores",
        }

    if _is_european_institution_candidate(candidate):
        return {
            "organism_status": "candidato",
            "automatic_decision": EUROPE_BASE_INCLUDED_INSTITUTION_DECISION,
            "automatic_priority": 3,
            "automatic_reason": (
                "A instituição pertence ao espaço europeu, mas entra como lacuna ou exceção "
                "a ser trabalhada separadamente da base agregadora do APE."
            ),
            "next_step": "verificar_relacao_com_o_ape_antes_de_incorporar",
        }

    if "audiovisual" in audiovisual_relevance and fit_score >= 3:
        return {
            "organism_status": "candidato",
            "automatic_decision": "aguarda_etapa_2",
            "automatic_priority": 3,
            "automatic_reason": (
                "A instituição é relevante para o audiovisual, mas a regra do organismo prioriza primeiro os agregadores."
            ),
            "next_step": "avaliar_apos_ampliar_agregadores",
        }

    return {
        "organism_status": "referencia",
        "automatic_decision": "monitoramento_estrategico",
        "automatic_priority": 5,
        "automatic_reason": (
            "A unidade permanece como referência metodológica, mas não é a próxima prioridade de incorporação."
        ),
        "next_step": "monitorar_sem_ingestao_imediata",
    }


def build_discovery_registry():
    active_codes = {definition["code"] for definition in CORPORA.values()}
    rows = []

    for corpus_def in CORPORA.values():
        category_def = CORPUS_CATEGORIES[corpus_def["category_code"]]
        evaluation = _evaluate_candidate(corpus_def, active_codes)
        rows.append(
            {
                "code": corpus_def["code"],
                "label": corpus_def["label"],
                "short_label": corpus_def["short_label"],
                "category_code": corpus_def["category_code"],
                "category_label": category_def["label"],
                "entity_level": corpus_def["entity_level"],
                "coverage_level": corpus_def["coverage_level"],
                "scope": corpus_def["scope"],
                "geographic_scope": corpus_def["coverage_level"],
                "audiovisual_relevance": corpus_def.get("audiovisual_scope_note", ""),
                "methodological_fit": "ativo",
                "discovery_origin": "corpus já incorporado ao organismo",
                "source_url": corpus_def.get("source_url", ""),
                "already_covered_by_active_aggregator": False,
                "rule_version": DISCOVERY_RULE_VERSION,
                **evaluation,
            }
        )

    for candidate in DISCOVERY_BASELINE_CANDIDATES:
        if candidate["code"] in active_codes:
            continue
        category_def = CORPUS_CATEGORIES[candidate["category_code"]]
        evaluation = _evaluate_candidate(candidate, active_codes)
        rows.append(
            {
                "code": candidate["code"],
                "label": candidate["label"],
                "short_label": candidate["short_label"],
                "category_code": candidate["category_code"],
                "category_label": category_def["label"],
                "entity_level": candidate["entity_level"],
                "coverage_level": candidate["coverage_level"],
                "scope": candidate["scope"],
                "geographic_scope": candidate["geographic_scope"],
                "audiovisual_relevance": candidate["audiovisual_relevance"],
                "methodological_fit": candidate["methodological_fit"],
                "discovery_origin": candidate["discovery_origin"],
                "source_url": candidate["source_url"],
                "already_covered_by_active_aggregator": candidate["already_covered_by_active_aggregator"],
                "rule_version": DISCOVERY_RULE_VERSION,
                **evaluation,
            }
        )

    registry_df = pd.DataFrame(rows, columns=DISCOVERY_COLUMNS)
    return registry_df.sort_values(
        ["automatic_priority", "category_label", "short_label"],
        ascending=[True, True, True],
    ).reset_index(drop=True)


def build_expansion_queue(registry_df: pd.DataFrame) -> pd.DataFrame:
    if registry_df is None or registry_df.empty:
        return pd.DataFrame(columns=DISCOVERY_COLUMNS)
    queue_df = registry_df.loc[
        registry_df["automatic_decision"].isin(
            {
                "prioridade_imediata_etapa_1",
                "fechamento_europa_agregador_audiovisual",
                "fechamento_europa_agregador_supranacional",
                "fechamento_europa_agregador_nacional",
                "monitoramento_estrategico",
                "aguarda_etapa_2",
                EUROPE_BASE_INCLUDED_INSTITUTION_DECISION,
            }
        )
    ].copy()
    return queue_df.sort_values(
        ["automatic_priority", "category_label", "short_label"],
        ascending=[True, True, True],
    ).reset_index(drop=True)


def build_discovery_summary(registry_df: pd.DataFrame) -> pd.DataFrame:
    if registry_df is None or registry_df.empty:
        return pd.DataFrame(columns=["categoria_analitica", "decisao_automatica", "total"])
    summary_df = (
        registry_df.groupby(["category_label", "automatic_decision"], dropna=False)
        .size()
        .reset_index(name="total")
        .rename(
            columns={
                "category_label": "categoria_analitica",
                "automatic_decision": "decisao_automatica",
            }
        )
    )
    return summary_df.sort_values(
        ["categoria_analitica", "total", "decisao_automatica"],
        ascending=[True, False, True],
    ).reset_index(drop=True)


def write_discovery_outputs(output_dir: Path = OUTPUT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_df = build_discovery_registry()
    queue_df = build_expansion_queue(registry_df)
    summary_df = build_discovery_summary(registry_df)

    registry_df.to_csv(
        output_dir / DISCOVERY_REGISTRY_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    queue_df.to_csv(
        output_dir / DISCOVERY_QUEUE_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    summary_df.to_csv(
        output_dir / DISCOVERY_SUMMARY_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )

    return {
        "registry": registry_df,
        "queue": queue_df,
        "summary": summary_df,
    }


__all__ = [
    "DISCOVERY_BASELINE_CANDIDATES",
    "DISCOVERY_COLUMNS",
    "DISCOVERY_QUEUE_FILENAME",
    "DISCOVERY_REGISTRY_FILENAME",
    "DISCOVERY_RULE_VERSION",
    "DISCOVERY_SUMMARY_FILENAME",
    "EUROPE_BASE_INCLUDED_INSTITUTION_DECISION",
    "build_discovery_registry",
    "build_discovery_summary",
    "build_expansion_queue",
    "write_discovery_outputs",
]
