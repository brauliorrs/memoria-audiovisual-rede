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


CINEMATHEQUE_CORSE_PROTOCOL_FILENAME = "observatorio_protocolo_cinematheque_corse.csv"
CINEMATHEQUE_CORSE_PROTOCOL_RULE_VERSION = "2026-06-cinematheque-corse-protocol-v1"
CINEMATHEQUE_CORSE_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
CINEMATHEQUE_CORSE_ACCESS_CATEGORY = (
    "arquivo_audiovisual_com_consulta_presencial_ou_por_acreditacao_sem_catalogo_publico_de_video"
)

CINEMATHEQUE_CORSE_OLD_QUEUE_URL = "https://casadilume.corse.fr/"
CINEMATHEQUE_CORSE_HOME_URL = "https://www.casadilume.corsica/"
CINEMATHEQUE_CORSE_COLLECTIONS_URL = "https://www.casadilume.corsica/Consulter-les-Collections_a510.html"
CINEMATHEQUE_CORSE_HERITAGE_URL = "https://www.casadilume.corsica/Le-Patrimoine_a42.html"
CINEMATHEQUE_CORSE_CINERESSOURCES_URL = "https://www.casadilume.corsica/Cine-Ressources_a507.html"
CINEMATHEQUE_CORSE_SEARCH_URL = "https://www.casadilume.corsica/search/?avance=1"
CINEMATHEQUE_CORSE_MEDIA_URL = "https://www.casadilume.corsica/MEDIAS_r9.html"
CINEMATHEQUE_CORSE_YOUTUBE_URL = "https://www.youtube.com/channel/UCP5nYsqzEj-XAkAH5jA0bzQ"


@dataclass(frozen=True)
class CinemathequeCorseProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


CINEMATHEQUE_CORSE_PROTOCOL_PROBES = [
    CinemathequeCorseProbe(
        probe="old_queue_domain",
        probe_label="Domínio antigo informado na fila INEDITS",
        method="GET",
        url=CINEMATHEQUE_CORSE_OLD_QUEUE_URL,
        evidence_signal="old_domain",
        methodological_note="Testa a URL histórica `casadilume.corse.fr` registrada na fila europeia.",
    ),
    CinemathequeCorseProbe(
        probe="official_home",
        probe_label="Site oficial atual Casa di Lume",
        method="GET",
        url=CINEMATHEQUE_CORSE_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Confirma a presença institucional sem tratar a home como catálogo audiovisual.",
    ),
    CinemathequeCorseProbe(
        probe="collections_page",
        probe_label="Página oficial Consulter les Collections",
        method="GET",
        url=CINEMATHEQUE_CORSE_COLLECTIONS_URL,
        evidence_signal="collection_access_policy",
        methodological_note="Verifica a política pública de consulta das coleções e a existência de rota online.",
    ),
    CinemathequeCorseProbe(
        probe="heritage_page",
        probe_label="Página Le Patrimoine",
        method="GET",
        url=CINEMATHEQUE_CORSE_HERITAGE_URL,
        evidence_signal="heritage_archive_reference",
        methodological_note="Confirma o enquadramento patrimonial e arquivístico da instituição.",
    ),
    CinemathequeCorseProbe(
        probe="cineressources_page",
        probe_label="Página Ciné-Ressources",
        method="GET",
        url=CINEMATHEQUE_CORSE_CINERESSOURCES_URL,
        evidence_signal="non_film_catalog_reference",
        methodological_note="Verifica se o catálogo online indicado cobre filmes ou apenas coleções Non Film.",
    ),
    CinemathequeCorseProbe(
        probe="site_search",
        probe_label="Busca avançada do site institucional",
        method="GET",
        url=CINEMATHEQUE_CORSE_SEARCH_URL,
        evidence_signal="site_search",
        methodological_note="Testa se a busca pública do site funciona como catálogo de acervo audiovisual.",
    ),
    CinemathequeCorseProbe(
        probe="media_section",
        probe_label="Seção MEDIAS do site institucional",
        method="GET",
        url=CINEMATHEQUE_CORSE_MEDIA_URL,
        evidence_signal="institutional_media_section",
        methodological_note="Distingue comunicação institucional de catálogo de vídeos de acervo.",
    ),
    CinemathequeCorseProbe(
        probe="youtube_channel",
        probe_label="Canal YouTube divulgado no rodapé",
        method="GET",
        url=CINEMATHEQUE_CORSE_YOUTUBE_URL,
        evidence_signal="external_video_platform",
        methodological_note="Verifica se plataforma externa substitui ou não uma rota arquivística de corpus.",
    ),
]


def fetch_cinematheque_corse_probe(url, method="GET", sample_bytes=524288):
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


def _page_signals(content):
    raw = str(content or "")
    visible_text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    text = _clean_text(f"{visible_text} {raw}").lower()
    video_files = re.findall(r"https?://[^\"'\s<>]+?\.(?:mp4|m3u8|webm|mov|avi|m4v)", raw, flags=re.I)
    return {
        "official_identity": "cinémathèque de corse" in text or "casa di lume" in text,
        "archive_terms": any(
            term in text
            for term in (
                "patrimoine",
                "archives",
                "collections",
                "conservation",
                "restauration",
                "cinémathèque",
            )
        ),
        "audiovisual_or_film_terms": any(term in text for term in ("film", "audiovisuel", "vidéo", "cinéma")),
        "non_film_online_catalog": "collections non film" in text or "non film" in text,
        "cineressources_reference": "cineressources" in text or "ciné-ressources" in text,
        "appointment_access": "rendez-vous" in text or "demande de recherche" in text,
        "registration_or_accreditation": "accréditation" in text or "inscription" in text,
        "ina_cnc_consultation": "dépôt légal" in text and "ina" in text and "cnc" in text,
        "site_search_only": "recherche avancée" in text and "consulter les collections" not in text,
        "institutional_media_terms": "medias" in text or "actualités" in text or "prochainement" in text,
        "youtube_terms": "youtube" in text or "consent.youtube" in text,
        "video_files": len(video_files),
        "video_embed_terms": any(term in raw.lower() for term in ("<video", "youtube.com/embed", "player.vimeo.com")),
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"identidade={'sim' if signals['official_identity'] else 'nao'}",
            f"arquivo={'sim' if signals['archive_terms'] else 'nao'}",
            f"filmico={'sim' if signals['audiovisual_or_film_terms'] else 'nao'}",
            f"catalogo_non_film={'sim' if signals['non_film_online_catalog'] else 'nao'}",
            f"cineressources={'sim' if signals['cineressources_reference'] else 'nao'}",
            f"rendez_vous={'sim' if signals['appointment_access'] else 'nao'}",
            f"acreditacao={'sim' if signals['registration_or_accreditation'] else 'nao'}",
            f"ina_cnc={'sim' if signals['ina_cnc_consultation'] else 'nao'}",
            f"busca_site={'sim' if signals['site_search_only'] else 'nao'}",
            f"midias_institucionais={'sim' if signals['institutional_media_terms'] else 'nao'}",
            f"youtube={'sim' if signals['youtube_terms'] else 'nao'}",
            f"arquivos_video={signals['video_files']}",
            f"embed_video={'sim' if signals['video_embed_terms'] else 'nao'}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        if probe.probe == "old_queue_domain":
            return "dominio_antigo_da_fila_indisponivel", "usar_dominio_oficial_atual_e_protocolar_redirecionamento_metodologico"
        return "rota_indisponivel_ou_instavel_na_rodada", "retestar_sem_promover_a_corpus"
    if signals.get("video_files"):
        return "sinal_de_arquivo_video_publico_exige_validacao", "validar_se_o_sinal_representa_video_de_acervo"
    if probe.probe == "collections_page" and (
        signals.get("non_film_online_catalog")
        or signals.get("appointment_access")
        or signals.get("registration_or_accreditation")
    ):
        return "colecoes_audiovisuais_sem_catalogo_publico_de_video", "registrar_unidade_nao_incorporada_por_acesso_presencial_ou_acreditado"
    if probe.probe == "cineressources_page" and signals.get("non_film_online_catalog"):
        return "catalogo_online_restrito_a_non_film", "nao_incorporar_como_corpus_audiovisual_de_imagem_em_movimento"
    if probe.probe == "cineressources_page" and signals.get("cineressources_reference"):
        return "rota_cineressources_indicada_sem_catalogo_publico_de_video", "usar_a_pagina_de_colecoes_como_evidencia_da_restricao_non_film"
    if probe.probe == "site_search":
        return "busca_do_site_nao_equivale_a_catalogo_arquivistico", "nao_usar_busca_institucional_como_corpus"
    if probe.probe in {"media_section", "youtube_channel"}:
        return "midia_institucional_nao_equivale_a_corpus_arquivistico", "manter_como_indicio_de_comunicacao_publica"
    if signals.get("archive_terms") and signals.get("audiovisual_or_film_terms"):
        return "arquivo_audiovisual_confirmado_sem_rota_publica_de_video", "manter_fora_do_corpus_ativo_ate_haver_rota_coletavel"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_cinematheque_corse_probe):
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
        "code": "inedits-cinematheque-corse",
        "label": "Cinémathèque de Corse",
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
        "rule_version": CINEMATHEQUE_CORSE_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_cinematheque_corse_protocol_probe(fetcher=fetch_cinematheque_corse_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [
        _build_protocol_row(probe, evaluated_at, fetcher=fetcher)
        for probe in CINEMATHEQUE_CORSE_PROTOCOL_PROBES
    ]
    return pd.DataFrame(rows, columns=CINEMATHEQUE_CORSE_PROTOCOL_COLUMNS)


def build_cinematheque_corse_non_incorporated_register(protocol_df):
    return pd.DataFrame(
        [
            {
                "unit_code": "inedits-cinematheque-corse",
                "unit_label": "Cinémathèque de Corse",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Córsega / França",
                "access_category": CINEMATHEQUE_CORSE_ACCESS_CATEGORY,
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A Cinémathèque de Corse é uma instituição audiovisual/fílmica confirmada, mas a rota oficial "
                    "não expõe catálogo público de vídeos ou player de acervo. A página de coleções informa consulta "
                    "por rendez-vous e o catálogo online indicado cobre coleções Non Film, como cartazes e fotografias."
                ),
                "collection_route_attempted": (
                    "Domínio antigo da fila INEDITS, site oficial atual Casa di Lume, página Consulter les Collections, "
                    "página Le Patrimoine, página Ciné-Ressources, busca avançada do site, seção MEDIAS e canal YouTube."
                ),
                "attempt_summary": (
                    "O domínio antigo `casadilume.corse.fr` não resolveu na rodada; o domínio oficial atual "
                    "`casadilume.corsica` respondeu. A política pública encontrada aponta consulta presencial, "
                    "inscrição/acreditação e catálogo online Non Film, sem rota aberta de vídeos."
                ),
                "methodological_explanation": (
                    "A decisão não nega a existência do acervo audiovisual; nega apenas a entrada como corpus ativo "
                    "do MVP, porque o organismo só incorpora unidades quando consegue materializar registros públicos "
                    "de imagem em movimento de forma reprodutível, sem login, sem credenciamento e sem substituir "
                    "catálogo arquivístico por comunicação institucional."
                ),
                "evidence_status": "arquivo_audiovisual_confirmado_sem_catalogo_publico_de_video_coletavel",
                "protocol_status": "consulta_presencial_ou_acreditada_e_catalogo_online_non_film",
                "next_step": "retestar site oficial, Ciné-Ressources e eventuais novas rotas públicas de vídeo em ciclos futuros",
                "blocks_expansion": False,
                "rule_version": CINEMATHEQUE_CORSE_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_cinematheque_corse_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_cinematheque_corse_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_cinematheque_corse_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / CINEMATHEQUE_CORSE_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_cinematheque_corse_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "CINEMATHEQUE_CORSE_ACCESS_CATEGORY",
    "CINEMATHEQUE_CORSE_PROTOCOL_COLUMNS",
    "CINEMATHEQUE_CORSE_PROTOCOL_FILENAME",
    "CINEMATHEQUE_CORSE_PROTOCOL_PROBES",
    "CINEMATHEQUE_CORSE_PROTOCOL_RULE_VERSION",
    "build_cinematheque_corse_non_incorporated_register",
    "build_cinematheque_corse_protocol_probe",
    "write_cinematheque_corse_protocol_probe",
]
