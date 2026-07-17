from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import (
    CNCAFF_EFG_PAGE_URL,
    CNCAFF_EFG_SEARCH_URL,
    CNCAFF_HOME_URL,
    CNCAFF_LEGACY_URL,
    CNCAFF_LISE_URL,
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


CNCAFF_PROTOCOL_FILENAME = "observatorio_protocolo_cnc_aff.csv"
CNCAFF_PROTOCOL_RULE_VERSION = "2026-06-cnc-aff-protocol-v1"
CNCAFF_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS


@dataclass(frozen=True)
class CncAffProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


CNCAFF_PROTOCOL_PROBES = [
    CncAffProbe(
        probe="official_dpc_page",
        probe_label="Página oficial da Direction du patrimoine cinématographique do CNC",
        method="GET",
        url=CNCAFF_HOME_URL,
        evidence_signal="official_film_archive_reference",
        methodological_note="Confirma a existência institucional do arquivo fílmico sem tratar a página como catálogo coletável.",
    ),
    CncAffProbe(
        probe="efg_partner_page",
        probe_label="Página do CNC/AFF como contribuinte no European Film Gateway",
        method="GET",
        url=CNCAFF_EFG_PAGE_URL,
        evidence_signal="aggregator_partner_reference",
        methodological_note="Verifica a referência pública do CNC/AFF como parceiro/contribuidor do EFG.",
    ),
    CncAffProbe(
        probe="efg_collection_first_page",
        probe_label="Primeira página da coleção CNC/AFF no EFG",
        method="GET",
        url=CNCAFF_EFG_SEARCH_URL,
        evidence_signal="aggregator_collection_route",
        methodological_note="Testa a superfície pública que anuncia resultados de vídeo do CNC/AFF no EFG.",
    ),
    CncAffProbe(
        probe="efg_collection_page_2",
        probe_label="Paginação da coleção CNC/AFF no EFG",
        method="GET",
        url=f"{CNCAFF_EFG_SEARCH_URL}?page=1%2C0%2C0",
        evidence_signal="aggregator_pagination_route",
        methodological_note="Testa se a paginação da coleção permite materialização completa por coleta estática.",
    ),
    CncAffProbe(
        probe="legacy_domain",
        probe_label="Domínio histórico cnc-aff.fr",
        method="GET",
        url=CNCAFF_LEGACY_URL,
        evidence_signal="legacy_domain",
        methodological_note="Registra a situação da rota histórica divulgada por fontes externas.",
    ),
    CncAffProbe(
        probe="lise_catalog",
        probe_label="Rota LISE/CNC",
        method="GET",
        url=CNCAFF_LISE_URL,
        evidence_signal="legacy_catalog_route",
        methodological_note="Testa a rota LISE/CNC mencionada como catálogo histórico.",
    ),
]


def _decode_response(response):
    content = response.content or b""
    encoding = response.encoding or response.apparent_encoding or "utf-8"
    return content.decode(encoding, errors="replace")


def _maybe_follow_efg_validation(session, response, request_kwargs):
    if not response.is_redirect:
        return response

    location = urljoin(response.url, response.headers.get("Location", ""))
    response.close()
    if "/validate-browser" in location:
        validation = session.get(location, **request_kwargs)
        if validation.is_redirect:
            location = urljoin(validation.url, validation.headers.get("Location", ""))
        else:
            return validation
        validation.close()
    return session.get(location, **{**request_kwargs, "allow_redirects": True})


def fetch_cnc_aff_probe(url, method="GET", sample_bytes=524288):
    response = None
    error = ""
    text = ""
    is_efg = "europeanfilmgateway.eu" in str(url)
    attempts = 2 if is_efg else 1
    for _ in range(attempts):
        try:
            session = requests.Session()
            request_kwargs = {
                "headers": {**HEADERS, "Accept-Language": "fr,en;q=0.9,pt-BR;q=0.6"},
                "timeout": (8, 20 if is_efg else 12),
                "allow_redirects": False,
            }
            response = session.get(url, **request_kwargs)
            response = _maybe_follow_efg_validation(session, response, request_kwargs)
            text = _decode_response(response)[:sample_bytes]
            error = ""
            break
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


def _parse_int(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return int(digits) if digits else 0


def _page_signals(text, final_url=""):
    raw = str(text or "")
    soup = BeautifulSoup(raw, "html.parser")
    normalized = _clean_text(f"{soup.get_text(' ', strip=True)} {raw}").lower()
    efg_video_total_match = re.search(r"videos?\s*\(([\d\s,\.]+)\s+results?\)", normalized)
    detail_links = {
        anchor.get("href", "")
        for anchor in soup.find_all("a", href=True)
        if "cnc::" in anchor.get("href", "").lower() or "cnc::" in anchor.get_text(" ", strip=True).lower()
    }
    return {
        "cnc_present": any(
            term in normalized
            for term in (
                "centre national du cinéma",
                "centre national du cinema",
                "archives françaises du film",
                "archives francaises du film",
                "cnc",
            )
        ),
        "film_archive_terms": any(
            term in normalized
            for term in (
                "patrimoine cinématographique",
                "patrimoine cinematographique",
                "archives du film",
                "film archives",
                "conservation",
                "restauration",
                "catalogage",
            )
        ),
        "declared_110000_titles": any(term in normalized for term in ("110 000", "110,000", "110000")),
        "online_catalog_terms": any(term in normalized for term in ("catalogue en ligne", "online catalog", "online catalogue")),
        "efg_partner_page": "view cnc collections" in normalized or "cnc collections" in normalized,
        "efg_video_results_total": _parse_int(efg_video_total_match.group(1)) if efg_video_total_match else 0,
        "efg_detail_links": len(detail_links),
        "player_detected": bool(soup.find(["iframe", "video", "source"])),
        "validate_browser": "/validate-browser" in str(final_url).lower() or "/validate-browser" in raw.lower(),
        "service_unavailable": "service unavailable" in normalized or "503" in normalized,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"cnc={'sim' if signals['cnc_present'] else 'nao'}",
            f"arquivo_filmico={'sim' if signals['film_archive_terms'] else 'nao'}",
            f"110000_titulos={'sim' if signals['declared_110000_titles'] else 'nao'}",
            f"catalogo_online={'sim' if signals['online_catalog_terms'] else 'nao'}",
            f"parceiro_efg={'sim' if signals['efg_partner_page'] else 'nao'}",
            f"efg_videos={signals['efg_video_results_total']}",
            f"links_detalhe_efg={signals['efg_detail_links']}",
            f"player={'sim' if signals['player_detected'] else 'nao'}",
            f"validacao_browser={'sim' if signals['validate_browser'] else 'nao'}",
            f"servico_indisponivel={'sim' if signals['service_unavailable'] else 'nao'}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        if probe.probe == "legacy_domain":
            return "dominio_legado_indisponivel_na_rodada", "manter_como_rota_historica_nao_coletavel"
        if probe.probe == "lise_catalog":
            return "catalogo_lise_indisponivel_na_rodada", "retestar_lise_em_ciclo_futuro_sem_incorporar"
        if probe.probe == "efg_collection_page_2":
            return "paginacao_efg_instavel_na_coleta_estatica", "nao_incorporar_sem_materializacao_completa"
        if probe.probe.startswith("efg_"):
            return "rota_efg_indisponivel_ou_instavel_na_rodada", "retestar_efg_antes_de_incorporar"
        return "rota_oficial_indisponivel_na_rodada", "retestar_sem_promover_a_corpus"

    if probe.probe == "official_dpc_page" and (
        signals.get("declared_110000_titles") or signals.get("film_archive_terms")
    ):
        return "pagina_oficial_confirma_arquivo_filmico", "usar_como_evidencia_institucional"

    if probe.probe == "efg_partner_page" and (signals.get("efg_partner_page") or signals.get("cnc_present")):
        return "pagina_efg_confirma_parceria_cnc_aff", "usar_como_evidencia_de_rota_mediada"

    if probe.probe == "efg_collection_first_page" and (
        signals.get("efg_video_results_total") or signals.get("efg_detail_links")
    ):
        return (
            "colecao_efg_identificada_com_resultados_video",
            "estabilizar_paginacao_e_materializar_registros_antes_de_incorporar",
        )

    if probe.probe == "efg_collection_page_2":
        if signals.get("validate_browser") or not signals.get("efg_detail_links"):
            return "paginacao_efg_instavel_na_coleta_estatica", "nao_incorporar_sem_materializacao_completa"
        return "paginacao_efg_respondeu_na_sondagem", "validar_materializacao_completa_antes_de_incorporar"

    if signals.get("player_detected"):
        return "player_publico_detectado_a_validar", "validar_se_o_player_representa_acervo_cnc_aff"

    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_cnc_aff_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text) or detect_js_redirect(text),
        fetched.get("error", ""),
    )
    signals = _page_signals(text, fetched.get("final_url", "")) if text else {}
    conclusion, next_step = _build_protocol_conclusion(probe, access_status, signals)
    return {
        "code": "fiaf-cnc-aff",
        "label": "CNC - Archives françaises du film",
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
        "rule_version": CNCAFF_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_cnc_aff_protocol_probe(fetcher=fetch_cnc_aff_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in CNCAFF_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=CNCAFF_PROTOCOL_COLUMNS)


def _observed_total(protocol_df, key):
    if protocol_df is None or protocol_df.empty:
        return 0
    pattern = re.compile(rf"{re.escape(key)}=(\d+)")
    totals = []
    for value in protocol_df["observed_value"].astype(str):
        match = pattern.search(value)
        if match:
            totals.append(int(match.group(1)))
    return max(totals) if totals else 0


def build_cnc_aff_non_incorporated_register(protocol_df):
    conclusions = set(protocol_df["protocol_conclusion"].astype(str)) if protocol_df is not None and not protocol_df.empty else set()
    efg_announced_total = _observed_total(protocol_df, "efg_videos")
    efg_detail_links = _observed_total(protocol_df, "links_detalhe_efg")
    efg_access_unstable = False
    if protocol_df is not None and not protocol_df.empty:
        efg_rows = protocol_df[protocol_df["probe"].astype(str).str.startswith("efg_collection")]
        efg_access_unstable = bool((efg_rows["access_status"].astype(str) != "acessivel").any())
    official_confirmed = "pagina_oficial_confirma_arquivo_filmico" in conclusions
    efg_confirmed = "colecao_efg_identificada_com_resultados_video" in conclusions or bool(efg_announced_total)
    page_unstable = "paginacao_efg_instavel_na_coleta_estatica" in conclusions or efg_access_unstable
    legacy_unavailable = "dominio_legado_indisponivel_na_rodada" in conclusions
    lise_unavailable = "catalogo_lise_indisponivel_na_rodada" in conclusions
    return pd.DataFrame(
        [
            {
                "unit_code": "fiaf-cnc-aff",
                "unit_label": "CNC - Archives françaises du film",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "França",
                "access_category": "rota_publica_mediada_instavel",
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo no MVP nesta rodada",
                "negative_reason": (
                    "A página oficial confirma o arquivo fílmico e o European Film Gateway anuncia coleção "
                    "pública com resultados de vídeo, mas a coleta completa não se materializou de forma "
                    "reprodutível. A paginação/rota mediada pelo EFG apresentou instabilidade na coleta "
                    "estática; o domínio histórico não respondeu e a rota LISE ficou indisponível."
                ),
                "collection_route_attempted": (
                    "Página oficial CNC/DPC, página parceira do CNC/AFF no European Film Gateway, primeira "
                    "página da coleção CNC/AFF no EFG, paginação da coleção, domínio histórico cnc-aff.fr "
                    "e rota LISE/CNC."
                ),
                "attempt_summary": (
                    "Arquivo fílmico oficial: "
                    f"{'confirmado' if official_confirmed else 'não confirmado na rodada'}; "
                    "coleção EFG com vídeos: "
                    f"{'confirmada' if efg_confirmed else 'não confirmada'}"
                    f"{f' ({efg_announced_total} resultados anunciados; {efg_detail_links} links na amostra)' if efg_announced_total or efg_detail_links else ''}; "
                    "paginação EFG: "
                    f"{'instável' if page_unstable else 'sem bloqueio específico na sondagem'}; "
                    "domínio legado: "
                    f"{'indisponível' if legacy_unavailable else 'sem negativa específica'}; "
                    "LISE: "
                    f"{'indisponível' if lise_unavailable else 'sem negativa específica'}."
                ),
                "methodological_explanation": (
                    "A negativa é técnica e metodológica, não ontológica: há evidência de arquivo audiovisual "
                    "e de registros de vídeo mediados pelo EFG. O organismo, porém, só incorpora corpus quando "
                    "consegue materializar registros completos, verificáveis e reexecutáveis. Portanto, o CNC/AFF "
                    "permanece documentado e será retestado, sem ser contado como corpus ativo."
                ),
                "evidence_status": "arquivo_filmico_confirmado_com_rota_efg_publica_instavel",
                "protocol_status": "rota_publica_mediada_instavel_sem_materializacao_completa",
                "next_step": "retestar EFG, LISE e possíveis endpoints públicos antes de incorporar",
                "blocks_expansion": False,
                "rule_version": CNCAFF_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_cnc_aff_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_cnc_aff_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_cnc_aff_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / CNCAFF_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_cnc_aff_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "CNCAFF_PROTOCOL_COLUMNS",
    "CNCAFF_PROTOCOL_FILENAME",
    "CNCAFF_PROTOCOL_PROBES",
    "CNCAFF_PROTOCOL_RULE_VERSION",
    "build_cnc_aff_non_incorporated_register",
    "build_cnc_aff_protocol_probe",
    "write_cnc_aff_protocol_probe",
]
