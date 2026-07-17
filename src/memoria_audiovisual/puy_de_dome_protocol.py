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


PUY_DE_DOME_PROTOCOL_FILENAME = "observatorio_protocolo_puy_de_dome.csv"
PUY_DE_DOME_PROTOCOL_RULE_VERSION = "2026-07-puy-de-dome-protocol-v1"
PUY_DE_DOME_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
PUY_DE_DOME_ACCESS_CATEGORY = "arquivo_audiovisual_identificado_com_rota_publica_bloqueada_por_verificacao_antirobo"

PUY_DE_DOME_HOME_URL = "https://www.archivesdepartementales.puy-de-dome.fr/"
PUY_DE_DOME_ARCHIVES_ET_CINEMA_URL = "https://www.archivesdepartementales.puy-de-dome.fr/n/archives-et-cinema/n:313"
PUY_DE_DOME_ARCHIVES_ONLINE_URL = "https://www.archivesdepartementales.puy-de-dome.fr/archives-en-ligne"
PUY_DE_DOME_SEARCH_URL = "https://www.archivesdepartementales.puy-de-dome.fr/search"
PUY_DE_DOME_ROBOTS_URL = "https://www.archivesdepartementales.puy-de-dome.fr/robots.txt"
PUY_DE_DOME_SITEMAP_URL = "http://www.archivesdepartementales.puydedome.fr/sitemap/contenus.xml"
PUY_DE_DOME_INEDITS_URL = "https://inedits.eu/en/inedits_content/the-archives-et-cinema-programme/"


@dataclass(frozen=True)
class PuyDeDomeProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


PUY_DE_DOME_PROTOCOL_PROBES = [
    PuyDeDomeProbe(
        probe="official_home",
        probe_label="Site oficial das Archives départementales du Puy-de-Dôme",
        method="GET",
        url=PUY_DE_DOME_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Testa a superfície institucional principal antes de qualquer inferência de acervo.",
    ),
    PuyDeDomeProbe(
        probe="archives_et_cinema_page",
        probe_label="Página oficial Archives et cinéma",
        method="GET",
        url=PUY_DE_DOME_ARCHIVES_ET_CINEMA_URL,
        evidence_signal="audiovisual_archive_programme",
        methodological_note="Verifica se o dispositivo Archives et cinéma expõe catálogo, players ou rota pública de vídeo.",
    ),
    PuyDeDomeProbe(
        probe="archives_online_page",
        probe_label="Página Archives en ligne",
        method="GET",
        url=PUY_DE_DOME_ARCHIVES_ONLINE_URL,
        evidence_signal="online_archives",
        methodological_note="Testa se a entrada geral de arquivos online permite localizar audiovisual coletável.",
    ),
    PuyDeDomeProbe(
        probe="site_search",
        probe_label="Busca pública do site oficial",
        method="GET",
        url=PUY_DE_DOME_SEARCH_URL,
        evidence_signal="site_search",
        methodological_note="Testa busca pública simples sem login, sem contornar barreiras e sem simular usuário humano.",
    ),
    PuyDeDomeProbe(
        probe="robots_txt",
        probe_label="robots.txt do domínio oficial",
        method="GET",
        url=PUY_DE_DOME_ROBOTS_URL,
        evidence_signal="robots_and_sitemap",
        methodological_note="Registra a rota de sitemap declarada publicamente pelo site.",
    ),
    PuyDeDomeProbe(
        probe="declared_sitemap",
        probe_label="Sitemap declarado no robots.txt",
        method="GET",
        url=PUY_DE_DOME_SITEMAP_URL,
        evidence_signal="sitemap",
        methodological_note="Testa o sitemap indicado no robots.txt como possível rota pública de descoberta.",
    ),
    PuyDeDomeProbe(
        probe="inedits_reference",
        probe_label="Referência INEDITS ao programa Archives et cinéma",
        method="GET",
        url=PUY_DE_DOME_INEDITS_URL,
        evidence_signal="directory_reference",
        methodological_note="Confirma a fonte de fila sem tratar a ficha INEDITS como catálogo de vídeos.",
    ),
]


def fetch_puy_de_dome_probe(url, method="GET", sample_bytes=524288):
    response = None
    error = ""
    try:
        response = requests.get(
            url,
            headers={**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"},
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


def _detect_antirobot(text):
    normalized = str(text or "").lower()
    return any(
        marker in normalized
        for marker in (
            "vérification que vous n",
            "verification que vous n",
            "êtes pas un robot",
            "n'êtes pas un robot",
            ".within.website",
            "xess.min.css",
            "noindex,nofollow",
        )
    )


def _page_signals(content):
    raw = str(content or "")
    visible_text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    text = _clean_text(f"{visible_text} {raw}").lower()
    video_files = re.findall(r"https?://[^\"'\s<>]+?\.(?:mp4|m3u8|webm|mov|avi|m4v)", raw, flags=re.I)
    sitemap_refs = re.findall(r"https?://[^\s<>]+sitemap[^\s<>]+", raw, flags=re.I)
    return {
        "anti_robot": _detect_antirobot(raw),
        "official_identity": "archives départementales du puy-de-dôme" in text or "puy-de-dome" in text,
        "archives_et_cinema": "archives et cinéma" in text or "archives et cinema" in text,
        "audiovisual_archive_terms": any(
            term in text
            for term in (
                "archives audiovisuelles",
                "archive audiovisuelle",
                "film",
                "cinéma",
                "cinema",
                "cinéaste amateur",
                "video",
                "vidéo",
            )
        ),
        "collect_describe_conserve_terms": all(term in text for term in ("collect", "décriv", "conserv")),
        "public_catalog_terms": any(term in text for term in ("catalogue", "archives en ligne", "sitemap")),
        "download_terms": "télécharger" in text or "telecharger" in text,
        "video_files": len(video_files),
        "video_embed_terms": any(term in raw.lower() for term in ("<video", "<source", "youtube.com/embed", "player.vimeo.com")),
        "sitemap_refs": len(sitemap_refs),
        "ovh_unavailable": "website unavailable" in text or "ovhcloud" in text,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"anti_robo={'sim' if signals['anti_robot'] else 'nao'}",
            f"identidade={'sim' if signals['official_identity'] else 'nao'}",
            f"archives_et_cinema={'sim' if signals['archives_et_cinema'] else 'nao'}",
            f"audiovisual={'sim' if signals['audiovisual_archive_terms'] else 'nao'}",
            f"coleta_descreve_conserva={'sim' if signals['collect_describe_conserve_terms'] else 'nao'}",
            f"catalogo_publico={'sim' if signals['public_catalog_terms'] else 'nao'}",
            f"download={'sim' if signals['download_terms'] else 'nao'}",
            f"arquivos_video={signals['video_files']}",
            f"embed_video={'sim' if signals['video_embed_terms'] else 'nao'}",
            f"sitemap_refs={signals['sitemap_refs']}",
            f"ovh_indisponivel={'sim' if signals['ovh_unavailable'] else 'nao'}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if signals.get("anti_robot"):
        return "rota_oficial_bloqueada_por_verificacao_antirobo", "retestar_api_sitemap_ou_pagina_publica_sem_contornar_verificacao"
    if signals.get("ovh_unavailable"):
        return "referencia_inedits_indisponivel_na_rodada", "retestar_ficha_inedits_em_ciclo_futuro"
    if access_status != "acessivel":
        return "rota_indisponivel_ou_instavel_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe == "robots_txt" and signals.get("sitemap_refs"):
        return "robots_txt_indica_sitemap_publico", "testar_sitemap_declarado_como_rota_de_descoberta"
    if probe.probe == "declared_sitemap" and signals.get("anti_robot"):
        return "sitemap_declarado_bloqueado_por_verificacao_antirobo", "retestar_sitemap_em_ciclo_futuro"
    if signals.get("video_files") or signals.get("video_embed_terms"):
        return "sinal_de_video_publico_exige_validacao", "validar_se_o_sinal_representa_video_de_acervo"
    if signals.get("archives_et_cinema") and signals.get("audiovisual_archive_terms"):
        return "arquivo_audiovisual_confirmado_sem_rota_publica_coletavel", "manter_fora_do_corpus_ativo_ate_haver_rota_publica_estavel"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_puy_de_dome_probe):
    fetched = fetcher(probe.url, probe.method)
    text = fetched.get("text", "")
    signals = _page_signals(text) if text else {}
    access_status = classify_probe_access_status(
        fetched.get("http_status"),
        detect_js_cookie_requirement(text)
        or detect_js_redirect(text)
        or signals.get("anti_robot", False),
        fetched.get("error", ""),
    )
    conclusion, next_step = _build_protocol_conclusion(probe, access_status, signals)
    return {
        "code": "inedits-county-archives-puy-de-dome",
        "label": "County Archives of Puy-de-Dôme",
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
        "rule_version": PUY_DE_DOME_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_puy_de_dome_protocol_probe(fetcher=fetch_puy_de_dome_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in PUY_DE_DOME_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=PUY_DE_DOME_PROTOCOL_COLUMNS)


def build_puy_de_dome_non_incorporated_register(protocol_df):
    return pd.DataFrame(
        [
            {
                "unit_code": "inedits-county-archives-puy-de-dome",
                "unit_label": "County Archives of Puy-de-Dôme",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Puy-de-Dôme / França",
                "access_category": PUY_DE_DOME_ACCESS_CATEGORY,
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A unidade foi identificada como programa/arquivo audiovisual ligado às Archives départementales "
                    "du Puy-de-Dôme, mas a home, a página `Archives et cinéma`, a busca e a página de arquivos online "
                    "retornaram verificação anti-robô. O sitemap declarado pelo robots.txt também redirecionou para "
                    "a mesma barreira, e a referência INEDITS estava indisponível na rodada."
                ),
                "collection_route_attempted": (
                    "Home oficial, página `Archives et cinéma`, página `Archives en ligne`, busca pública, robots.txt, "
                    "sitemap declarado e referência INEDITS ao programa `Archives et cinéma`."
                ),
                "attempt_summary": (
                    "As rotas oficiais responderam com página de verificação anti-robô em vez de HTML de catálogo, API, "
                    "sitemap utilizável, player ou arquivos de vídeo. O protocolo não tentou burlar a barreira técnica."
                ),
                "methodological_explanation": (
                    "A decisão não nega a existência do acervo audiovisual; registra que, nesta rodada, não houve rota "
                    "pública estável, reprodutível e coletável sem verificação anti-robô. Por rigor científico, a unidade "
                    "permanece documentada fora do corpus ativo até que exista API, sitemap acessível, catálogo público "
                    "ou página de vídeos verificável."
                ),
                "evidence_status": "arquivo_audiovisual_identificado_com_rota_publica_bloqueada",
                "protocol_status": "protocolo_de_nao_incorporacao_por_barreira_tecnica_de_acesso",
                "next_step": "retestar pagina Archives et cinéma, sitemap e eventual API pública em ciclos futuros",
                "blocks_expansion": False,
                "rule_version": PUY_DE_DOME_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_puy_de_dome_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_puy_de_dome_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_puy_de_dome_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / PUY_DE_DOME_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_puy_de_dome_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "PUY_DE_DOME_ACCESS_CATEGORY",
    "PUY_DE_DOME_PROTOCOL_COLUMNS",
    "PUY_DE_DOME_PROTOCOL_FILENAME",
    "PUY_DE_DOME_PROTOCOL_PROBES",
    "PUY_DE_DOME_PROTOCOL_RULE_VERSION",
    "build_puy_de_dome_non_incorporated_register",
    "build_puy_de_dome_protocol_probe",
    "write_puy_de_dome_protocol_probe",
]
