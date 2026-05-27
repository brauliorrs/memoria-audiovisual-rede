from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import OUTPUT_DIR
from .europe_closure import (
    EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    merge_existing_excluded_units,
)
from .european_aggregators import classify_probe_access_status, detect_js_cookie_requirement
from .european_protocols import (
    FRANCEARCHIVES_PROTOCOL_COLUMNS,
    detect_js_redirect,
    fetch_protocol_probe,
    utcnow_iso,
)


IBERARCHIVOS_PROTOCOL_FILENAME = "observatorio_protocolo_iberarchivos.csv"
IBERARCHIVOS_PROTOCOL_RULE_VERSION = "2026-05-iberarchivos-protocol-v1"
IBERARCHIVOS_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS

IBERARCHIVOS_AUDIOVISUAL_TERMS = (
    "audiovisual",
    "audiovisuales",
    "film",
    "fílmico",
    "video",
    "vídeo",
)


@dataclass(frozen=True)
class IberarchivosProbe:
    probe: str
    probe_label: str
    url: str
    evidence_signal: str
    methodological_note: str


IBERARCHIVOS_PROTOCOL_PROBES = [
    IberarchivosProbe(
        probe="observatory_home",
        probe_label="Observatório Iberoamericano de Archivos",
        url="https://iberarchivos.org/observatorio/",
        evidence_signal="policy_observatory",
        methodological_note="Verifica se a unidade opera como observatório de políticas arquivísticas.",
    ),
    IberarchivosProbe(
        probe="data_center",
        probe_label="Centro de dados do observatório",
        url="https://iberarchivos.org/observatorio/centro-de-datos/",
        evidence_signal="policy_data_center",
        methodological_note="Verifica se há camada de dados, indicadores ou registros coletáveis de acervo.",
    ),
    IberarchivosProbe(
        probe="site_search_audiovisual",
        probe_label="Busca pública por audiovisual",
        url="https://iberarchivos.org/?s=audiovisual",
        evidence_signal="public_search",
        methodological_note="Testa sinais audiovisuais contextuais sem tratar notícias ou projetos como corpus.",
    ),
    IberarchivosProbe(
        probe="site_search_video",
        probe_label="Busca pública por video",
        url="https://iberarchivos.org/?s=video",
        evidence_signal="public_search",
        methodological_note="Testa sinais de vídeo na superfície pública do site.",
    ),
    IberarchivosProbe(
        probe="wordpress_search_audiovisual",
        probe_label="Índice WordPress por audiovisual",
        url="https://iberarchivos.org/wp-json/wp/v2/search?search=audiovisual&per_page=5",
        evidence_signal="wordpress_search",
        methodological_note="Verifica se há índice estruturado do site, sem confundi-lo com API de acervo audiovisual.",
    ),
]


def _detected_terms(text):
    normalized = str(text or "").lower()
    return sorted({term for term in IBERARCHIVOS_AUDIOVISUAL_TERMS if term in normalized})


def _build_iberarchivos_protocol_conclusion(probe, access_status, detected_terms):
    if access_status != "acessivel":
        return (
            "rota_indisponivel_na_sondagem_simples",
            "retestar_sem_promover_a_corpus_ativo",
        )

    if probe.evidence_signal in {"policy_observatory", "policy_data_center"}:
        return (
            "observatorio_de_politicas_confirmado_sem_catalogo_audiovisual_coletavel",
            "manter_como_fonte_de_radar_e_nao_como_corpus",
        )

    if detected_terms:
        return (
            "sinais_audiovisuais_contextuais_detectados_sem_rota_de_acervo",
            "usar_para_descobrir_instituicoes_e_projetos_sem_ingestao_de_corpus",
        )

    return (
        "rota_acessivel_sem_sinal_audiovisual_suficiente",
        "manter_em_monitoramento_estrategico",
    )


def _build_iberarchivos_protocol_row(probe, evaluated_at, fetcher=fetch_protocol_probe):
    fetched = fetcher(probe.url, "GET")
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    terms = _detected_terms(text)
    conclusion, next_step = _build_iberarchivos_protocol_conclusion(probe, access_status, terms)
    return {
        "code": "iberarchivos",
        "label": "Iberarchivos / Observatorio Iberoamericano de Archivos",
        "probe": probe.probe,
        "probe_label": probe.probe_label,
        "method": "GET",
        "url": probe.url,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", probe.url),
        "content_type": fetched.get("content_type", ""),
        "content_length": fetched.get("content_length", ""),
        "access_status": access_status,
        "evidence_signal": probe.evidence_signal,
        "observed_value": "; ".join(terms) if terms else access_status,
        "protocol_conclusion": conclusion,
        "next_step": next_step,
        "methodological_note": probe.methodological_note,
        "evaluated_at": evaluated_at,
        "rule_version": IBERARCHIVOS_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_iberarchivos_protocol_probe(fetcher=fetch_protocol_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_iberarchivos_protocol_row(probe, evaluated_at, fetcher=fetcher)
        for probe in IBERARCHIVOS_PROTOCOL_PROBES
    ]
    return pd.DataFrame(rows, columns=IBERARCHIVOS_PROTOCOL_COLUMNS)


def build_iberarchivos_non_incorporated_register(protocol_df):
    accessible_total = 0
    audiovisual_hits_total = 0
    if protocol_df is not None and not protocol_df.empty:
        accessible_total = int((protocol_df["access_status"].astype(str) == "acessivel").sum())
        audiovisual_hits_total = int(
            protocol_df["observed_value"].astype(str).str.contains("audiovisual|video", case=False).sum()
        )

    return pd.DataFrame(
        [
            {
                "unit_code": "iberarchivos",
                "unit_label": "Iberarchivos / Observatorio Iberoamericano de Archivos",
                "unit_type": "fonte_de_radar",
                "territorial_scope": "rede ibero-americana",
                "public_status": "Identificada como fonte estratégica, mas não incluída no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo no MVP",
                "negative_reason": (
                    "O Iberarchivos é um observatório de políticas e cooperação arquivística. A sondagem "
                    "localizou sinais audiovisuais contextuais, mas não uma rota de registros audiovisuais "
                    "comparável aos corpora ativos."
                ),
                "collection_route_attempted": (
                    "Página do observatório, centro de dados, buscas públicas por termos audiovisuais "
                    "e índice WordPress do site."
                ),
                "attempt_summary": (
                    f"{accessible_total} sondagens acessíveis; {audiovisual_hits_total} com sinais "
                    "audiovisuais contextuais. Os sinais aparecem como projetos, notícias ou referências, "
                    "não como catálogo de vídeos ou metadados de acervo audiovisual."
                ),
                "methodological_explanation": (
                    "A unidade permanece no radar porque ajuda a descobrir instituições, políticas e "
                    "projetos ibero-americanos. Ela não entra como corpus para preservar a separação entre "
                    "fonte de curadoria e agregador de registros audiovisuais."
                ),
                "evidence_status": "fonte_de_radar_com_sinais_audiovisuais_contextuais",
                "protocol_status": "protocolo_confirma_fonte_estrategica_sem_corpus_coletavel",
                "next_step": "usar_como_fonte_de_descoberta_e_reavaliar_se_surgir_api_ou_catalogo_de_acervo",
                "blocks_expansion": False,
                "rule_version": IBERARCHIVOS_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_iberarchivos_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_protocol_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_iberarchivos_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(
        output_dir / IBERARCHIVOS_PROTOCOL_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_iberarchivos_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(
        output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
        index=False,
        encoding="utf-8-sig",
    )
    return protocol_df


__all__ = [
    "IBERARCHIVOS_PROTOCOL_COLUMNS",
    "IBERARCHIVOS_PROTOCOL_FILENAME",
    "IBERARCHIVOS_PROTOCOL_PROBES",
    "IBERARCHIVOS_PROTOCOL_RULE_VERSION",
    "build_iberarchivos_non_incorporated_register",
    "build_iberarchivos_protocol_probe",
    "write_iberarchivos_protocol_probe",
]
