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


PRISE2_PROTOCOL_FILENAME = "observatorio_protocolo_prise2.csv"
PRISE2_PROTOCOL_RULE_VERSION = "2026-06-prise2-protocol-v1"
PRISE2_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS

PRISE2_HOME_URL = "https://associationprise2.wordpress.com/"
PRISE2_ABOUT_URL = "https://associationprise2.wordpress.com/quisommes-nous/"
PRISE2_COLLECTION_URL = "https://associationprise2.wordpress.com/dimitri/"
PRISE2_INEDITS_MEMBER_URL = "https://inedits.eu/inedits_content/nives-sartori-association-prise-2/"
PRISE2_WP_API_URL = "https://associationprise2.wordpress.com/wp-json/wp/v2/pages?per_page=100"
PRISE2_WORDPRESSCOM_API_PAGES_URL = (
    "https://public-api.wordpress.com/wp/v2/sites/associationprise2.wordpress.com/pages?per_page=100"
)


@dataclass(frozen=True)
class Prise2Probe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


PRISE2_PROTOCOL_PROBES = [
    Prise2Probe(
        probe="official_home",
        probe_label="Site oficial Prise 2",
        method="GET",
        url=PRISE2_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Confirma a presença institucional sem tratar posts editoriais como catálogo completo.",
    ),
    Prise2Probe(
        probe="about_page",
        probe_label="Página Qui sommes-nous",
        method="GET",
        url=PRISE2_ABOUT_URL,
        evidence_signal="institutional_scope",
        methodological_note="Verifica missão, coleções e links públicos de vídeo declarados pela associação.",
    ),
    Prise2Probe(
        probe="collections_page",
        probe_label="Página Collections Prise 2",
        method="GET",
        url=PRISE2_COLLECTION_URL,
        evidence_signal="collection_reference",
        methodological_note="Testa se a página de coleção funciona como catálogo exaustivo ou apenas lista editorial.",
    ),
    Prise2Probe(
        probe="inedits_member_page",
        probe_label="Ficha do membro no INEDITS",
        method="GET",
        url=PRISE2_INEDITS_MEMBER_URL,
        evidence_signal="directory_reference",
        methodological_note="Confirma a identificação na rede INEDITS sem transformar a ficha em corpus.",
    ),
    Prise2Probe(
        probe="wordpress_api_pages",
        probe_label="API WordPress de páginas",
        method="GET",
        url=PRISE2_WP_API_URL,
        evidence_signal="api_route",
        methodological_note="Testa a rota REST padrão do próprio domínio WordPress.",
    ),
    Prise2Probe(
        probe="wordpresscom_api_pages",
        probe_label="API pública WordPress.com de páginas",
        method="GET",
        url=PRISE2_WORDPRESSCOM_API_PAGES_URL,
        evidence_signal="api_route",
        methodological_note="Verifica se a API pública do WordPress.com expõe páginas, distinguindo página editorial de catálogo audiovisual fechado.",
    ),
]


def fetch_prise2_probe(url, method="GET", sample_bytes=524288):
    response = None
    error = ""
    try:
        response = requests.get(
            url,
            headers={**HEADERS, "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)"},
            timeout=(8, 12),
            allow_redirects=True,
            stream=True,
        )
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=65536, decode_unicode=True):
            if not chunk:
                continue
            chunks.append(chunk if isinstance(chunk, str) else chunk.decode("utf-8", errors="ignore"))
            total += len(chunks[-1])
            if total >= sample_bytes:
                break
        text = "".join(chunks)
    except Exception as exc:
        text = ""
        error = str(exc)
    finally:
        if response is not None:
            response.close()

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


def _page_signals(html):
    soup = BeautifulSoup(html or "", "html.parser")
    text = _clean_text(soup.get_text(" ", strip=True)).lower()
    links_blob = " ".join(
        f"{anchor.get_text(' ', strip=True)} {anchor.get('href', '')}"
        for anchor in soup.find_all("a", href=True)
    ).lower()
    platform_links = re.findall(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com)[^\s\"'<>]+", links_blob)
    return {
        "prise2_present": "prise 2" in text or "associationprise2" in links_blob,
        "batritchevitch_present": "batritchevitch" in text,
        "audiovisual_terms": any(term in text for term in ("film", "cinéma", "cinema", "vidéo", "video", "super 8", "16 mm")),
        "collection_page": "collection batritchevitch" in text or "collections prise 2" in text,
        "non_exhaustive": "non exhaustive" in text or "non-exhaustive" in text,
        "wordpress_api_json": "application/json" in str(soup),
        "platform_links_total": len(dict.fromkeys(platform_links)),
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"prise2={'sim' if signals['prise2_present'] else 'nao'}",
            f"batritchevitch={'sim' if signals['batritchevitch_present'] else 'nao'}",
            f"sinal_audiovisual={'sim' if signals['audiovisual_terms'] else 'nao'}",
            f"pagina_colecao={'sim' if signals['collection_page'] else 'nao'}",
            f"lista_nao_exaustiva={'sim' if signals['non_exhaustive'] else 'nao'}",
            f"links_video_plataforma={signals['platform_links_total']}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        if probe.probe == "wordpress_api_pages":
            return "api_wordpress_padrao_indisponivel", "testar_api_publica_wordpresscom_sem_promover_a_corpus"
        return "rota_indisponivel_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe == "wordpresscom_api_pages":
        return "api_wordpresscom_disponivel_sem_catalogo_audiovisual_fechado", "usar_api_apenas_como_apoio_a_protocolo"
    if probe.probe == "collections_page" and signals.get("non_exhaustive"):
        return "colecao_publica_identificada_mas_lista_nao_exaustiva", "nao_incorporar_como_corpus_completo"
    if signals.get("platform_links_total", 0) > 0 and signals.get("audiovisual_terms"):
        return "links_publicos_de_video_detectados_sem_catalogo_fechado", "manter_protocolo_e_buscar_lista_exaustiva"
    if signals.get("audiovisual_terms"):
        return "referencia_audiovisual_confirmada_sem_rota_catalografica", "buscar_catalogo_publico_api_ou_parceria"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_prise2_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    signals = _page_signals(text) if access_status == "acessivel" else {}
    conclusion, next_step = _build_protocol_conclusion(probe, access_status, signals)
    return {
        "code": "inedits-prise-2",
        "label": "Association Prise 2",
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
        "rule_version": PRISE2_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_prise2_protocol_probe(fetcher=fetch_prise2_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in PRISE2_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=PRISE2_PROTOCOL_COLUMNS)


def build_prise2_non_incorporated_register(protocol_df):
    platform_links_total = 0
    wordpresscom_api_available = False
    if protocol_df is not None and not protocol_df.empty:
        wordpresscom_api_available = bool(
            (
                protocol_df["protocol_conclusion"].astype(str)
                == "api_wordpresscom_disponivel_sem_catalogo_audiovisual_fechado"
            ).any()
        )
        for observed_value in protocol_df["observed_value"].astype(str):
            match = re.search(r"links_video_plataforma=(\d+)", observed_value)
            if match:
                platform_links_total = max(platform_links_total, int(match.group(1)))

    return pd.DataFrame(
        [
            {
                "unit_code": "inedits-prise-2",
                "unit_label": "Association Prise 2",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "França",
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A associação tem pertinência audiovisual e página pública de coleção, mas a própria "
                    "página declara lista não exaustiva. A API pública do WordPress.com responde, mas expõe "
                    "páginas/posts editoriais, não um catálogo audiovisual fechado. Incorporar agora produziria "
                    "um corpus parcial como se fosse completo."
                ),
                "collection_route_attempted": (
                    "Site oficial WordPress, página institucional, página Collections Prise 2, ficha INEDITS "
                    "rota REST padrão e API pública WordPress.com de páginas."
                ),
                "attempt_summary": (
                    f"Foram detectados até {platform_links_total} links públicos de vídeo/plataforma nas páginas "
                    "sondadas. "
                    f"API WordPress.com disponível: {'sim' if wordpresscom_api_available else 'não'}. "
                    "Mesmo assim, não há catálogo fechado ou endpoint especificamente audiovisual para absorção completa."
                ),
                "methodological_explanation": (
                    "A negativa não equivale à ausência de audiovisual. Ela registra que há acervo e sinais "
                    "públicos, mas ainda não há rota suficiente para cumprir a regra de corpus completo do MVP."
                ),
                "evidence_status": "arquivo_audiovisual_confirmado_com_rota_publica_parcial",
                "protocol_status": "colecao_publica_nao_exaustiva_e_api_nao_disponivel",
                "next_step": "buscar catálogo público fechado, sitemap completo, API alternativa ou parceria documentada",
                "blocks_expansion": False,
                "rule_version": PRISE2_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_prise2_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_prise2_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_prise2_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / PRISE2_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_prise2_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "PRISE2_PROTOCOL_COLUMNS",
    "PRISE2_PROTOCOL_FILENAME",
    "PRISE2_PROTOCOL_PROBES",
    "PRISE2_PROTOCOL_RULE_VERSION",
    "build_prise2_non_incorporated_register",
    "build_prise2_protocol_probe",
    "write_prise2_protocol_probe",
]
