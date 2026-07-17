from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from .config import HEADERS, OUTPUT_DIR
from .europe_closure import (
    EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    merge_existing_excluded_units,
)
from .european_aggregators import classify_probe_access_status, detect_js_cookie_requirement
from .european_protocols import FRANCEARCHIVES_PROTOCOL_COLUMNS, detect_js_redirect, utcnow_iso


CINETECA_ITALIANA_PROTOCOL_FILENAME = "observatorio_protocolo_cineteca_italiana.csv"
CINETECA_ITALIANA_PROTOCOL_RULE_VERSION = "2026-07-cineteca-italiana-protocol-v1"
CINETECA_ITALIANA_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
CINETECA_ITALIANA_ACCESS_CATEGORY = (
    "arquivo_filmico_com_streaming_protegido_sem_catalogo_publico_de_video"
)

CINETECA_ITALIANA_HOME_URL = "https://www.cinetecamilano.it/"
CINETECA_ITALIANA_ABOUT_URL = "https://www.cinetecamilano.it/chi-siamo/"
CINETECA_ITALIANA_RESTORATION_URL = "https://www.cinetecamilano.it/restauro-film/"
CINETECA_ITALIANA_FILM_URL = "https://www.cinetecamilano.it/film/"
CINETECA_ITALIANA_STREAMING_URL = "https://www.cinetecamilano.it/streaming/"
CINETECA_ITALIANA_STREAMING_API_URL = (
    "https://www.cinetecamilano.it/wp-json/wp/v2/streaming?per_page=10&context=view"
)
CINETECA_ITALIANA_FILM_API_URL = "https://www.cinetecamilano.it/wp-json/wp/v2/film?per_page=10&context=view"
CINETECA_ITALIANA_ARCHIVE_VISIT_URL = (
    "https://www.cinetecamilano.it/evento/visita-guidata-allarchivio-film/"
)
CINETECA_ITALIANA_YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCazdgK2z2EdkCqnVMtFpelA"
THE_FILM_CORNER_REGISTER_URL = "https://www.thefilmcorner.eu/register/"


@dataclass(frozen=True)
class CinetecaItalianaProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


CINETECA_ITALIANA_PROTOCOL_PROBES = [
    CinetecaItalianaProbe(
        probe="official_home",
        probe_label="Página oficial da Cineteca Milano",
        method="GET",
        url=CINETECA_ITALIANA_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Confirma a identidade institucional sem tratar a página geral como catálogo de acervo.",
    ),
    CinetecaItalianaProbe(
        probe="about_archive",
        probe_label="Página Chi siamo",
        method="GET",
        url=CINETECA_ITALIANA_ABOUT_URL,
        evidence_signal="film_archive_confirmed",
        methodological_note="Verifica se a instituição confirma acervo fílmico preservado e rota pública de catálogo.",
    ),
    CinetecaItalianaProbe(
        probe="restoration_lab",
        probe_label="Laboratório de restauração",
        method="GET",
        url=CINETECA_ITALIANA_RESTORATION_URL,
        evidence_signal="restoration_digitization",
        methodological_note="Distingue digitalização/restauração de acesso público online ao acervo.",
    ),
    CinetecaItalianaProbe(
        probe="film_programming_archive",
        probe_label="Arquivo público de páginas Film",
        method="GET",
        url=CINETECA_ITALIANA_FILM_URL,
        evidence_signal="film_programming",
        methodological_note="Testa se a seção Film é catálogo de acervo ou programação de sala.",
    ),
    CinetecaItalianaProbe(
        probe="streaming_account_page",
        probe_label="Página de streaming",
        method="GET",
        url=CINETECA_ITALIANA_STREAMING_URL,
        evidence_signal="protected_streaming",
        methodological_note="Verifica se o streaming é público ou depende de conta, compra, senha ou autenticação.",
    ),
    CinetecaItalianaProbe(
        probe="streaming_rest_api",
        probe_label="Endpoint WordPress de streaming",
        method="GET",
        url=CINETECA_ITALIANA_STREAMING_API_URL,
        evidence_signal="protected_streaming_api",
        methodological_note="Sonda metadados públicos sem tentar contornar conteúdo protegido por senha.",
    ),
    CinetecaItalianaProbe(
        probe="film_rest_api",
        probe_label="Endpoint WordPress de páginas Film",
        method="GET",
        url=CINETECA_ITALIANA_FILM_API_URL,
        evidence_signal="film_programming_api",
        methodological_note="Confirma se os registros Film são páginas de programação e não vídeos de acervo.",
    ),
    CinetecaItalianaProbe(
        probe="guided_archive_visit",
        probe_label="Visita guiada ao Arquivo Film",
        method="GET",
        url=CINETECA_ITALIANA_ARCHIVE_VISIT_URL,
        evidence_signal="onsite_archive_access",
        methodological_note="Distingue acesso presencial guiado de corpus público online coletável.",
    ),
    CinetecaItalianaProbe(
        probe="youtube_rss",
        probe_label="Feed RSS do canal YouTube",
        method="GET",
        url=CINETECA_ITALIANA_YOUTUBE_RSS_URL,
        evidence_signal="public_institutional_channel",
        methodological_note="Registra canal público sem promovê-lo automaticamente a catálogo do acervo fílmico.",
    ),
    CinetecaItalianaProbe(
        probe="the_film_corner_register",
        probe_label="The Film Corner",
        method="GET",
        url=THE_FILM_CORNER_REGISTER_URL,
        evidence_signal="educational_platform",
        methodological_note="Verifica plataforma educativa associada sem confundi-la com catálogo público de acervo.",
    ),
]


def fetch_cineteca_italiana_probe(probe, sample_bytes=786432):
    response = None
    error = ""
    try:
        response = requests.get(
            probe.url,
            headers={
                **HEADERS,
                "Accept": "application/json, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.8,pt-BR;q=0.7",
            },
            timeout=(8, 16),
            allow_redirects=True,
        )
        response.encoding = response.encoding or response.apparent_encoding or "utf-8"
        text = response.text[:sample_bytes]
    except Exception as exc:
        text = ""
        error = str(exc)

    return {
        "http_status": response.status_code if response is not None else "",
        "final_url": response.url if response is not None else probe.url,
        "content_type": response.headers.get("content-type", "") if response is not None else "",
        "content_length": response.headers.get("content-length", "") if response is not None else "",
        "text": text,
        "error": error,
    }


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _json_items(raw):
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return parsed.get("items", []) if isinstance(parsed.get("items"), list) else [parsed]
    return []


def _page_signals(content):
    raw = str(content or "")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
        visible_text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    text = _clean_text(f"{visible_text} {raw}").lower()
    items = _json_items(raw)
    protected_entries = sum(1 for item in items if isinstance(item, dict) and item.get("content", {}).get("protected"))
    if not protected_entries:
        protected_entries = len(re.findall(r'"protected"\s*:\s*true', raw, flags=re.I))
    streaming_items = len(items) if items and any(str(item.get("type", "")) == "streaming" for item in items if isinstance(item, dict)) else 0
    film_items = len(items) if items and any(str(item.get("type", "")) == "film" for item in items if isinstance(item, dict)) else 0
    youtube_entries = len(re.findall(r"<entry\b", raw, flags=re.I))
    public_player_patterns = len(
        re.findall(
            r"youtube(?:-nocookie)?\.com/embed/|player\.vimeo\.com/video/|\.mp4\b|\.m3u8\b|<video\b",
            raw,
            flags=re.I,
        )
    )
    return {
        "official_identity": "cineteca milano" in text or "fondazione cineteca italiana" in text,
        "archive_count_40000": bool(re.search(r"\b40[ .]?000\b", text) and ("pellicola" in text or "titoli" in text)),
        "film_archive_terms": any(term in text for term in ("archivio film", "archivio di film", "film archive", "pellicola")),
        "restoration_terms": any(term in text for term in ("restauro", "digitalizzazione", "laboratorio")),
        "programming_terms": any(term in text for term in ("programmazione", "proiezioni", "biglietti", "acquista", "sale cinematografiche")),
        "protected_streaming_terms": any(term in text for term in ("protetto", "password", "acquistato", "mio-account", "streaming che hai acquistato")),
        "archive_visit_terms": any(term in text for term in ("visita guidata", "archivio film", "15 metri", "realtà aumentata")),
        "the_film_corner_terms": "the film corner" in text and any(term in text for term in ("register", "literacy", "education", "educational", "didactical")),
        "streaming_items": streaming_items,
        "film_items": film_items,
        "protected_entries": protected_entries,
        "youtube_rss_entries": youtube_entries,
        "youtube_channel_identity": "cineteca milano" in text and "youtube" in text,
        "public_player_patterns": public_player_patterns,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"identidade={'sim' if signals['official_identity'] else 'nao'}",
            f"acervo_40000_titulos={'sim' if signals['archive_count_40000'] else 'nao'}",
            f"termos_arquivo_filmico={'sim' if signals['film_archive_terms'] else 'nao'}",
            f"restauro_digitalizacao={'sim' if signals['restoration_terms'] else 'nao'}",
            f"programacao_sala={'sim' if signals['programming_terms'] else 'nao'}",
            f"streaming_protegido={'sim' if signals['protected_streaming_terms'] else 'nao'}",
            f"acesso_presencial={'sim' if signals['archive_visit_terms'] else 'nao'}",
            f"film_corner={'sim' if signals['the_film_corner_terms'] else 'nao'}",
            f"streaming_items={signals['streaming_items']}",
            f"film_items={signals['film_items']}",
            f"protected_entries={signals['protected_entries']}",
            f"youtube_rss_entries={signals['youtube_rss_entries']}",
            f"players_publicos={signals['public_player_patterns']}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        return "rota_indisponivel_ou_instavel_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe == "about_archive" and (signals.get("archive_count_40000") or signals.get("film_archive_terms")):
        return "acervo_filmico_confirmado_sem_catalogo_publico_de_video", "registrar_unidade_nao_incorporada_por_ausencia_de_rota_coletavel"
    if probe.probe == "restoration_lab":
        return "laboratorio_confirma_preservacao_sem_superficie_publica_de_acervo", "manter_como_evidencia_institucional"
    if probe.probe in {"film_programming_archive", "film_rest_api"}:
        return "programacao_de_sala_nao_equivale_a_corpus_audiovisual", "nao_incorporar_paginas_de_programacao_como_acervo"
    if probe.probe == "streaming_account_page":
        return "streaming_por_conta_compra_ou_senha_nao_incorporavel", "nao_contornar_login_senha_ou_compra"
    if probe.probe == "streaming_rest_api" and (signals.get("protected_entries") or signals.get("streaming_items")):
        return "api_streaming_expoe_registros_protegidos_sem_conteudo_publico", "documentar_restricao_sem_coletar_conteudo_protegido"
    if probe.probe == "guided_archive_visit":
        return "acesso_presencial_guiado_nao_equivale_a_corpus_online", "manter_como_evidencia_de_acervo_nao_coletavel"
    if probe.probe == "youtube_rss" and signals.get("youtube_rss_entries"):
        return "canal_youtube_publico_detectado_sem_catalogo_de_acervo", "monitorar_como_canal_institucional_sem_promover_a_corpus_integral"
    if probe.probe == "the_film_corner_register":
        return "plataforma_educativa_com_registro_nao_equivale_a_catalogo_publico_do_acervo", "manter_fora_do_corpus_ativo_do_acervo"
    if probe.probe == "official_home":
        return "site_oficial_contextual_sem_catalogo_publico_de_video", "manter_como_evidencia_institucional"
    if signals.get("protected_streaming_terms"):
        return "streaming_protegido_sem_rota_publica_coletavel", "manter_fora_do_corpus_ativo"
    if signals.get("public_player_patterns"):
        return "players_publicos_detectados_sem_recorte_catalografico_validado", "validar_recorte_antes_de_incorporar"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_cineteca_italiana_probe):
    fetched = fetcher(probe)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    signals = _page_signals(text) if text else {}
    conclusion, next_step = _build_protocol_conclusion(probe, access_status, signals)
    return {
        "code": "fiaf-cineteca-italiana",
        "label": "Fondazione Cineteca Italiana",
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
        "rule_version": CINETECA_ITALIANA_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_cineteca_italiana_protocol_probe(fetcher=fetch_cineteca_italiana_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in CINETECA_ITALIANA_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=CINETECA_ITALIANA_PROTOCOL_COLUMNS)


def build_cineteca_italiana_non_incorporated_register(protocol_df):
    return pd.DataFrame(
        [
            {
                "unit_code": "fiaf-cineteca-italiana",
                "unit_label": "Fondazione Cineteca Italiana",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Milão / Itália",
                "access_category": CINETECA_ITALIANA_ACCESS_CATEGORY,
                "public_status": "Identificada, mas não incluída no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A Fondazione Cineteca Italiana/Cineteca Milano tem acervo fílmico confirmado, mas as rotas "
                    "públicas observadas expõem página institucional, restauração, programação de sala, acesso "
                    "presencial guiado, streaming protegido por conta/compra/senha e canais institucionais externos. "
                    "Não foi localizada rota pública estável de catálogo de vídeos de acervo."
                ),
                "collection_route_attempted": (
                    "Página oficial, página Chi siamo, laboratório de restauração, seção Film, endpoint WordPress "
                    "de Film, página de streaming, endpoint WordPress de streaming, visita guiada ao Arquivo Film, "
                    "feed RSS do canal YouTube e The Film Corner."
                ),
                "attempt_summary": (
                    "A página institucional confirma acervo fílmico de cerca de 40.000 títulos em película. A seção "
                    "Film e o endpoint `film` funcionam como programação de sala. O endpoint `streaming` expõe poucos "
                    "registros protegidos, sem conteúdo público. A visita ao Arquivo Film é presencial. O feed YouTube "
                    "é público, mas representa canal institucional recente, não catálogo público integral do acervo."
                ),
                "methodological_explanation": (
                    "A negativa não nega a existência nem a relevância do acervo. Ela impede que programação de cinema, "
                    "streaming protegido, visita presencial, plataforma educativa com registro ou canal institucional "
                    "recente sejam tratados como corpus público de arquivo fílmico. Para entrar como corpus ativo, a "
                    "unidade precisa expor registros públicos de vídeo de acervo ou metadados audiovisuais coletáveis "
                    "de forma reprodutível."
                ),
                "evidence_status": "arquivo_filmico_confirmado_com_streaming_protegido_sem_catalogo_publico_de_video",
                "protocol_status": "acervo_preservado_programacao_publica_streaming_protegido_e_canal_publico_nao_catalografico",
                "next_step": "retestar_site_oficial_streaming_youtube_vimeo_e_eventual_catalogo_publico_de_acervo_em_ciclos_futuros",
                "blocks_expansion": False,
                "rule_version": CINETECA_ITALIANA_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_cineteca_italiana_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_cineteca_italiana_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_cineteca_italiana_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / CINETECA_ITALIANA_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_cineteca_italiana_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "CINETECA_ITALIANA_ACCESS_CATEGORY",
    "CINETECA_ITALIANA_PROTOCOL_COLUMNS",
    "CINETECA_ITALIANA_PROTOCOL_FILENAME",
    "CINETECA_ITALIANA_PROTOCOL_PROBES",
    "CINETECA_ITALIANA_PROTOCOL_RULE_VERSION",
    "build_cineteca_italiana_non_incorporated_register",
    "build_cineteca_italiana_protocol_probe",
    "write_cineteca_italiana_protocol_probe",
]
