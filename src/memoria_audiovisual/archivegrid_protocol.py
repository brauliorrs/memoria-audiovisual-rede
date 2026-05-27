from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import OUTPUT_DIR
from .europe_closure import (
    EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
)
from .european_aggregators import classify_probe_access_status, detect_js_cookie_requirement
from .european_protocols import (
    FRANCEARCHIVES_PROTOCOL_COLUMNS,
    detect_js_redirect,
    fetch_protocol_probe,
    utcnow_iso,
)


ARCHIVEGRID_PROTOCOL_FILENAME = "observatorio_protocolo_archivegrid.csv"
ARCHIVEGRID_PROTOCOL_RULE_VERSION = "2026-05-archivegrid-protocol-v1"

ARCHIVEGRID_HOME_URL = "https://researchworks.oclc.org/archivegrid/"
ARCHIVEGRID_ABOUT_URL = "https://researchworks.oclc.org/archivegrid/about/"
ARCHIVEGRID_SEARCH_FILM_URL = "https://researchworks.oclc.org/archivegrid/?q=film"
ARCHIVEGRID_SEARCH_VIDEO_URL = "https://researchworks.oclc.org/archivegrid/?q=video"
ARCHIVEGRID_SEARCH_AUDIOVISUAL_URL = "https://researchworks.oclc.org/archivegrid/?q=audiovisual"
ARCHIVEGRID_API_CANDIDATE_URL = "https://researchworks.oclc.org/archivegrid/api"
ARCHIVEGRID_API_SEARCH_CANDIDATE_URL = "https://researchworks.oclc.org/archivegrid/api/search?q=film"
ARCHIVEGRID_OCLC_REFERENCE_URL = "https://www.oclc.org/research/areas/research-collections/archivegrid.html"

ARCHIVEGRID_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS


@dataclass(frozen=True)
class ArchiveGridProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    methodological_note: str


ARCHIVEGRID_PROTOCOL_PROBES = [
    ArchiveGridProbe(
        probe="home_page",
        probe_label="Página inicial do ArchiveGrid",
        method="GET",
        url=ARCHIVEGRID_HOME_URL,
        methodological_note="Verifica se a superfície pública principal responde por requisição simples.",
    ),
    ArchiveGridProbe(
        probe="about_page",
        probe_label="Página pública sobre o ArchiveGrid",
        method="GET",
        url=ARCHIVEGRID_ABOUT_URL,
        methodological_note="Verifica a página pública que descreve o escopo e a composição do ArchiveGrid.",
    ),
    ArchiveGridProbe(
        probe="search_film",
        probe_label="Busca pública por film",
        method="GET",
        url=ARCHIVEGRID_SEARCH_FILM_URL,
        methodological_note="Testa uma busca audiovisual mínima sem tentar coleta em massa.",
    ),
    ArchiveGridProbe(
        probe="search_video",
        probe_label="Busca pública por video",
        method="GET",
        url=ARCHIVEGRID_SEARCH_VIDEO_URL,
        methodological_note="Testa a visibilidade de registros potencialmente audiovisuais.",
    ),
    ArchiveGridProbe(
        probe="search_audiovisual",
        probe_label="Busca pública por audiovisual",
        method="GET",
        url=ARCHIVEGRID_SEARCH_AUDIOVISUAL_URL,
        methodological_note="Testa o vocabulário direto do recorte audiovisual do organismo.",
    ),
    ArchiveGridProbe(
        probe="api_candidate",
        probe_label="Rota candidata /api",
        method="GET",
        url=ARCHIVEGRID_API_CANDIDATE_URL,
        methodological_note="Testa se existe rota pública simples de API no domínio do ArchiveGrid.",
    ),
    ArchiveGridProbe(
        probe="api_search_candidate",
        probe_label="Rota candidata /api/search",
        method="GET",
        url=ARCHIVEGRID_API_SEARCH_CANDIDATE_URL,
        methodological_note="Testa se há endpoint público de busca estruturada por parâmetro.",
    ),
    ArchiveGridProbe(
        probe="oclc_reference_page",
        probe_label="Página institucional da OCLC sobre ArchiveGrid",
        method="GET",
        url=ARCHIVEGRID_OCLC_REFERENCE_URL,
        methodological_note="Confirma a relevância institucional do agregador sem tratar a página como rota de coleta.",
    ),
]


def _build_archivegrid_protocol_conclusion(probe, access_status, text):
    normalized_text = str(text or "").lower()
    if access_status == "acessivel":
        if probe.probe == "oclc_reference_page" and "archivegrid" in normalized_text:
            return (
                "referencia_institucional_confirma_agregador_mundial",
                "usar_como_evidencia_metodologica_sem_promover_a_corpus",
            )
        if probe.probe.startswith("search_"):
            return (
                "busca_publica_acessivel_a_validar",
                "prototipar_parseamento_controlado_antes_de_incorporar",
            )
        return "rota_publica_acessivel", "validar_se_a_rota_sustenta_coleta_comparavel"

    if access_status in {"bloqueado_por_js_ou_cookies", "restrito_ou_bloqueado"}:
        if probe.probe.startswith("api"):
            return (
                "api_nao_documentada_ou_bloqueada_na_sondagem_simples",
                "buscar_documentacao_oficial_ou_contato_tecnico_antes_de_ingestao",
            )
        if probe.probe.startswith("search_"):
            return (
                "busca_publica_bloqueada_na_sondagem_simples",
                "validar_por_navegacao_controlada_sem_incorporar_ao_corpus",
            )
        return (
            "superficie_publica_bloqueada_na_sondagem_simples",
            "manter_como_unidade_identificada_sem_corpus_ativo",
        )

    if access_status == "falha_tecnica":
        return "rota_com_falha_tecnica_na_rodada", "retestar_em_rodada_posterior"
    return "rota_sem_confirmacao_estavel", "retestar_antes_de_qualquer_incorporacao"


def _build_archivegrid_protocol_row(probe, evaluated_at, fetcher=fetch_protocol_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    if probe.probe.startswith("api"):
        evidence_signal = "api_candidate"
    elif probe.probe.startswith("search_"):
        evidence_signal = "public_search"
    elif probe.probe == "oclc_reference_page":
        evidence_signal = "institutional_reference"
    else:
        evidence_signal = "page_access"

    protocol_conclusion, next_step = _build_archivegrid_protocol_conclusion(probe, access_status, text)
    return {
        "code": "archivegrid",
        "label": "ArchiveGrid",
        "probe": probe.probe,
        "probe_label": probe.probe_label,
        "method": probe.method,
        "url": probe.url,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", probe.url),
        "content_type": fetched.get("content_type", ""),
        "content_length": fetched.get("content_length", ""),
        "access_status": access_status,
        "evidence_signal": evidence_signal,
        "observed_value": access_status,
        "protocol_conclusion": protocol_conclusion,
        "next_step": next_step,
        "methodological_note": probe.methodological_note,
        "evaluated_at": evaluated_at,
        "rule_version": ARCHIVEGRID_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_archivegrid_protocol_probe(fetcher=fetch_protocol_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_archivegrid_protocol_row(probe, evaluated_at, fetcher=fetcher)
        for probe in ARCHIVEGRID_PROTOCOL_PROBES
    ]
    return pd.DataFrame(rows, columns=ARCHIVEGRID_PROTOCOL_COLUMNS)


def build_archivegrid_non_incorporated_register(protocol_df):
    blocked_total = 0
    accessible_reference = False
    if protocol_df is not None and not protocol_df.empty:
        blocked_total = int(
            protocol_df["access_status"].astype(str).isin(
                {"bloqueado_por_js_ou_cookies", "restrito_ou_bloqueado"}
            ).sum()
        )
        accessible_reference = bool(
            (
                (protocol_df["probe"].astype(str) == "oclc_reference_page")
                & (protocol_df["access_status"].astype(str) == "acessivel")
            ).any()
        )

    attempt_summary = (
        "Foram testadas a página inicial, a página sobre o ArchiveGrid, buscas públicas por "
        "`film`, `video` e `audiovisual`, além de rotas candidatas `/api` e `/api/search`. "
        f"{blocked_total} sondagens retornaram bloqueio, restrição ou desafio por navegação. "
    )
    if accessible_reference:
        attempt_summary += "A página institucional da OCLC confirmou a relevância do agregador."
    else:
        attempt_summary += "A referência institucional também precisa ser reavaliada em rodada posterior."

    return pd.DataFrame(
        [
            {
                "unit_code": "archivegrid",
                "unit_label": "ArchiveGrid",
                "unit_type": "agregador_candidato",
                "territorial_scope": "agregador mundial",
                "public_status": "Identificada, mas não incluída no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo no MVP",
                "negative_reason": (
                    "O ArchiveGrid é metodologicamente central como agregador mundial, mas a "
                    "sondagem leve não encontrou rota pública estável de coleta ou API documentada "
                    "para triagem audiovisual comparável."
                ),
                "collection_route_attempted": (
                    "Página pública, busca por termos audiovisuais, rotas candidatas de API e "
                    "referência institucional da OCLC."
                ),
                "attempt_summary": attempt_summary,
                "methodological_explanation": (
                    "A negativa é técnica e metodológica: a relevância do agregador foi reconhecida, "
                    "mas a coleta automatizada não pode depender de superfície bloqueada ou de rota "
                    "não documentada. Isso não equivale a ausência de acervo audiovisual no ArchiveGrid."
                ),
                "evidence_status": "agregador_mundial_relevante_sem_rota_publica_estavel_de_coleta",
                "protocol_status": "prototipo_leve_indica_bloqueio_em_busca_publica_e_api_nao_documentada",
                "next_step": "identificar_api_exportacao_parceria_ou_rota_controlada_antes_de_incorporar",
                "blocks_expansion": False,
                "rule_version": ARCHIVEGRID_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def merge_non_incorporated_units(output_dir, new_units_df):
    output_path = Path(output_dir) / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
    if output_path.exists():
        existing_df = pd.read_csv(output_path)
    else:
        existing_df = pd.DataFrame(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)

    merged_df = pd.concat([existing_df, new_units_df], ignore_index=True)
    return (
        merged_df.drop_duplicates(subset=["unit_code"], keep="last")
        .reindex(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)
        .sort_values("unit_label")
        .reset_index(drop=True)
    )


def write_archivegrid_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_protocol_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_archivegrid_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(
        output_dir / ARCHIVEGRID_PROTOCOL_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    excluded_df = merge_non_incorporated_units(
        output_dir,
        build_archivegrid_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(
        output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    return protocol_df


__all__ = [
    "ARCHIVEGRID_PROTOCOL_COLUMNS",
    "ARCHIVEGRID_PROTOCOL_FILENAME",
    "ARCHIVEGRID_PROTOCOL_PROBES",
    "ARCHIVEGRID_PROTOCOL_RULE_VERSION",
    "build_archivegrid_non_incorporated_register",
    "build_archivegrid_protocol_probe",
    "merge_non_incorporated_units",
    "write_archivegrid_protocol_probe",
]
