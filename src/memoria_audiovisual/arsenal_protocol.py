from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from .config import (
    ARSENAL_ARCHIVE_DISTRIBUTION_URL,
    ARSENAL_FILM_DATABASE_BROWSE_URL,
    ARSENAL_FILM_DATABASE_URL,
    ARSENAL_HOME_URL,
    HEADERS,
    OUTPUT_DIR,
    ROOT_DIR,
)
from .europe_closure import (
    EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    merge_existing_excluded_units,
)
from .european_aggregators import classify_probe_access_status, detect_js_cookie_requirement
from .european_protocols import FRANCEARCHIVES_PROTOCOL_COLUMNS, detect_js_redirect, utcnow_iso


ARSENAL_PROTOCOL_FILENAME = "observatorio_protocolo_arsenal.csv"
ARSENAL_PROTOCOL_RULE_VERSION = "2026-06-arsenal-protocol-v1"
ARSENAL_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
ARSENAL_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
)


@dataclass(frozen=True)
class ArsenalProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


ARSENAL_PROTOCOL_PROBES = [
    ArsenalProbe(
        probe="official_home",
        probe_label="Site oficial Arsenal",
        method="GET",
        url=ARSENAL_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Confirma a presença institucional sem tratar a home como catálogo.",
    ),
    ArsenalProbe(
        probe="archive_distribution_page",
        probe_label="Página Archive & Distribution",
        method="GET",
        url=ARSENAL_ARCHIVE_DISTRIBUTION_URL,
        evidence_signal="archive_distribution_reference",
        methodological_note="Verifica a página que aponta para arquivo, distribuição e Film Database.",
    ),
    ArsenalProbe(
        probe="film_database_simple_get",
        probe_label="Film Database por requisição simples",
        method="GET",
        url=ARSENAL_FILM_DATABASE_URL,
        evidence_signal="catalog_route",
        methodological_note="Testa se o catálogo responde sem navegador; nesta rodada houve bloqueio/timeout intermitente.",
    ),
    ArsenalProbe(
        probe="browse_works_browser",
        probe_label="Browse Works por navegador",
        method="BROWSER",
        url=ARSENAL_FILM_DATABASE_BROWSE_URL,
        evidence_signal="browser_catalog_probe",
        methodological_note="Testa a rota pública com navegador Playwright, necessária por proteção Anubis.",
    ),
]


def _playwright_browser_path():
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return
    local_playwright_dir = ROOT_DIR / ".playwright"
    if local_playwright_dir.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(local_playwright_dir)


def fetch_arsenal_probe(url, method="GET", sample_bytes=524288):
    method = str(method or "GET").upper()
    if method == "BROWSER":
        return fetch_arsenal_browser_probe(url)

    response = None
    error = ""
    try:
        response = requests.get(
            url,
            headers={**HEADERS, "User-Agent": ARSENAL_USER_AGENT},
            timeout=(8, 10),
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


def fetch_arsenal_browser_probe(url):
    _playwright_browser_path()
    error = ""
    final_url = url
    text = ""
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(user_agent=ARSENAL_USER_AGENT)
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(8000)
                final_url = page.url
                text = page.locator("body").inner_text(timeout=10000)
            finally:
                browser.close()
    except Exception as exc:
        error = str(exc)
    return {
        "http_status": 200 if text and not error else "",
        "final_url": final_url,
        "content_type": "text/html" if text else "",
        "content_length": len(text),
        "text": text,
        "error": error,
    }


def _page_signals(text):
    normalized = BeautifulSoup(str(text or ""), "html.parser").get_text(" ", strip=True).lower()
    total_match = re.search(r"(\d[\d.,]*)\s+(?:werke|works)\s+(?:gefunden|found)", normalized)
    browse_total = re.sub(r"\D", "", total_match.group(1)) if total_match else ""
    return {
        "arsenal_present": "arsenal" in normalized,
        "film_database_present": "film database" in normalized or "browse works" in normalized,
        "anubis_detected": "anubis" in normalized or "making sure" in normalized,
        "records_detected": bool(re.search(r"\b\d[\d.,]*\s+(?:werke|works)\s+(?:gefunden|found)", normalized)),
        "browse_total": browse_total,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"arsenal={'sim' if signals['arsenal_present'] else 'nao'}",
            f"film_database={'sim' if signals['film_database_present'] else 'nao'}",
            f"anubis={'sim' if signals['anubis_detected'] else 'nao'}",
            f"registros_detectados={'sim' if signals['records_detected'] else 'nao'}",
            f"total_browse={signals['browse_total'] or 'nao_detectado'}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        return "rota_instavel_ou_timeout_na_rodada", "retestar_rota_com_janela_de_coleta_mais_estavel"
    if probe.method == "BROWSER" and signals.get("records_detected"):
        return "catalogo_publico_confirmado_mas_coleta_completa_instavel", "retestar_paginacao_completa_antes_de_incorporar"
    if signals.get("anubis_detected"):
        return "catalogo_exige_navegador_por_protecao_anubis", "usar_protocolo_de_navegador_e_validar_estabilidade"
    if probe.probe in {"official_home", "archive_distribution_page"} and signals.get("arsenal_present"):
        return "referencia_institucional_confirma_arquivo_audiovisual", "validar_rota_catalografica_antes_de_incorporar"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_arsenal_probe):
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
        "code": "fiaf-arsenal-filminstitut",
        "label": "Arsenal Filminstitut",
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
        "rule_version": ARSENAL_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_arsenal_protocol_probe(fetcher=fetch_arsenal_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in ARSENAL_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=ARSENAL_PROTOCOL_COLUMNS)


def build_arsenal_non_incorporated_register(protocol_df):
    browser_rows = pd.DataFrame()
    if protocol_df is not None and not protocol_df.empty:
        browser_rows = protocol_df.loc[protocol_df["probe"].astype(str) == "browse_works_browser"].copy()
    browser_observed = browser_rows["observed_value"].iloc[0] if not browser_rows.empty else ""
    return pd.DataFrame(
        [
            {
                "unit_code": "fiaf-arsenal-filminstitut",
                "unit_label": "Arsenal Filminstitut",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Alemanha",
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A Film Database pública foi identificada, mas a rota exige navegador por proteção Anubis "
                    "e apresentou timeouts intermitentes durante a tentativa de paginação completa. "
                    "Sem estabilidade, a incorporação geraria corpus incompleto ou saída zero."
                ),
                "collection_route_attempted": (
                    "Site oficial, página Archive & Distribution, Film Database por requisição simples "
                    "e Browse Works por navegador Playwright."
                ),
                "attempt_summary": (
                    "A rota Browse Works chegou a indicar catálogo público de obras, mas não se manteve "
                    f"estável para ciclo reprodutível. Observação do navegador: {browser_observed or 'não disponível'}."
                ),
                "methodological_explanation": (
                    "A negativa é técnica e metodológica: o Arsenal é audiovisual e tem catálogo público, "
                    "mas o organismo só incorpora corpus quando consegue reproduzir a coleta sem instabilidade "
                    "estrutural. Isso não equivale à ausência de acervo."
                ),
                "evidence_status": "arquivo_audiovisual_confirmado_com_rota_catalografica_instavel",
                "protocol_status": "catalogo_publico_identificado_mas_paginacao_instavel",
                "next_step": "retestar Browse Works com janela estável e só incorporar após completar a paginação pública",
                "blocks_expansion": False,
                "rule_version": ARSENAL_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_arsenal_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_arsenal_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_arsenal_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / ARSENAL_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_arsenal_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "ARSENAL_PROTOCOL_COLUMNS",
    "ARSENAL_PROTOCOL_FILENAME",
    "ARSENAL_PROTOCOL_PROBES",
    "ARSENAL_PROTOCOL_RULE_VERSION",
    "build_arsenal_non_incorporated_register",
    "build_arsenal_protocol_probe",
    "write_arsenal_protocol_probe",
]
