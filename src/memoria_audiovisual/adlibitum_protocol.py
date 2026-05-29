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


ADLIBITUM_PROTOCOL_FILENAME = "observatorio_protocolo_adlibitum.csv"
ADLIBITUM_PROTOCOL_RULE_VERSION = "2026-05-adlibitum-protocol-v1"
ADLIBITUM_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS

ADLIBITUM_OFFICIAL_HTTP_URL = "http://www.adlibitum.saintmarcellin-vercors-isere.fr/"
ADLIBITUM_OFFICIAL_HTTPS_URL = "https://www.adlibitum.saintmarcellin-vercors-isere.fr/"
ADLIBITUM_INEDITS_MEMBER_URL = "https://inedits.eu/en/inedits_content/ad-libitum-workshop/"
ADLIBITUM_INEDITS_ONLINE_ARCHIVES_URL = "https://inedits.eu/en/resources/online-archives/"
ADLIBITUM_VOIRON_DIRECTORY_URL = (
    "https://www.voiron.fr/annuaire/1694/1266-ad-libitum-atelier-cinematographique-photographique.htm"
)


@dataclass(frozen=True)
class AdLibitumProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


ADLIBITUM_PROTOCOL_PROBES = [
    AdLibitumProbe(
        probe="official_site_http",
        probe_label="Site oficial informado pelo INEDITS - HTTP",
        method="GET",
        url=ADLIBITUM_OFFICIAL_HTTP_URL,
        evidence_signal="official_site",
        methodological_note="Testa a URL institucional informada pelo diretório INEDITS.",
    ),
    AdLibitumProbe(
        probe="official_site_https",
        probe_label="Site oficial informado pelo INEDITS - HTTPS",
        method="GET",
        url=ADLIBITUM_OFFICIAL_HTTPS_URL,
        evidence_signal="official_site",
        methodological_note="Testa a variação HTTPS da URL institucional informada pelo INEDITS.",
    ),
    AdLibitumProbe(
        probe="inedits_member_page",
        probe_label="Ficha do membro no INEDITS",
        method="GET",
        url=ADLIBITUM_INEDITS_MEMBER_URL,
        evidence_signal="directory_reference",
        methodological_note="Confirma a identificação institucional sem tratar a ficha como catálogo de filmes.",
    ),
    AdLibitumProbe(
        probe="inedits_online_archives_index",
        probe_label="Índice INEDITS de arquivos online",
        method="GET",
        url=ADLIBITUM_INEDITS_ONLINE_ARCHIVES_URL,
        evidence_signal="online_archives_index",
        methodological_note="Verifica se o INEDITS lista o Ad Libitum entre arquivos com acervo online.",
    ),
    AdLibitumProbe(
        probe="voiron_directory_page",
        probe_label="Página pública municipal de Voiron",
        method="GET",
        url=ADLIBITUM_VOIRON_DIRECTORY_URL,
        evidence_signal="municipal_reference",
        methodological_note="Confirma referência pública externa sem tratá-la como rota de acervo.",
    ),
]


def fetch_adlibitum_probe(url, method="GET", sample_bytes=524288):
    method = str(method or "GET").upper()
    response = None
    error = ""
    try:
        request_fn = requests.head if method == "HEAD" else requests.get
        kwargs = {
            "headers": {**HEADERS, "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)"},
            "timeout": (6, 8),
            "allow_redirects": True,
        }
        if method != "HEAD":
            kwargs["stream"] = True
        response = request_fn(url, **kwargs)
    except Exception as exc:
        error = str(exc)

    if response is None:
        return {
            "http_status": "",
            "final_url": url,
            "content_type": "",
            "content_length": "",
            "text": "",
            "error": error,
        }

    text = ""
    try:
        content_type = response.headers.get("content-type", "")
        if method != "HEAD" and any(token in content_type for token in ("text", "html", "json", "xml")):
            sample = response.raw.read(sample_bytes, decode_content=True)
            text = sample.decode(response.encoding or "utf-8", errors="replace")
    finally:
        response.close()

    return {
        "http_status": int(response.status_code),
        "final_url": response.url,
        "content_type": response.headers.get("content-type", ""),
        "content_length": response.headers.get("content-length", ""),
        "text": text,
        "error": error,
    }


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _page_signals(html, probe):
    soup = BeautifulSoup(html or "", "html.parser")
    text = _clean_text(soup.get_text(" ", strip=True)).lower()
    links = " ".join(
        f"{anchor.get_text(' ', strip=True)} {anchor.get('href', '')}"
        for anchor in soup.find_all("a", href=True)
    ).lower()
    adlibitum_present = "ad libitum" in text
    audiovisual_terms = ("film", "cinema", "cinématographique", "audiovisual", "audiovisuel")
    catalog_terms = ("catalogue", "database", "online archive", "archives online", "films online")
    player_detected = bool(soup.find(["iframe", "video", "source"]))
    online_archive_listed = probe == "inedits_online_archives_index" and adlibitum_present
    raw_catalog_detected = any(term in text or term in links for term in catalog_terms)
    if probe == "inedits_online_archives_index":
        catalog_detected = online_archive_listed
    elif probe in {"inedits_member_page", "voiron_directory_page"}:
        catalog_detected = False
    else:
        catalog_detected = raw_catalog_detected
    return {
        "adlibitum_present": adlibitum_present,
        "audiovisual_terms": any(term in text for term in audiovisual_terms),
        "player_detected": player_detected,
        "catalog_detected": catalog_detected,
        "online_archive_listed": online_archive_listed,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    values = [
        f"ad_libitum={'sim' if signals['adlibitum_present'] else 'nao'}",
        f"sinal_audiovisual={'sim' if signals['audiovisual_terms'] else 'nao'}",
        f"player={'sim' if signals['player_detected'] else 'nao'}",
        f"catalogo_publico={'sim' if signals['catalog_detected'] else 'nao'}",
        f"listado_no_indice_online={'sim' if signals['online_archive_listed'] else 'nao'}",
    ]
    return "; ".join(values)


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        if probe.evidence_signal == "official_site":
            return "site_oficial_indisponivel_na_rodada", "retestar_site_oficial_em_ciclo_futuro"
        return "rota_de_referencia_indisponivel_na_rodada", "retestar_sem_promover_a_corpus"

    if signals["player_detected"]:
        return "player_publico_detectado_a_validar", "prototipar_coleta_antes_de_incorporar"

    if probe.probe == "inedits_online_archives_index":
        if signals["online_archive_listed"]:
            return "indice_inedits_lista_acervo_online", "validar_fichas_e_players_do_acervo_online"
        return "indice_inedits_acessivel_sem_adlibitum", "manter_fora_do_corpus_ativo_nesta_rodada"

    if signals["adlibitum_present"] and signals["audiovisual_terms"]:
        return (
            "referencia_institucional_confirma_arquivo_sem_catalogo_publico",
            "buscar_catalogo_publico_api_ou_parceria_antes_de_ingestao",
        )

    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_adlibitum_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    signals = _page_signals(text, probe.probe) if access_status == "acessivel" else {}
    conclusion, next_step = _build_protocol_conclusion(probe, access_status, signals)
    return {
        "code": "inedits-ad-libitum",
        "label": "Ad Libitum Workshop",
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
        "rule_version": ADLIBITUM_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_adlibitum_protocol_probe(fetcher=fetch_adlibitum_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in ADLIBITUM_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=ADLIBITUM_PROTOCOL_COLUMNS)


def build_adlibitum_non_incorporated_register(protocol_df):
    inaccessible_official_total = 0
    reference_total = 0
    online_index_lists_adlibitum = False
    if protocol_df is not None and not protocol_df.empty:
        inaccessible_official_total = int(
            (
                protocol_df["probe"].astype(str).str.startswith("official_site")
                & (protocol_df["access_status"].astype(str) != "acessivel")
            ).sum()
        )
        reference_total = int(
            (
                protocol_df["protocol_conclusion"].astype(str)
                == "referencia_institucional_confirma_arquivo_sem_catalogo_publico"
            ).sum()
        )
        online_index_lists_adlibitum = bool(
            (
                protocol_df["protocol_conclusion"].astype(str)
                == "indice_inedits_lista_acervo_online"
            ).any()
        )

    index_note = (
        "O índice INEDITS de arquivos online lista o Ad Libitum."
        if online_index_lists_adlibitum
        else "O índice INEDITS de arquivos online não listou o Ad Libitum na sondagem."
    )
    return pd.DataFrame(
        [
            {
                "unit_code": "inedits-ad-libitum",
                "unit_label": "Ad Libitum Workshop",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "França",
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "O diretório INEDITS confirma a pertinência audiovisual, mas a sondagem não encontrou "
                    "catálogo público, player, API ou fichas de filmes coletáveis. O site oficial informado "
                    "não respondeu por rota HTTP/HTTPS simples."
                ),
                "collection_route_attempted": (
                    "Site oficial HTTP/HTTPS, ficha do membro no INEDITS, índice INEDITS de arquivos online "
                    "e página pública municipal de Voiron."
                ),
                "attempt_summary": (
                    f"{inaccessible_official_total} variações do site oficial indisponíveis; "
                    f"{reference_total} referências públicas confirmam a instituição audiovisual. "
                    f"{index_note}"
                ),
                "methodological_explanation": (
                    "A negativa é técnica e metodológica: a instituição é audiovisual, mas o organismo não "
                    "pode transformar referência institucional em corpus sem rota pública de registros, "
                    "metadados ou vídeo. Isso não equivale à ausência de acervo audiovisual no Ad Libitum."
                ),
                "evidence_status": "arquivo_audiovisual_confirmado_sem_rota_publica_coletavel",
                "protocol_status": "site_oficial_indisponivel_e_catalogo_publico_nao_detectado",
                "next_step": "retestar_site_oficial_e_buscar_catalogo_publico_api_ou_parceria_documentada",
                "blocks_expansion": False,
                "rule_version": ADLIBITUM_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_adlibitum_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_adlibitum_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_adlibitum_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / ADLIBITUM_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_adlibitum_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "ADLIBITUM_PROTOCOL_COLUMNS",
    "ADLIBITUM_PROTOCOL_FILENAME",
    "ADLIBITUM_PROTOCOL_PROBES",
    "ADLIBITUM_PROTOCOL_RULE_VERSION",
    "build_adlibitum_non_incorporated_register",
    "build_adlibitum_protocol_probe",
    "write_adlibitum_protocol_probe",
]
