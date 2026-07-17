from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import (
    BNFA_EFG_COLLECTION_URL,
    BNFA_EFG_PAGE_URL,
    BNFA_E_CATALOGUE_BG_URL,
    BNFA_E_CATALOGUE_EN_URL,
    BNFA_FILM_COLLECTION_URL,
    BNFA_FILM_LIBRARY_URL,
    BNFA_HOME_HTTP_URL,
    BNFA_HOME_HTTPS_URL,
    BNFA_SEARCH_EN_URL,
    HEADERS,
    OUTPUT_DIR,
)
from .europe_closure import (
    EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    merge_existing_excluded_units,
)
from .european_aggregators import classify_probe_access_status, detect_js_cookie_requirement
from .european_protocols import FRANCEARCHIVES_PROTOCOL_COLUMNS, detect_js_redirect, utcnow_iso


BNFA_PROTOCOL_FILENAME = "observatorio_protocolo_bnfa.csv"
BNFA_PROTOCOL_RULE_VERSION = "2026-06-bnfa-protocol-v1"
BNFA_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS


@dataclass(frozen=True)
class BnfaProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str
    payload: dict | None = None


BNFA_PROTOCOL_PROBES = [
    BnfaProbe(
        probe="official_home_https",
        probe_label="Site oficial em HTTPS",
        method="GET",
        url=BNFA_HOME_HTTPS_URL,
        evidence_signal="https_route",
        methodological_note="Testa a rota HTTPS divulgada por diretórios externos; nesta infraestrutura pode falhar por TLS.",
    ),
    BnfaProbe(
        probe="official_home_http",
        probe_label="Site oficial em HTTP",
        method="GET",
        url=BNFA_HOME_HTTP_URL,
        evidence_signal="official_site",
        methodological_note="Confirma a presença institucional no domínio oficial por HTTP.",
    ),
    BnfaProbe(
        probe="film_library",
        probe_label="Página institucional da filmoteca",
        method="GET",
        url=BNFA_FILM_LIBRARY_URL,
        evidence_signal="film_archive_reference",
        methodological_note="Verifica a página que descreve missão, acesso, preservação e responsabilidades do arquivo fílmico.",
    ),
    BnfaProbe(
        probe="film_collection",
        probe_label="Film Collection",
        method="GET",
        url=BNFA_FILM_COLLECTION_URL,
        evidence_signal="collection_counts",
        methodological_note="Verifica números declarados do acervo fílmico sem inferir disponibilidade pública online.",
    ),
    BnfaProbe(
        probe="e_catalogue_en",
        probe_label="e-Catalogue em inglês",
        method="GET",
        url=BNFA_E_CATALOGUE_EN_URL,
        evidence_signal="catalog_route",
        methodological_note="Testa a rota oficial de e-Catalogue para verificar se há registros ou vídeos públicos.",
    ),
    BnfaProbe(
        probe="e_catalogue_bg",
        probe_label="e-Catalogue em búlgaro",
        method="GET",
        url=BNFA_E_CATALOGUE_BG_URL,
        evidence_signal="catalog_route",
        methodological_note="Testa a versão búlgara do e-Catalogue; ela explicita quando a página está em desenvolvimento.",
    ),
    BnfaProbe(
        probe="search_film_sample",
        probe_label="Busca interna por film",
        method="POST",
        url=BNFA_SEARCH_EN_URL,
        evidence_signal="search_route",
        methodological_note="Testa a busca interna leve para distinguir catálogo vazio de busca indisponível.",
        payload={"keywords": "film"},
    ),
    BnfaProbe(
        probe="efg_partner_page",
        probe_label="Página BNFA no European Film Gateway",
        method="GET",
        url=BNFA_EFG_PAGE_URL,
        evidence_signal="aggregator_partner_reference",
        methodological_note="Confirma a identificação da BNFA como parceira/contribuidora do EFG.",
    ),
    BnfaProbe(
        probe="efg_collection_link",
        probe_label="Link de coleção BNFA no EFG",
        method="GET",
        url=BNFA_EFG_COLLECTION_URL,
        evidence_signal="aggregator_collection_route",
        methodological_note="Testa se o link público para a coleção BNFA no EFG oferece rota coletável estável.",
    ),
]


def _decode_response(response):
    content = response.content or b""
    head = content[:1000].lower()
    if b"windows-1251" in head:
        encoding = "windows-1251"
    elif b"windows-1252" in head:
        encoding = "windows-1252"
    else:
        encoding = response.encoding or response.apparent_encoding or "utf-8"
    return content.decode(encoding, errors="replace")


def fetch_bnfa_probe(url, method="GET", payload=None, sample_bytes=524288):
    response = None
    error = ""
    try:
        method = str(method or "GET").upper()
        request_kwargs = {
            "headers": {**HEADERS, "Accept-Language": "en,bg;q=0.9,pt-BR;q=0.6"},
            "timeout": (8, 12),
            "allow_redirects": True,
        }
        if method == "POST":
            response = requests.post(url, data=payload or {}, **request_kwargs)
        else:
            response = requests.get(url, **request_kwargs)
        text = _decode_response(response)[:sample_bytes]
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


def _page_signals(text, final_url=""):
    raw = str(text or "")
    normalized = _clean_text(f"{BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True)} {raw}").lower()
    video_matches = re.findall(r"https?://[^\"'\s<>]+?\.(?:mp4|m3u8|webm|mov|avi|m4v)", raw, flags=re.IGNORECASE)
    video_total_match = re.search(r"videos?\s*\(([\d,\.]+)\s+results?\)", normalized)
    efg_video_results_total = int(re.sub(r"\D", "", video_total_match.group(1))) if video_total_match else 0
    return {
        "bnfa_present": "bulgarian national film archive" in normalized
        or "bulgarian national film archive" in str(final_url).lower()
        or "българска национална филмотека" in normalized,
        "film_archive_terms": any(term in normalized for term in ("film archive", "film collection", "film reels", "film heritage")),
        "declared_15000_titles": "15 000" in normalized or "15,000" in normalized or "15000" in normalized,
        "declared_videotapes": "3000 videotapes" in normalized or "3 000 videotapes" in normalized,
        "catalog_under_development": "process of development" in normalized or "процес на разработка" in normalized,
        "page_not_available": "the page is not available" in normalized,
        "video_files": len(video_matches),
        "video_embed_terms": any(term in raw.lower() for term in ("<video", "youtube.com/embed", "player.vimeo.com")),
        "efg_video_results_total": efg_video_results_total,
        "efg_partner_page": "view bnfa collection" in normalized or "selected collections of 40 film archives" in normalized,
        "efg_collection_redirected_to_news": "/news" in str(final_url).lower() and "news" in normalized,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"bnfa={'sim' if signals['bnfa_present'] else 'nao'}",
            f"arquivo_filmico={'sim' if signals['film_archive_terms'] else 'nao'}",
            f"15000_titulos={'sim' if signals['declared_15000_titles'] else 'nao'}",
            f"videotapes={'sim' if signals['declared_videotapes'] else 'nao'}",
            f"catalogo_em_desenvolvimento={'sim' if signals['catalog_under_development'] else 'nao'}",
            f"pagina_indisponivel={'sim' if signals['page_not_available'] else 'nao'}",
            f"arquivos_video={signals['video_files']}",
            f"embed_video={'sim' if signals['video_embed_terms'] else 'nao'}",
            f"efg_videos={signals['efg_video_results_total']}",
            f"efg_parceiro={'sim' if signals['efg_partner_page'] else 'nao'}",
            f"efg_link_news={'sim' if signals['efg_collection_redirected_to_news'] else 'nao'}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if probe.probe == "official_home_https" and access_status == "falha_tecnica":
        return "https_indisponivel_http_precisa_ser_testado", "usar_rota_http_oficial_e_registrar_fragilidade_tls"
    if access_status != "acessivel":
        return "rota_indisponivel_ou_instavel_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe == "efg_collection_link" and signals.get("efg_video_results_total"):
        return "colecao_publica_efg_com_resultados_video_confirmada", "incorporar_como_corpus_mediado_por_efg"
    if signals.get("video_files") or signals.get("video_embed_terms"):
        return "sinal_de_video_publico_exige_validacao_total", "validar_se_o_sinal_representa_video_de_acervo"
    if signals.get("catalog_under_development") or signals.get("page_not_available"):
        return "catalogo_publico_indisponivel_ou_em_desenvolvimento", "manter_fora_do_corpus_ativo_ate_haver_catalogo_publico"
    if probe.probe == "efg_collection_link" and signals.get("efg_collection_redirected_to_news"):
        return "link_efg_para_colecao_redireciona_sem_rota_coletavel", "retestar_efg_ou_europeana_antes_de_incorporar"
    if signals.get("declared_15000_titles") and signals.get("film_archive_terms"):
        return "acervo_filmico_confirmado_sem_video_publico_coletavel", "nao_incorporar_sem_rota_publica_de_registros_ou_player"
    if probe.probe == "efg_partner_page" and signals.get("efg_partner_page"):
        return "parceria_efg_confirmada_sem_rota_de_colecao_estavel", "usar_como_evidencia_institucional_e_nao_como_corpus"
    if signals.get("bnfa_present") or signals.get("film_archive_terms"):
        return "referencia_institucional_confirma_arquivo_audiovisual", "validar_catalogo_publico_antes_de_incorporar"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_bnfa_probe):
    fetched = fetcher(probe.url, probe.method, probe.payload)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    signals = _page_signals(text, fetched.get("final_url", "")) if text else {}
    conclusion, next_step = _build_protocol_conclusion(probe, access_status, signals)
    return {
        "code": "fiaf-bulgarian-national-film-archive",
        "label": "Bulgarian National Film Archive",
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
        "rule_version": BNFA_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_bnfa_protocol_probe(fetcher=fetch_bnfa_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in BNFA_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=BNFA_PROTOCOL_COLUMNS)


def build_bnfa_non_incorporated_register(protocol_df):
    conclusions = set(protocol_df["protocol_conclusion"].astype(str)) if protocol_df is not None and not protocol_df.empty else set()
    if "colecao_publica_efg_com_resultados_video_confirmada" in conclusions:
        return pd.DataFrame(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)
    has_declared_collection = "acervo_filmico_confirmado_sem_video_publico_coletavel" in conclusions
    has_catalog_block = "catalogo_publico_indisponivel_ou_em_desenvolvimento" in conclusions
    has_efg_block = "link_efg_para_colecao_redireciona_sem_rota_coletavel" in conclusions
    return pd.DataFrame(
        [
            {
                "unit_code": "fiaf-bulgarian-national-film-archive",
                "unit_label": "Bulgarian National Film Archive",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Bulgária",
                "access_category": "catalogo_publico_indisponivel_ou_em_desenvolvimento",
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A Bulgarian National Film Archive é arquivo audiovisual/fílmico confirmado, mas a rota pública "
                    "do e-Catalogue não materializou registros audiovisuais coletáveis nem player público. A versão "
                    "búlgara informa página em desenvolvimento; a busca interna retorna página indisponível; e o link "
                    "da coleção BNFA no EFG redireciona sem entregar rota estável de coleção."
                ),
                "collection_route_attempted": (
                    "Site oficial HTTPS, site oficial HTTP, Film Library, Film Collection, e-Catalogue em inglês e "
                    "búlgaro, busca interna por 'film', página parceira no European Film Gateway e link público da "
                    "coleção BNFA no EFG."
                ),
                "attempt_summary": (
                    "Acervo fílmico declarado: "
                    f"{'confirmado' if has_declared_collection else 'não confirmado na rodada'}; "
                    "catálogo público: "
                    f"{'indisponível/em desenvolvimento' if has_catalog_block else 'sem bloqueio explícito'}; "
                    "rota EFG da coleção: "
                    f"{'sem rota coletável estável' if has_efg_block else 'sem negativa específica'}."
                ),
                "methodological_explanation": (
                    "A negativa é técnica e metodológica, não ontológica: há acervo audiovisual, mas o organismo "
                    "não deve incorporar corpus vazio, instável ou apenas declaratório. A unidade permanece "
                    "protocolada fora do corpus ativo até existir catálogo público reprodutível, endpoint, sitemap "
                    "ou recorte agregado estável com registros audiovisuais."
                ),
                "evidence_status": "arquivo_filmico_confirmado_sem_rota_publica_de_video_coletavel",
                "protocol_status": "catalogo_publico_indisponivel_ou_em_desenvolvimento",
                "next_step": "retestar e-Catalogue, busca interna, EFG e Europeana em ciclo futuro antes de incorporar",
                "blocks_expansion": False,
                "rule_version": BNFA_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_bnfa_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_bnfa_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_bnfa_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / BNFA_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    non_incorporated_df = build_bnfa_non_incorporated_register(protocol_df)
    if non_incorporated_df.empty:
        existing_path = output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME
        excluded_df = pd.read_csv(existing_path) if existing_path.exists() else pd.DataFrame(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)
        if not excluded_df.empty and "unit_code" in excluded_df.columns:
            excluded_df = excluded_df.loc[
                excluded_df["unit_code"].astype(str) != "fiaf-bulgarian-national-film-archive"
            ].copy()
            excluded_df = excluded_df.reindex(columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS)
    else:
        excluded_df = merge_existing_excluded_units(output_dir, non_incorporated_df)
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "BNFA_PROTOCOL_COLUMNS",
    "BNFA_PROTOCOL_FILENAME",
    "BNFA_PROTOCOL_PROBES",
    "BNFA_PROTOCOL_RULE_VERSION",
    "build_bnfa_non_incorporated_register",
    "build_bnfa_protocol_probe",
    "write_bnfa_protocol_probe",
]
