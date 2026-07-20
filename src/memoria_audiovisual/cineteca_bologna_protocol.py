from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import HEADERS, OUTPUT_DIR
from .europe_closure import (
    CINETECA_BOLOGNA_NON_INCORPORATION_CATEGORY,
    EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    merge_existing_excluded_units,
)
from .european_aggregators import classify_probe_access_status, detect_js_cookie_requirement
from .european_protocols import FRANCEARCHIVES_PROTOCOL_COLUMNS, detect_js_redirect, utcnow_iso


CINETECA_BOLOGNA_PROTOCOL_FILENAME = "observatorio_protocolo_cineteca_bologna.csv"
CINETECA_BOLOGNA_PROTOCOL_RULE_VERSION = "2026-07-cineteca-bologna-protocol-v1"
CINETECA_BOLOGNA_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS

CINETECA_BOLOGNA_HOME_URL = "https://cinetecadibologna.it/"
CINETECA_BOLOGNA_ARCHIVES_URL = "https://cinetecadibologna.it/archivi/"
CINETECA_BOLOGNA_AUDIOVISUAL_ARCHIVE_URL = (
    "https://cinetecadibologna.it/archivi/archivio/archivio-audiovisivi/"
)
CINETECA_BOLOGNA_CATALOG_FILM_URL = (
    "https://cinetecadibologna.it/archivi/archivio/archivio-audiovisivi/catalogo-film/"
)
CINETECA_BOLOGNA_CATALOG_DETAIL_SAMPLE_URL = (
    "https://cinetecadibologna.it/archivi/archivio/archivio-audiovisivi/catalogo-film/film/?film=62851"
)
CINETECA_BOLOGNA_WP_REST_TYPES_URL = "https://cinetecadibologna.it/wp-json/wp/v2/types"
CINETECA_BOLOGNA_AJAX_URL = "https://cinetecadibologna.it/archivi/wp-admin/admin-ajax.php"
CINETECA_BOLOGNA_YOUTUBE_URL = "https://www.youtube.com/@CinetecaBologna"


@dataclass(frozen=True)
class CinetecaBolognaProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str
    payload: dict[str, str] | None = None


CINETECA_BOLOGNA_PROTOCOL_PROBES = [
    CinetecaBolognaProbe(
        probe="official_home",
        probe_label="Página oficial da Cineteca di Bologna",
        method="GET",
        url=CINETECA_BOLOGNA_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Confirma identidade institucional sem tratar home ou agenda como corpus.",
    ),
    CinetecaBolognaProbe(
        probe="archives_overview",
        probe_label="Página Archivi",
        method="GET",
        url=CINETECA_BOLOGNA_ARCHIVES_URL,
        evidence_signal="archive_holdings",
        methodological_note="Verifica a existência de acervos e as regras de consulta pública.",
    ),
    CinetecaBolognaProbe(
        probe="audiovisual_archive",
        probe_label="Archivio audiovisivi",
        method="GET",
        url=CINETECA_BOLOGNA_AUDIOVISUAL_ARCHIVE_URL,
        evidence_signal="audiovisual_archive_catalog",
        methodological_note="Verifica a rota pública específica do arquivo audiovisual.",
    ),
    CinetecaBolognaProbe(
        probe="catalog_film_page",
        probe_label="Catalogo Film",
        method="GET",
        url=CINETECA_BOLOGNA_CATALOG_FILM_URL,
        evidence_signal="public_metadata_catalog",
        methodological_note="Testa a página pública do catálogo de metadados audiovisuais.",
    ),
    CinetecaBolognaProbe(
        probe="catalog_ajax_page_1",
        probe_label="Endpoint AJAX do Catalogo Film",
        method="POST",
        url=CINETECA_BOLOGNA_AJAX_URL,
        evidence_signal="ajax_catalog_enumeration",
        methodological_note="Sonda a enumeração pública sem varrer todas as 3.290 páginas no protocolo leve.",
        payload={
            "action": "archivio_audiovisivo_apply_filters",
            "archive_page_id": "280",
            "post_type": "",
            "posts_per_page": "12",
            "catalogo": "film",
            "pag": "1",
            "navigation": "load-more",
            "filters_query": "",
            "filters": "",
        },
    ),
    CinetecaBolognaProbe(
        probe="catalog_detail_sample",
        probe_label="Ficha pública de exemplo",
        method="GET",
        url=CINETECA_BOLOGNA_CATALOG_DETAIL_SAMPLE_URL,
        evidence_signal="public_record_no_player",
        methodological_note="Verifica se a ficha individual expõe player ou apenas metadados.",
    ),
    CinetecaBolognaProbe(
        probe="wp_rest_types",
        probe_label="WordPress REST types",
        method="GET",
        url=CINETECA_BOLOGNA_WP_REST_TYPES_URL,
        evidence_signal="wp_rest_access",
        methodological_note="Testa se existe rota REST pública mais eficiente que o AJAX.",
    ),
    CinetecaBolognaProbe(
        probe="youtube_channel",
        probe_label="Canal YouTube institucional",
        method="GET",
        url=CINETECA_BOLOGNA_YOUTUBE_URL,
        evidence_signal="public_institutional_channel",
        methodological_note="Registra canal público sem confundi-lo com catálogo do acervo audiovisual.",
    ),
]


def fetch_cineteca_bologna_probe(probe, sample_bytes=786432):
    response = None
    error = ""
    try:
        kwargs = {
            "headers": {
                **HEADERS,
                "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.8,pt-BR;q=0.7",
                "Referer": CINETECA_BOLOGNA_CATALOG_FILM_URL,
            },
            "timeout": (8, 18),
            "allow_redirects": True,
        }
        if probe.method == "POST":
            response = requests.post(probe.url, data=probe.payload or {}, **kwargs)
        else:
            response = requests.get(probe.url, **kwargs)
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


def _json_payload(raw):
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _page_signals(content):
    raw = str(content or "")
    payload = _json_payload(raw)
    html_items = payload.get("items", "") if isinstance(payload, dict) else ""
    combined_html = f"{raw} {html_items}"
    visible_text = BeautifulSoup(combined_html, "html.parser").get_text(" ", strip=True)
    text = _clean_text(f"{visible_text} {raw}").lower()
    articles = len(BeautifulSoup(html_items, "html.parser").select("article")) if html_items else 0
    navigation = payload.get("navigation", {}) if isinstance(payload, dict) else {}
    total_pages = navigation.get("total_pages", "")
    return {
        "official_identity": "cineteca di bologna" in text,
        "archive_terms": any(term in text for term in ("archivio", "archivi", "patrimonio")),
        "film_archive_90000": bool(re.search(r"\b90[ .]?000\b", text) and "archivio film" in text),
        "audiovisual_archive_terms": "archivio audiovisivi" in text,
        "consultation_terms": any(term in text for term in ("consultazione", "prestito", "su richiesta", "via mail")),
        "catalog_terms": "catalogo film" in text or "catalogo registi" in text,
        "ajax_articles": articles,
        "ajax_total_pages": total_pages,
        "detail_links": len(re.findall(r"catalogo-film(?:\\/|/)film(?:\\/|/)\?film=", raw, flags=re.I)),
        "public_player_patterns": len(
            re.findall(
                r"youtube(?:-nocookie)?\\.com/embed/|player\\.vimeo\\.com/video/|\\.mp4\\b|\\.m3u8\\b|<video\\b",
                combined_html,
                flags=re.I,
            )
        ),
        "wp_rest_denied": "rest_not_logged_in" in raw or '"status":401' in raw,
        "youtube_channel": "cinetecabologna" in text and "youtube" in text,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"identidade={'sim' if signals['official_identity'] else 'nao'}",
            f"arquivo={'sim' if signals['archive_terms'] else 'nao'}",
            f"acervo_90000={'sim' if signals['film_archive_90000'] else 'nao'}",
            f"arquivo_audiovisivi={'sim' if signals['audiovisual_archive_terms'] else 'nao'}",
            f"consulta_prestimo={'sim' if signals['consultation_terms'] else 'nao'}",
            f"catalogo={'sim' if signals['catalog_terms'] else 'nao'}",
            f"ajax_items={signals['ajax_articles']}",
            f"ajax_total_pages={signals['ajax_total_pages']}",
            f"links_detalhe={signals['detail_links']}",
            f"players_publicos={signals['public_player_patterns']}",
            f"wp_rest_401={'sim' if signals['wp_rest_denied'] else 'nao'}",
            f"canal_youtube={'sim' if signals['youtube_channel'] else 'nao'}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        if probe.probe == "wp_rest_types" and signals.get("wp_rest_denied"):
            return "wp_rest_nao_publico_para_coleta_eficiente", "usar_ajax_ou_buscar_exportacao_documentada"
        return "rota_indisponivel_ou_instavel_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe == "archives_overview" and signals.get("film_archive_90000"):
        return "acervo_filmico_confirmado_com_consulta_por_pedido", "registrar_contexto_de_acesso_local_autorizado"
    if probe.probe == "audiovisual_archive" and signals.get("catalog_terms"):
        return "arquivo_audiovisual_confirma_catalogo_publico", "validar_viabilidade_de_ingestao_total"
    if probe.probe == "catalog_ajax_page_1" and signals.get("ajax_total_pages"):
        return "catalogo_ajax_publico_extenso_validado_sem_bulk_export", "planejar_ingestao_incremental_ou_exportacao"
    if probe.probe == "catalog_detail_sample":
        if signals.get("public_player_patterns"):
            return "ficha_publica_com_player_a_validar", "validar_player_antes_de_incorporar"
        return "ficha_publica_de_metadados_sem_player_detectado", "classificar_como_metadados_publicos_midia_local_autorizada"
    if probe.probe == "wp_rest_types":
        if signals.get("wp_rest_denied"):
            return "wp_rest_nao_publico_para_coleta_eficiente", "usar_ajax_ou_buscar_exportacao_documentada"
        return "wp_rest_acessivel_a_validar", "validar_se_substitui_ajax"
    if probe.probe == "youtube_channel":
        return "canal_youtube_publico_nao_equivale_ao_catalogo_de_acervo", "monitorar_apenas_como_canal_institucional"
    if probe.probe == "catalog_film_page":
        return "pagina_de_catalogo_publica_com_renderizacao_ajax", "usar_endpoint_ajax_com_cautela"
    return "site_oficial_contextual_sem_incorporacao_automatica", "manter_como_evidencia_institucional"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_cineteca_bologna_probe):
    fetched = fetcher(probe)
    text = fetched.get("text", "")
    signals = _page_signals(text) if text else {}
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    if probe.probe == "wp_rest_types" and signals.get("wp_rest_denied"):
        access_status = "restrito"
    conclusion, next_step = _build_protocol_conclusion(probe, access_status, signals)
    return {
        "code": "fiaf-cineteca-bologna",
        "label": "Fondazione Cineteca di Bologna",
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
        "rule_version": CINETECA_BOLOGNA_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_cineteca_bologna_protocol_probe(fetcher=fetch_cineteca_bologna_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in CINETECA_BOLOGNA_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=CINETECA_BOLOGNA_PROTOCOL_COLUMNS)


def build_cineteca_bologna_non_incorporated_register(protocol_df):
    return pd.DataFrame(
        [
            {
                "unit_code": "fiaf-cineteca-bologna",
                "unit_label": "Fondazione Cineteca di Bologna",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Bolonha / Itália",
                "access_category": CINETECA_BOLOGNA_NON_INCORPORATION_CATEGORY,
                "public_status": "Identificada, mas não incluída no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A rota pública do Catalogo Film do Archivio audiovisivi foi validada e anuncia 3.290 páginas "
                    "AJAX de registros, mas não há exportação pública/bulk ou REST aberto. A tentativa de coleta "
                    "total no ambiente local excedeu a janela operacional de 15 minutos. As fichas amostradas não "
                    "expõem player público; o acesso à mídia permanece por consulta/prestimo/autorização."
                ),
                "collection_route_attempted": (
                    "Página oficial, página Archivi, Archivio audiovisivi, Catalogo Film, endpoint AJAX "
                    "`archivio_audiovisivo_apply_filters`, ficha pública de exemplo, WordPress REST e canal YouTube."
                ),
                "attempt_summary": (
                    "O site confirma acervo fílmico de mais de 90.000 elementos e rota pública de catálogo "
                    "audiovisual. O AJAX retorna 12 registros por página e total de 3.290 páginas; a REST pública "
                    "retorna 401. As fichas testadas trazem metadados, duração/formato quando disponíveis e ausência "
                    "de player público."
                ),
                "methodological_explanation": (
                    "A negativa é operacional, não substantiva. A unidade tem acervo audiovisual e catálogo público "
                    "relevante, mas não deve entrar como corpus ativo com amostra parcial. A incorporação definitiva "
                    "exige ingestão incremental/sharding, exportação oficial ou outro método reprodutível para "
                    "materializar o catálogo completo sem sobrecarregar a fonte."
                ),
                "evidence_status": "catalogo_publico_audiovisual_extenso_validado_sem_ingestao_total_no_mvp",
                "protocol_status": "rota_validada_incorporacao_total_pendente_por_custo_operacional",
                "next_step": "criar_ingestao_incremental_por_pagina_ou_solicitar_exportacao_publica_do_catalogo",
                "blocks_expansion": False,
                "rule_version": CINETECA_BOLOGNA_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_cineteca_bologna_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_cineteca_bologna_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_cineteca_bologna_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / CINETECA_BOLOGNA_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_cineteca_bologna_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "CINETECA_BOLOGNA_PROTOCOL_COLUMNS",
    "CINETECA_BOLOGNA_PROTOCOL_FILENAME",
    "CINETECA_BOLOGNA_PROTOCOL_PROBES",
    "CINETECA_BOLOGNA_PROTOCOL_RULE_VERSION",
    "build_cineteca_bologna_non_incorporated_register",
    "build_cineteca_bologna_protocol_probe",
    "write_cineteca_bologna_protocol_probe",
]
