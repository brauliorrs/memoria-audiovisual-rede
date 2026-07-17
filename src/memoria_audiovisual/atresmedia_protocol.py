from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

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


ATRESMEDIA_PROTOCOL_FILENAME = "observatorio_protocolo_atresmedia.csv"
ATRESMEDIA_PROTOCOL_RULE_VERSION = "2026-06-atresmedia-protocol-v1"
ATRESMEDIA_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
ATRESMEDIA_ACCESS_CATEGORY = "banco_privado_de_imagens_e_videos_com_acesso_restrito_e_pagamento"

ATRESMEDIA_HOME_URL = "https://www.atresmedia.com/"
ATRESMEDIA_FIAT_MEMBERS_URL = "https://fiatifta.org/membership/members/"
ATRESMEDIA_AWARD_URL = "https://fiatifta.org/awards-2021/"
ATRESMEDIA_SALES_PORTAL_URL = "https://portalventas.atresmedia.com/"
ATRESMEDIA_ATRESPLAYER_URL = "https://www.atresplayer.com/"
ATRESMEDIA_API_BASE_URL = "https://portalventas.atresmedia.com/apiportalventas"


@dataclass(frozen=True)
class AtresmediaProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


ATRESMEDIA_PROTOCOL_PROBES = [
    AtresmediaProbe(
        probe="fiat_member_page",
        probe_label="Ficha FIAT/IFTA de membros",
        method="GET",
        url=ATRESMEDIA_FIAT_MEMBERS_URL,
        evidence_signal="directory_reference",
        methodological_note="Confirma Atresmedia como membro de rede internacional de arquivos de televisão.",
    ),
    AtresmediaProbe(
        probe="official_home",
        probe_label="Site oficial Atresmedia",
        method="GET",
        url=ATRESMEDIA_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Confirma o grupo audiovisual sem tratar a home institucional como catálogo arquivístico.",
    ),
    AtresmediaProbe(
        probe="archive_award_page",
        probe_label="Prêmio FIAT/IFTA de gestão de arquivo",
        method="GET",
        url=ATRESMEDIA_AWARD_URL,
        evidence_signal="archive_management_reference",
        methodological_note="Verifica evidência independente sobre gestão documental e arquivo audiovisual da Atresmedia.",
    ),
    AtresmediaProbe(
        probe="sales_portal_home",
        probe_label="PortalVentas Atresmedia",
        method="GET",
        url=ATRESMEDIA_SALES_PORTAL_URL,
        evidence_signal="archive_sales_portal",
        methodological_note="Testa o portal oficial de venda/licenciamento do arquivo sem autenticação.",
    ),
    AtresmediaProbe(
        probe="sales_portal_bundle",
        probe_label="Aplicação pública do PortalVentas",
        method="BUNDLE",
        url=ATRESMEDIA_SALES_PORTAL_URL,
        evidence_signal="portal_app_bundle",
        methodological_note="Inspeciona a aplicação pública para identificar fluxo de compra, login e endpoints disponíveis.",
    ),
    AtresmediaProbe(
        probe="api_versions",
        probe_label="API pública de versões do PortalVentas",
        method="GET",
        url=f"{ATRESMEDIA_API_BASE_URL}/Versiones/GetVersiones",
        evidence_signal="public_api_route",
        methodological_note="Verifica se existe API pública; esta rota expõe versões do sistema, não registros audiovisuais.",
    ),
    AtresmediaProbe(
        probe="api_form",
        probe_label="API de formulário do PortalVentas",
        method="GET",
        url=f"{ATRESMEDIA_API_BASE_URL}/ventana/GetFormulario",
        evidence_signal="restricted_api_route",
        methodological_note="Testa rota funcional do portal para distinguir API técnica de catálogo público.",
    ),
    AtresmediaProbe(
        probe="api_files",
        probe_label="API de arquivos de solicitação",
        method="GET",
        url=f"{ATRESMEDIA_API_BASE_URL}/Solicitud/GetFicheros",
        evidence_signal="restricted_api_route",
        methodological_note="Testa se a rota de arquivos é pública ou depende de solicitação/autenticação.",
    ),
    AtresmediaProbe(
        probe="atresplayer_home",
        probe_label="Atresplayer",
        method="GET",
        url=ATRESMEDIA_ATRESPLAYER_URL,
        evidence_signal="streaming_platform",
        methodological_note="Distingue plataforma de streaming de corpus arquivístico público.",
    ),
]


def _request_text(url, sample_bytes=524288):
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


def _fetch_portal_bundle(url):
    portal = _request_text(url)
    if portal.get("error") or not portal.get("text"):
        return portal
    soup = BeautifulSoup(portal["text"], "html.parser")
    scripts = [
        urljoin(portal.get("final_url") or url, script.get("src", ""))
        for script in soup.find_all("script", src=True)
    ]
    main_scripts = [script_url for script_url in scripts if "/main." in script_url or script_url.endswith("main.js")]
    bundle_url = main_scripts[-1] if main_scripts else (scripts[-1] if scripts else "")
    if not bundle_url:
        portal["error"] = "script principal do PortalVentas não encontrado"
        return portal
    return _request_text(bundle_url, sample_bytes=1048576)


def fetch_atresmedia_probe(url, method="GET", sample_bytes=524288):
    if str(method or "GET").upper() == "BUNDLE":
        return _fetch_portal_bundle(url)
    return _request_text(url, sample_bytes=sample_bytes)


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _page_signals(content):
    raw = str(content or "")
    soup_text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    text = _clean_text(f"{soup_text} {raw}").lower()
    api_endpoints = set(re.findall(r"['\"]([A-Za-z]+/[A-Za-z0-9]+)['\"]", raw))
    return {
        "atresmedia_present": "atresmedia" in text,
        "fiat_member_present": "fiat/ifta" in text and "atresmedia" in text,
        "archive_terms": any(
            term in text
            for term in (
                "television archives",
                "atresmedia archive",
                "archivo de atresmedia",
                "archivo documental",
                "gestión documental",
                "media cataloguing",
                "documentación",
            )
        ),
        "audiovisual_terms": any(term in text for term in ("audiovisual", "video", "televisión", "television")),
        "sales_terms": any(
            term in text
            for term in ("compra", "presupuesto", "contrato", "licencia", "marca de agua", "baja resolución")
        ),
        "auth_terms": any(
            term in text
            for term in ("oidc", "accesstoken", "isauthenticated", "portalventas-identity", "authorize")
        ),
        "js_app_shell": "<app-root" in text or "portalimagenesweb" in text,
        "coverage_since_1989": "1989" in text and ("noviembre" in text or "november" in text),
        "processed_video_hours": bool(re.search(r"(16\.000|19\.000|16000|19000).{0,30}horas?.{0,20}v[íi]deo", text)),
        "api_base_detected": "apiportalventas" in text,
        "api_endpoints_total": len(api_endpoints),
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"atresmedia={'sim' if signals['atresmedia_present'] else 'nao'}",
            f"fiat_ifta={'sim' if signals['fiat_member_present'] else 'nao'}",
            f"arquivo={'sim' if signals['archive_terms'] else 'nao'}",
            f"audiovisual={'sim' if signals['audiovisual_terms'] else 'nao'}",
            f"comercial={'sim' if signals['sales_terms'] else 'nao'}",
            f"autenticacao={'sim' if signals['auth_terms'] else 'nao'}",
            f"app_js={'sim' if signals['js_app_shell'] else 'nao'}",
            f"cobertura_1989={'sim' if signals['coverage_since_1989'] else 'nao'}",
            f"endpoints_api={signals['api_endpoints_total']}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if probe.probe.startswith("api_") and access_status == "restrito_ou_bloqueado":
        return "api_do_portal_requer_autenticacao", "manter_fora_do_corpus_ativo_sem_login_ou_licenca"
    if access_status != "acessivel":
        return "rota_indisponivel_ou_restrita_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe == "api_versions":
        return "api_publica_apenas_operacional_sem_catalogo", "nao_usar_como_corpus_audiovisual"
    if probe.probe == "sales_portal_bundle" and signals.get("auth_terms") and signals.get("sales_terms"):
        return "portal_de_arquivo_com_fluxo_comercial_autenticado", "buscar_catalogo_publico_ou_acordo_documentado"
    if probe.probe == "sales_portal_home" and signals.get("js_app_shell"):
        return "portal_publico_exige_aplicacao_js", "inspecionar_bundle_e_rotas_autenticadas"
    if probe.probe == "archive_award_page" and signals.get("archive_terms"):
        return "arquivo_audiovisual_confirmado_sem_catalogo_publico", "validar_rota_publica_de_registros"
    if probe.probe == "fiat_member_page" and signals.get("fiat_member_present"):
        return "membro_fiat_ifta_confirmado", "avaliar_rota_catalografica_propria"
    if probe.probe == "atresplayer_home":
        return "plataforma_streaming_nao_equivale_a_catalogo_arquivistico", "nao_substituir_arquivo_por_streaming"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_atresmedia_probe):
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
        "code": "fiat-atresmedia",
        "label": "Atresmedia",
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
        "rule_version": ATRESMEDIA_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_atresmedia_protocol_probe(fetcher=fetch_atresmedia_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in ATRESMEDIA_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=ATRESMEDIA_PROTOCOL_COLUMNS)


def build_atresmedia_non_incorporated_register(protocol_df):
    auth_restricted_total = 0
    endpoint_total = 0
    if protocol_df is not None and not protocol_df.empty:
        auth_restricted_total = int(
            (
                protocol_df["protocol_conclusion"].astype(str)
                == "api_do_portal_requer_autenticacao"
            ).sum()
        )
        for observed_value in protocol_df["observed_value"].astype(str):
            match = re.search(r"endpoints_api=(\d+)", observed_value)
            if match:
                endpoint_total = max(endpoint_total, int(match.group(1)))

    return pd.DataFrame(
        [
            {
                "unit_code": "fiat-atresmedia",
                "unit_label": "Atresmedia",
                "unit_type": "instituicao_televisiva_com_acervo_audiovisual",
                "territorial_scope": "Espanha",
                "access_category": ATRESMEDIA_ACCESS_CATEGORY,
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A Atresmedia tem acervo audiovisual confirmado e portal oficial de banco privado de imagens "
                    "e vídeos, mas a rota pública funciona como fluxo comercial/autenticado de solicitação, "
                    "orçamento, visionamento e licenciamento pago. "
                    "Não foi encontrado catálogo público ou endpoint aberto de registros audiovisuais completo."
                ),
                "collection_route_attempted": (
                    "Lista de membros FIAT/IFTA, site oficial da Atresmedia, página FIAT/IFTA do prêmio de gestão "
                    "de arquivo, PortalVentas, aplicação JavaScript do PortalVentas, endpoints da API e Atresplayer."
                ),
                "attempt_summary": (
                    f"Foram detectados até {endpoint_total} endpoints internos na aplicação do PortalVentas. "
                    f"{auth_restricted_total} rotas operacionais testadas exigiram autenticação. "
                    "A rota pública de versões respondeu, mas não expõe catálogo audiovisual."
                ),
                "methodological_explanation": (
                    "A negativa registra uma categoria própria de acesso restrito e monetizado, não ausência de "
                    "acervo. Para o MVP, o organismo só incorpora corpus quando consegue materializar registros "
                    "públicos de modo completo e reprodutível."
                ),
                "evidence_status": "banco_privado_de_imagens_e_videos_confirmado_com_acesso_restrito_pago",
                "protocol_status": "banco_privado_confirmado_sem_catalogo_publico_coletavel",
                "next_step": "buscar catálogo público, endpoint de metadados, sitemap, recorte aberto ou acordo documentado",
                "blocks_expansion": False,
                "rule_version": ATRESMEDIA_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_atresmedia_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_atresmedia_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_atresmedia_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / ATRESMEDIA_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_atresmedia_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "ATRESMEDIA_PROTOCOL_COLUMNS",
    "ATRESMEDIA_ACCESS_CATEGORY",
    "ATRESMEDIA_PROTOCOL_FILENAME",
    "ATRESMEDIA_PROTOCOL_PROBES",
    "ATRESMEDIA_PROTOCOL_RULE_VERSION",
    "build_atresmedia_non_incorporated_register",
    "build_atresmedia_protocol_probe",
    "write_atresmedia_protocol_probe",
]
