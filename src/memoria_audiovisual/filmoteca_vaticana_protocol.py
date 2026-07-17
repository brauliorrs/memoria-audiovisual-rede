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


FILMOTECA_VATICANA_PROTOCOL_FILENAME = "observatorio_protocolo_filmoteca_vaticana.csv"
FILMOTECA_VATICANA_PROTOCOL_RULE_VERSION = "2026-07-filmoteca-vaticana-protocol-v1"
FILMOTECA_VATICANA_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
FILMOTECA_VATICANA_ACCESS_CATEGORY = "arquivo_filmico_confirmado_sem_catalogo_publico_de_video"

FILMOTECA_VATICANA_OFFICIAL_EN_URL = "https://www.comunicazione.va/en/filmoteca-vaticana.html"
FILMOTECA_VATICANA_OFFICIAL_IT_URL = "https://www.comunicazione.va/it/filmoteca-vaticana.html"
FILMOTECA_VATICANA_VIDEO_GALLERY_URL = "https://www.comunicazione.va/it/multimedia/video-gallery.html"
FILMOTECA_VATICANA_VATICAN_NEWS_WEBDOC_URL = (
    "https://www.vaticannews.va/it/vaticano/news/2019-11/"
    "filmoteca-vaticana-anniversario-60-webdoc-giovanni-xxiii-papi0.html"
)
FILMOTECA_VATICANA_YOUTUBE_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLEych8J5GOKjSfPuIA20tw30M4nfXN4Pz"
FILMOTECA_VATICANA_SEARCH_URL = "https://www.comunicazione.va/en/search.html?q=Filmoteca%20Vaticana"


@dataclass(frozen=True)
class FilmotecaVaticanaProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str


FILMOTECA_VATICANA_PROTOCOL_PROBES = [
    FilmotecaVaticanaProbe(
        probe="official_dicastery_page_en",
        probe_label="Página oficial em inglês da Vatican Film Library",
        method="GET",
        url=FILMOTECA_VATICANA_OFFICIAL_EN_URL,
        evidence_signal="official_archive_page",
        methodological_note="Confirma a existência institucional e o tamanho do acervo, sem presumir catálogo público.",
    ),
    FilmotecaVaticanaProbe(
        probe="official_dicastery_page_it",
        probe_label="Página oficial em italiano da Filmoteca Vaticana",
        method="GET",
        url=FILMOTECA_VATICANA_OFFICIAL_IT_URL,
        evidence_signal="official_archive_page",
        methodological_note="Confirma a descrição oficial italiana e testa termos de catálogo/consulta pública.",
    ),
    FilmotecaVaticanaProbe(
        probe="dicastery_video_gallery",
        probe_label="Galeria oficial de vídeos do Dicastero per la Comunicazione",
        method="GET",
        url=FILMOTECA_VATICANA_VIDEO_GALLERY_URL,
        evidence_signal="institutional_video_gallery",
        methodological_note="Distingue vídeos institucionais sobre a Filmoteca de um corpus de acervo filmográfico.",
    ),
    FilmotecaVaticanaProbe(
        probe="vatican_news_webdoc",
        probe_label="Webdoc Vatican News sobre as origens da Filmoteca Vaticana",
        method="GET",
        url=FILMOTECA_VATICANA_VATICAN_NEWS_WEBDOC_URL,
        evidence_signal="editorial_webdoc_about_archive",
        methodological_note="Evita tratar reportagem/webdoc editorial como catálogo ou coleção do acervo.",
    ),
    FilmotecaVaticanaProbe(
        probe="youtube_playlist",
        probe_label="Playlist Filmoteca Vaticana no YouTube",
        method="GET",
        url=FILMOTECA_VATICANA_YOUTUBE_PLAYLIST_URL,
        evidence_signal="youtube_playlist_about_archive",
        methodological_note="Verifica se a playlist é conteúdo sobre a instituição, não acervo filmográfico enumerável.",
    ),
    FilmotecaVaticanaProbe(
        probe="official_site_search",
        probe_label="Busca oficial do Dicastero por Filmoteca Vaticana",
        method="GET",
        url=FILMOTECA_VATICANA_SEARCH_URL,
        evidence_signal="official_site_search",
        methodological_note="Testa se a busca oficial revela catálogo público, API, download ou coleção de vídeos de acervo.",
    ),
]


def fetch_filmoteca_vaticana_probe(probe, sample_bytes=786432):
    response = None
    error = ""
    text = ""
    try:
        response = requests.get(
            probe.url,
            headers={
                **HEADERS,
                "Accept": "text/html,application/xhtml+xml,*/*",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.8,pt-BR;q=0.7",
                "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)",
            },
            timeout=(8, 18),
            allow_redirects=True,
            stream=True,
        )
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=65536, decode_unicode=True):
            if not chunk:
                continue
            if not isinstance(chunk, str):
                chunk = chunk.decode("utf-8", errors="ignore")
            chunks.append(chunk)
            total += len(chunk)
            if total >= sample_bytes:
                break
        text = "".join(chunks)
    except Exception as exc:
        error = str(exc)
    finally:
        if response is not None:
            response.close()

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


def _page_signals(content):
    raw = str(content or "")
    visible_text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    text = _clean_text(f"{visible_text} {raw}").lower()
    youtube_embeds = len(re.findall(r"youtube(?:-nocookie)?\.com/embed/", raw, flags=re.I))
    filmoteca_video_mentions = len(re.findall(r"filmoteca vaticana", text, flags=re.I))
    youtube_playlist_terms = "playlist" in text and "youtube" in text
    catalogue_public_terms = any(
        term in text
        for term in (
            "catalogo online",
            "catalogue online",
            "online catalogue",
            "search the catalogue",
            "consulta il catalogo",
            " api ",
            "/api/",
            "endpoint",
            "download catalogue",
            "download catalog",
            "oai-pmh",
        )
    )
    return {
        "official_identity": "filmoteca vaticana" in text or "vatican film library" in text,
        "dicastery_identity": "dicastero per la comunicazione" in text or "dicastery for communication" in text,
        "archive_terms": any(term in text for term in ("archive", "archivio", "patrimony", "patrimonio", "conserva", "custodisce")),
        "archive_count_8000": bool(re.search(r"\b8[ .,\u00a0]?000\b", text) and ("titoli" in text or "titles" in text)),
        "history_terms": any(term in text for term in ("history", "storia", "papa leone xiii", "pope leo xiii", "giovanni xxiii")),
        "catalogue_public_terms": catalogue_public_terms and not youtube_playlist_terms,
        "contact_terms": "filmoteca.vaticana" in text or "contact" in text or "contatti" in text,
        "video_gallery_terms": "video gallery" in text or "galleria video" in text,
        "webdoc_terms": "web doc" in text or "webdoc" in text or "le origini della filmoteca" in text,
        "youtube_playlist_terms": youtube_playlist_terms,
        "youtube_embeds": youtube_embeds,
        "filmoteca_video_mentions": filmoteca_video_mentions,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"identidade={'sim' if signals['official_identity'] else 'nao'}",
            f"dicasterio={'sim' if signals['dicastery_identity'] else 'nao'}",
            f"arquivo={'sim' if signals['archive_terms'] else 'nao'}",
            f"acervo_8000_titulos={'sim' if signals['archive_count_8000'] else 'nao'}",
            f"historia={'sim' if signals['history_terms'] else 'nao'}",
            f"catalogo_publico={'sim' if signals['catalogue_public_terms'] else 'nao'}",
            f"contato={'sim' if signals['contact_terms'] else 'nao'}",
            f"galeria_video={'sim' if signals['video_gallery_terms'] else 'nao'}",
            f"webdoc={'sim' if signals['webdoc_terms'] else 'nao'}",
            f"playlist_youtube={'sim' if signals['youtube_playlist_terms'] else 'nao'}",
            f"youtube_embeds={signals['youtube_embeds']}",
            f"mencoes_filmoteca={signals['filmoteca_video_mentions']}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        return "rota_indisponivel_ou_instavel_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe.startswith("official_dicastery_page") and signals.get("archive_count_8000"):
        if not signals.get("catalogue_public_terms"):
            return "acervo_filmico_confirmado_sem_catalogo_publico_de_video", "registrar_unidade_nao_incorporada_por_ausencia_de_rota_coletavel"
        return "pagina_oficial_com_sinal_de_catalogo_a_validar", "validar_catalogo_antes_de_incorporar"
    if probe.probe == "dicastery_video_gallery":
        return "videos_institucionais_sobre_a_filmoteca_nao_equivalem_ao_acervo", "manter_videos_editoriais_fora_do_corpus_do_arquivo"
    if probe.probe == "vatican_news_webdoc":
        return "webdoc_editorial_sobre_a_filmoteca_nao_equivale_a_corpus", "usar_como_evidencia_contextual_sem_incorporar"
    if probe.probe == "youtube_playlist":
        return "playlist_sobre_a_filmoteca_nao_equivale_a_catalogo_do_acervo", "nao_incorporar_playlist_institucional_como_acervo"
    if probe.probe == "official_site_search":
        if signals.get("catalogue_public_terms"):
            return "busca_oficial_indica_rota_catalografica_a_validar", "investigar_rota_especifica_em_ciclo_futuro"
        return "busca_oficial_sem_catalogo_publico_de_video", "manter_em_monitoramento"
    if signals.get("archive_terms"):
        return "arquivo_confirmado_sem_rota_publica_de_video", "manter_fora_do_corpus_ativo_ate_haver_rota_coletavel"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_filmoteca_vaticana_probe):
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
        "code": "fiaf-filmoteca-vaticana",
        "label": "Filmoteca Vaticana",
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
        "rule_version": FILMOTECA_VATICANA_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_filmoteca_vaticana_protocol_probe(fetcher=fetch_filmoteca_vaticana_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in FILMOTECA_VATICANA_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=FILMOTECA_VATICANA_PROTOCOL_COLUMNS)


def build_filmoteca_vaticana_non_incorporated_register(protocol_df):
    return pd.DataFrame(
        [
            {
                "unit_code": "fiaf-filmoteca-vaticana",
                "unit_label": "Filmoteca Vaticana",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Vaticano",
                "access_category": FILMOTECA_VATICANA_ACCESS_CATEGORY,
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "A página oficial do Dicastero per la Comunicazione confirma a Filmoteca Vaticana e um acervo "
                    "de cerca de 8.000 títulos, mas não expõe catálogo público, API, dump, OAI-PMH ou coleção de "
                    "vídeos de acervo coletável. As rotas públicas com vídeo encontradas são webdocs, galeria "
                    "institucional e playlist sobre a Filmoteca, não registros do acervo filmográfico."
                ),
                "collection_route_attempted": (
                    "Página oficial em inglês e italiano da Filmoteca Vaticana no Dicastero per la Comunicazione; "
                    "galeria oficial de vídeos do Dicastero; webdoc Vatican News; playlist YouTube Filmoteca "
                    "Vaticana; busca oficial do site do Dicastero por Filmoteca Vaticana."
                ),
                "attempt_summary": (
                    "As páginas oficiais confirmam instituição, preservação, contato e cerca de 8.000 títulos. "
                    "A galeria e a playlist materializam vídeos editoriais sobre a Filmoteca, incluindo webdocs, "
                    "mas não fornecem enumeração pública do acervo nem fichas de filmes com player de acervo."
                ),
                "methodological_explanation": (
                    "A decisão não nega a existência nem a relevância do acervo. Ela evita confundir vídeos "
                    "institucionais sobre a Filmoteca com corpus audiovisual do arquivo. Para entrar como corpus "
                    "ativo, a unidade precisa expor uma rota pública reprodutível de metadados audiovisuais ou "
                    "vídeos de acervo."
                ),
                "evidence_status": "arquivo_filmico_confirmado_sem_catalogo_publico_de_video_coletavel",
                "protocol_status": "acervo_preservado_com_videos_editoriais_sem_rota_publica_de_acervo",
                "next_step": "retestar páginas oficiais, busca do Dicastero e eventuais catálogos digitais em ciclos futuros",
                "blocks_expansion": False,
                "rule_version": FILMOTECA_VATICANA_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_filmoteca_vaticana_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_filmoteca_vaticana_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_filmoteca_vaticana_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / FILMOTECA_VATICANA_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_filmoteca_vaticana_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "FILMOTECA_VATICANA_ACCESS_CATEGORY",
    "FILMOTECA_VATICANA_PROTOCOL_COLUMNS",
    "FILMOTECA_VATICANA_PROTOCOL_FILENAME",
    "FILMOTECA_VATICANA_PROTOCOL_PROBES",
    "FILMOTECA_VATICANA_PROTOCOL_RULE_VERSION",
    "build_filmoteca_vaticana_non_incorporated_register",
    "build_filmoteca_vaticana_protocol_probe",
    "write_filmoteca_vaticana_protocol_probe",
]
