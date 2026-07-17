from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import HEADERS, OUTPUT_DIR
from .europe_closure import (
    EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    merge_existing_excluded_units,
)
from .european_aggregators import classify_probe_access_status, detect_js_cookie_requirement
from .european_protocols import FRANCEARCHIVES_PROTOCOL_COLUMNS, detect_js_redirect, utcnow_iso


CINEMATHEQUE_LUXEMBOURG_PROTOCOL_FILENAME = "observatorio_protocolo_cinematheque_luxembourg.csv"
CINEMATHEQUE_LUXEMBOURG_PROTOCOL_RULE_VERSION = "2026-06-cinematheque-luxembourg-protocol-v1"
CINEMATHEQUE_LUXEMBOURG_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
CINEMATHEQUE_LUXEMBOURG_ACCESS_CATEGORY = (
    "arquivo_filmico_com_acervo_preservado_e_programacao_publica_sem_catalogo_publico_de_video"
)

CINEMATHEQUE_LUXEMBOURG_HOME_URL = "https://www.cinematheque.lu/"
CINEMATHEQUE_LUXEMBOURG_ARCHIVES_URL = "https://www.cinematheque.lu/fr/archives-collections"
CINEMATHEQUE_LUXEMBOURG_PROGRAMME_URL = "https://www.cinematheque.lu/fr/programme"
CINEMATHEQUE_LUXEMBOURG_HISTORY_URL = "https://www.cinematheque.lu/fr/la-cinematheque"
CINEMATHEQUE_LUXEMBOURG_FILM_API_URL = "https://www.cinematheque.lu/fr/api/film"
CINEMATHEQUE_LUXEMBOURG_SEARCH_URL = "https://www.cinematheque.lu/fr/search/node?keys=archives"
CINEMATHEQUE_LUXEMBOURG_VDL_URL = (
    "https://www.vdl.lu/fr/visiter/art-et-culture/lieux-culturels/cinema/cinematheque"
)


@dataclass(frozen=True)
class CinemathequeLuxembourgProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


CINEMATHEQUE_LUXEMBOURG_PROTOCOL_PROBES = [
    CinemathequeLuxembourgProbe(
        probe="official_home",
        probe_label="Site oficial da Cinémathèque de la Ville de Luxembourg",
        method="GET",
        url=CINEMATHEQUE_LUXEMBOURG_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Confirma a presença institucional sem tratar a home como catálogo audiovisual.",
    ),
    CinemathequeLuxembourgProbe(
        probe="archives_collections",
        probe_label="Página oficial Archives & collections",
        method="GET",
        url=CINEMATHEQUE_LUXEMBOURG_ARCHIVES_URL,
        evidence_signal="archive_collection_policy",
        methodological_note="Verifica se a página de coleções expõe catálogo público de vídeos de acervo.",
    ),
    CinemathequeLuxembourgProbe(
        probe="programme",
        probe_label="Página Programme",
        method="GET",
        url=CINEMATHEQUE_LUXEMBOURG_PROGRAMME_URL,
        evidence_signal="screening_programme",
        methodological_note="Distingue programação de sessões de cinema de corpus digital de acervo.",
    ),
    CinemathequeLuxembourgProbe(
        probe="history_page",
        probe_label="Página La Cinémathèque",
        method="GET",
        url=CINEMATHEQUE_LUXEMBOURG_HISTORY_URL,
        evidence_signal="institutional_history",
        methodological_note="Confirma o enquadramento FIAF e patrimonial sem promover a corpus coletável.",
    ),
    CinemathequeLuxembourgProbe(
        probe="film_api",
        probe_label="API pública /fr/api/film",
        method="GET",
        url=CINEMATHEQUE_LUXEMBOURG_FILM_API_URL,
        evidence_signal="programme_api",
        methodological_note="Testa se a API pública lista filmes de acervo ou apenas sessões/programação.",
    ),
    CinemathequeLuxembourgProbe(
        probe="site_search",
        probe_label="Busca pública do site",
        method="GET",
        url=CINEMATHEQUE_LUXEMBOURG_SEARCH_URL,
        evidence_signal="site_search",
        methodological_note="Testa se a busca institucional funciona como catálogo arquivístico de vídeos.",
    ),
    CinemathequeLuxembourgProbe(
        probe="municipal_page",
        probe_label="Página municipal VDL sobre a Cinémathèque",
        method="GET",
        url=CINEMATHEQUE_LUXEMBOURG_VDL_URL,
        evidence_signal="municipal_context",
        methodological_note="Verifica fonte municipal complementar sobre acervo e programação.",
    ),
]


def fetch_cinematheque_luxembourg_probe(url, method="GET", sample_bytes=524288):
    response = None
    error = ""
    try:
        response = requests.get(
            url,
            headers={
                **HEADERS,
                "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7",
            },
            timeout=(8, 14),
            allow_redirects=True,
        )
        response.encoding = response.encoding or response.apparent_encoding or "utf-8"
        text = response.text[:sample_bytes]
    except Exception as exc:
        text = ""
        error = str(exc)

    return {
        "http_status": response.status_code if response is not None else "",
        "final_url": response.url if response is not None else url,
        "content_type": response.headers.get("content-type", "") if response is not None else "",
        "content_length": response.headers.get("content-length", "") if response is not None else "",
        "text": text,
        "error": error,
    }


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _page_signals(content):
    raw = str(content or "")
    visible_text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    text = _clean_text(f"{visible_text} {raw}").lower()
    video_files = re.findall(r"https?://[^\"'\s<>]+?\.(?:mp4|m3u8|webm|mov|avi|m4v)", raw, flags=re.I)
    return {
        "official_identity": "cinémathèque de la ville de luxembourg" in text or "cinematheque.lu" in text,
        "archive_terms": any(term in text for term in ("archives", "collections", "préserver", "preserve", "fiaf")),
        "collection_counts": bool(re.search(r"\b20[ .]?0?38\b", text) or "copies de film" in text or "film prints" in text),
        "programme_terms": any(term in text for term in ("programme", "projection", "billetterie", "ticket", "séance")),
        "api_program_fields": all(
            term in text
            for term in ("projection_date", "projection_time", "ticket_url")
        ),
        "ticketing_terms": "utick" in text or "module=catalogue" in text,
        "site_search_terms": "rechercher" in text or "search" in text,
        "archive_catalog_terms": any(term in text for term in ("catalogue d'archives", "catalogue des archives", "online catalogue")),
        "video_files": len(video_files),
        "institutional_video_files": sum(
            1
            for url in video_files
            if any(marker in url.lower() for marker in ("frigo.mp4", "pellicule.mp4", "bg-video.mp4"))
        ),
        "video_embed_terms": any(term in raw.lower() for term in ("<video", "youtube.com/embed", "player.vimeo.com")),
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"identidade={'sim' if signals['official_identity'] else 'nao'}",
            f"arquivo={'sim' if signals['archive_terms'] else 'nao'}",
            f"contagens_acervo={'sim' if signals['collection_counts'] else 'nao'}",
            f"programacao={'sim' if signals['programme_terms'] else 'nao'}",
            f"api_programacao={'sim' if signals['api_program_fields'] else 'nao'}",
            f"bilheteria={'sim' if signals['ticketing_terms'] else 'nao'}",
            f"busca_site={'sim' if signals['site_search_terms'] else 'nao'}",
            f"catalogo_arquivistico_video={'sim' if signals['archive_catalog_terms'] else 'nao'}",
            f"arquivos_video={signals['video_files']}",
            f"videos_institucionais={signals['institutional_video_files']}",
            f"embed_video={'sim' if signals['video_embed_terms'] else 'nao'}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        return "rota_indisponivel_ou_instavel_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe == "site_search":
        return "busca_do_site_nao_equivale_a_catalogo_arquivistico", "nao_usar_busca_institucional_como_corpus"
    if probe.probe == "archives_collections" and signals.get("collection_counts"):
        return "acervo_filmico_confirmado_sem_catalogo_publico_de_video", "registrar_unidade_nao_incorporada_por_ausencia_de_rota_coletavel"
    if probe.probe == "film_api" and signals.get("api_program_fields"):
        return "api_publica_de_programacao_nao_equivale_a_catalogo_de_acervo", "nao_incorporar_sessoes_de_bilheteria_como_videos_de_acervo"
    if probe.probe == "official_home":
        return "site_oficial_contextual_sem_catalogo_publico_de_video", "manter_como_evidencia_institucional"
    if probe.probe == "history_page":
        return "historia_institucional_confirma_perfil_fiaf_sem_rota_coletavel", "manter_como_evidencia_contextual"
    if probe.probe == "programme" or signals.get("programme_terms") and signals.get("ticketing_terms"):
        return "programacao_e_bilheteria_nao_equivalem_a_corpus_audiovisual", "manter_como_contexto_institucional"
    if signals.get("video_files") and signals.get("institutional_video_files") == signals.get("video_files"):
        return "videos_institucionais_de_contexto_nao_equivalem_a_acervo", "nao_usar_clipes_de_fundo_como_corpus"
    if probe.probe == "municipal_page":
        return "fonte_municipal_confirma_acervo_sem_rota_coletavel", "manter_como_evidencia_contextual"
    if signals.get("archive_terms"):
        return "arquivo_filmico_confirmado_sem_rota_publica_de_video", "manter_fora_do_corpus_ativo_ate_haver_rota_coletavel"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_cinematheque_luxembourg_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    signals = _page_signals(text) if text else {}
    conclusion, next_step = _build_protocol_conclusion(probe, access_status, signals)
    return {
        "code": "fiaf-cinematheque-luxembourg",
        "label": "Cinémathèque de la Ville de Luxembourg",
        "probe": probe.probe,
        "probe_label": probe.probe_label,
        "method": probe.method,
        "url": probe.url,
        "http_status": fetched.get("http_status", ""),
        "final_url": fetched.get("final_url", probe.url),
        "content_type": fetched.get("content_type", ""),
        "content_length": fetched.get("content_length", ""),
        "access_status": access_status,
        "evidence_signal": probe.evidence_signal,
        "observed_value": _observed_value(signals, access_status),
        "protocol_conclusion": conclusion,
        "next_step": next_step,
        "methodological_note": probe.methodological_note,
        "evaluated_at": evaluated_at,
        "rule_version": CINEMATHEQUE_LUXEMBOURG_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_cinematheque_luxembourg_protocol_probe(fetcher=fetch_cinematheque_luxembourg_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_protocol_row(probe, evaluated_at, fetcher=fetcher)
        for probe in CINEMATHEQUE_LUXEMBOURG_PROTOCOL_PROBES
    ]
    return pd.DataFrame(rows, columns=CINEMATHEQUE_LUXEMBOURG_PROTOCOL_COLUMNS)


def build_cinematheque_luxembourg_non_incorporated_register(protocol_df):
    return pd.DataFrame(
        [
            {
                "unit_code": "fiaf-cinematheque-luxembourg",
                "unit_label": "Cinémathèque de la Ville de Luxembourg",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Luxemburgo",
                "access_category": CINEMATHEQUE_LUXEMBOURG_ACCESS_CATEGORY,
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A Cinémathèque de la Ville de Luxembourg é um arquivo fílmico confirmado, com acervo "
                    "preservado e programação pública. Porém, as rotas oficiais observadas não expõem um "
                    "catálogo público de vídeos de acervo. A API pública encontrada lista sessões, datas, "
                    "locais e bilheteria; os arquivos MP4 detectados são clipes institucionais de contexto."
                ),
                "collection_route_attempted": (
                    "Site oficial, página Archives & collections, página Programme, página La Cinémathèque, "
                    "API pública /fr/api/film, busca pública do site e página municipal da Ville de Luxembourg."
                ),
                "attempt_summary": (
                    "A página Archives & collections confirma a existência do acervo fílmico e suas contagens; "
                    "a API /fr/api/film respondeu em JSON, mas com campos de programação e bilheteria, como "
                    "projection_date, projection_time e ticket_url. Não foi localizada rota pública de catálogo "
                    "de vídeos de acervo materializável."
                ),
                "methodological_explanation": (
                    "A decisão não nega a existência nem a relevância do acervo. Ela apenas impede que programação "
                    "de sala, bilheteria, páginas institucionais ou clipes de fundo sejam tratados como corpus "
                    "digital de imagem em movimento. Para entrar no corpus ativo, a unidade precisa expor registros "
                    "públicos de vídeo de acervo ou metadados audiovisuais coletáveis de forma reprodutível."
                ),
                "evidence_status": "arquivo_filmico_confirmado_sem_catalogo_publico_de_video_coletavel",
                "protocol_status": "acervo_preservado_e_programacao_publica_sem_rota_de_video_de_acervo",
                "next_step": "retestar site oficial, API pública e eventuais catálogos digitais em ciclos futuros",
                "blocks_expansion": False,
                "rule_version": CINEMATHEQUE_LUXEMBOURG_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_cinematheque_luxembourg_protocol_probe(
    output_dir: Path = OUTPUT_DIR,
    fetcher=fetch_cinematheque_luxembourg_probe,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_cinematheque_luxembourg_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / CINEMATHEQUE_LUXEMBOURG_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_cinematheque_luxembourg_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "CINEMATHEQUE_LUXEMBOURG_ACCESS_CATEGORY",
    "CINEMATHEQUE_LUXEMBOURG_PROTOCOL_COLUMNS",
    "CINEMATHEQUE_LUXEMBOURG_PROTOCOL_FILENAME",
    "CINEMATHEQUE_LUXEMBOURG_PROTOCOL_PROBES",
    "CINEMATHEQUE_LUXEMBOURG_PROTOCOL_RULE_VERSION",
    "build_cinematheque_luxembourg_non_incorporated_register",
    "build_cinematheque_luxembourg_protocol_probe",
    "write_cinematheque_luxembourg_protocol_probe",
]
