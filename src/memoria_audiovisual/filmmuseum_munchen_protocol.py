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


FILMMUSEUM_MUNCHEN_PROTOCOL_FILENAME = "observatorio_protocolo_filmmuseum_munchen.csv"
FILMMUSEUM_MUNCHEN_PROTOCOL_RULE_VERSION = "2026-07-filmmuseum-munchen-protocol-v1"
FILMMUSEUM_MUNCHEN_PROTOCOL_COLUMNS = FRANCEARCHIVES_PROTOCOL_COLUMNS
FILMMUSEUM_MUNCHEN_ACCESS_CATEGORY = (
    "arquivo_filmico_com_acervo_confirmado_sem_catalogo_publico_de_video"
)

FILMMUSEUM_MUNCHEN_HOME_URL = "https://www.muenchner-stadtmuseum.de/film"
FILMMUSEUM_MUNCHEN_HISTORY_URL = "https://www.muenchner-stadtmuseum.de/sammlungen/filmmuseum/geschichte"
FILMMUSEUM_MUNCHEN_PROGRAMME_URL = (
    "https://www.muenchner-stadtmuseum.de/sammlungen/filmmuseum/aktueller-spielplan"
)
FILMMUSEUM_MUNCHEN_FILM_SERIES_URL = "https://www.muenchner-stadtmuseum.de/sammlungen/filmmuseum/filmreihen"
FILMMUSEUM_MUNCHEN_MUSEUM_VIDEOS_URL = "https://www.muenchner-stadtmuseum.de/muenchner-stadtmuseum/videos"
MUNICH_COLLECTION_ONLINE_URL = "https://sammlungonline.muenchner-stadtmuseum.de/"
MUNICH_COLLECTION_SEARCH_URL = (
    "https://sammlungonline.muenchner-stadtmuseum.de/liste"
    "?tx_so_displayso%5Baction%5D=list&tx_so_displayso%5Bcontroller%5D=Objekt"
    "&cHash=70fafbb825a565d9bbceddf71fb64187"
)


@dataclass(frozen=True)
class FilmmuseumMunchenProbe:
    probe: str
    probe_label: str
    method: str
    url: str
    evidence_signal: str
    methodological_note: str
    payload: dict[str, str] | None = None


FILMMUSEUM_MUNCHEN_PROTOCOL_PROBES = [
    FilmmuseumMunchenProbe(
        probe="official_film_page",
        probe_label="Página oficial do Filmmuseum München",
        method="GET",
        url=FILMMUSEUM_MUNCHEN_HOME_URL,
        evidence_signal="official_site",
        methodological_note="Confirma a presença institucional sem tratar programação de cinema como corpus digital.",
    ),
    FilmmuseumMunchenProbe(
        probe="history_page",
        probe_label="Página Geschichte do Filmmuseum",
        method="GET",
        url=FILMMUSEUM_MUNCHEN_HISTORY_URL,
        evidence_signal="archive_collection_history",
        methodological_note="Verifica se a página histórica confirma acervo fílmico e rota pública de catálogo.",
    ),
    FilmmuseumMunchenProbe(
        probe="current_programme",
        probe_label="Spielplan & Tickets",
        method="GET",
        url=FILMMUSEUM_MUNCHEN_PROGRAMME_URL,
        evidence_signal="screening_programme",
        methodological_note="Distingue sessões de cinema, ingressos e programação de corpus audiovisual de acervo.",
    ),
    FilmmuseumMunchenProbe(
        probe="film_series",
        probe_label="Filmreihen",
        method="GET",
        url=FILMMUSEUM_MUNCHEN_FILM_SERIES_URL,
        evidence_signal="screening_series",
        methodological_note="Verifica se séries de filmes oferecem registros de acervo ou apenas programação curatorial.",
    ),
    FilmmuseumMunchenProbe(
        probe="museum_videos_page",
        probe_label="Página geral de vídeos do Münchner Stadtmuseum",
        method="GET",
        url=FILMMUSEUM_MUNCHEN_MUSEUM_VIDEOS_URL,
        evidence_signal="general_museum_youtube_videos",
        methodological_note="Evita confundir vídeos institucionais do museu inteiro com corpus do Filmmuseum.",
    ),
    FilmmuseumMunchenProbe(
        probe="collection_online_home",
        probe_label="Sammlung Online do Münchner Stadtmuseum",
        method="GET",
        url=MUNICH_COLLECTION_ONLINE_URL,
        evidence_signal="collection_online",
        methodological_note="Sondagem leve da coleção online; não varre objetos em massa nem força recorte inexistente.",
    ),
    FilmmuseumMunchenProbe(
        probe="collection_online_film_search",
        probe_label="Busca Film na Sammlung Online",
        method="POST",
        url=MUNICH_COLLECTION_SEARCH_URL,
        evidence_signal="collection_search",
        methodological_note="Testa o formulário público com termo Film; erro ou timeout impede promoção a corpus.",
        payload={"tx_so_displayso[newSuchanfrage][sword]": "Film"},
    ),
]


def fetch_filmmuseum_munchen_probe(probe, sample_bytes=524288):
    response = None
    error = ""
    try:
        request_kwargs = {
            "headers": {
                **HEADERS,
                "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8,pt-BR;q=0.7",
            },
            "timeout": (8, 14),
            "allow_redirects": True,
        }
        if probe.method == "POST":
            response = requests.post(probe.url, data=probe.payload or {}, **request_kwargs)
        else:
            response = requests.get(probe.url, **request_kwargs)
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


def _page_signals(content):
    raw = str(content or "")
    visible_text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    text = _clean_text(f"{visible_text} {raw}").lower()
    youtube_embeds = len(re.findall(r"youtube(?:-nocookie)?\.com/embed/", raw, flags=re.I))
    object_links = len(re.findall(r"tx_so_displayso%5Bobjekt%5D=|tx_so_displayso\[objekt\]=", raw, flags=re.I))
    return {
        "official_identity": "filmmuseum münchen" in text or "münchner stadtmuseum" in text,
        "archive_terms": any(term in text for term in ("archiv", "filmarchiv", "kopien", "klassiker der filmgeschichte")),
        "archive_count_6000": bool(re.search(r"\b6[ .]?000\b", text) and "kopien" in text),
        "programme_terms": any(term in text for term in ("spielplan", "tickets", "vorstellungen", "retrospektiven", "filmreihen")),
        "screening_terms": any(term in text for term in ("musikbegleitung", "eintritt", "kinokasse", "tickets")),
        "collection_online_terms": "sammlung online" in text or "tx_so_displayso" in raw,
        "collection_filmmuseum_terms": "filmmuseum" in text and "sammlung online" in text,
        "archive_catalog_terms": any(
            term in text
            for term in ("online-katalog", "online katalog", "catalogue", "katalog des filmarchivs", "filmarchiv katalog")
        ),
        "youtube_embeds": youtube_embeds,
        "object_links": object_links,
    }


def _observed_value(signals, access_status):
    if not signals:
        return access_status
    return "; ".join(
        [
            f"identidade={'sim' if signals['official_identity'] else 'nao'}",
            f"arquivo={'sim' if signals['archive_terms'] else 'nao'}",
            f"acervo_6000_copias={'sim' if signals['archive_count_6000'] else 'nao'}",
            f"programacao={'sim' if signals['programme_terms'] else 'nao'}",
            f"sessoes_ingressos={'sim' if signals['screening_terms'] else 'nao'}",
            f"sammlung_online={'sim' if signals['collection_online_terms'] else 'nao'}",
            f"recorte_filmmuseum_na_sammlung={'sim' if signals['collection_filmmuseum_terms'] else 'nao'}",
            f"catalogo_filmarchiv={'sim' if signals['archive_catalog_terms'] else 'nao'}",
            f"youtube_embeds={signals['youtube_embeds']}",
            f"object_links={signals['object_links']}",
        ]
    )


def _build_protocol_conclusion(probe, access_status, signals):
    if access_status != "acessivel":
        if probe.probe == "collection_online_film_search":
            return "busca_sammlung_online_instavel_nao_promove_corpus", "nao_incorporar_sem_rota_estavel_de_busca_ou_catalogo"
        return "rota_indisponivel_ou_instavel_na_rodada", "retestar_sem_promover_a_corpus"
    if probe.probe == "history_page" and signals.get("archive_count_6000"):
        return "acervo_filmico_confirmado_sem_catalogo_publico_de_video", "registrar_unidade_nao_incorporada_por_ausencia_de_rota_coletavel"
    if probe.probe in {"current_programme", "film_series"}:
        return "programacao_de_sala_nao_equivale_a_corpus_audiovisual", "nao_incorporar_sessoes_e_ingressos_como_acervo"
    if probe.probe == "museum_videos_page" and signals.get("youtube_embeds"):
        return "videos_institucionais_do_museu_nao_equivalem_ao_acervo_do_filmmuseum", "manter_videos_gerais_fora_do_corpus_do_filmmuseum"
    if probe.probe == "collection_online_home":
        if signals.get("collection_filmmuseum_terms") or signals.get("archive_catalog_terms"):
            return "sammlung_online_requer_recorte_especifico_a_validar", "validar_rota_especifica_antes_de_incorporar"
        return "sammlung_online_sem_recorte_filmmuseum_detectado", "nao_raspar_colecao_geral_sem_recorte_audiovisual"
    if probe.probe == "official_film_page":
        return "site_oficial_contextual_sem_catalogo_publico_de_video", "manter_como_evidencia_institucional"
    if signals.get("archive_terms"):
        return "arquivo_filmico_confirmado_sem_rota_publica_de_video", "manter_fora_do_corpus_ativo_ate_haver_rota_coletavel"
    return "rota_acessivel_sem_evidencia_coletavel_suficiente", "manter_em_monitoramento"


def _build_protocol_row(probe, evaluated_at, fetcher=fetch_filmmuseum_munchen_probe):
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
        "code": "fiaf-filmmuseum-munchen",
        "label": "Filmmuseum München",
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
        "rule_version": FILMMUSEUM_MUNCHEN_PROTOCOL_RULE_VERSION,
        "error": fetched.get("error", ""),
    }


def build_filmmuseum_munchen_protocol_probe(fetcher=fetch_filmmuseum_munchen_probe, evaluated_at=None):
    evaluated_at = evaluated_at or utcnow_iso()
    rows = [_build_protocol_row(probe, evaluated_at, fetcher=fetcher) for probe in FILMMUSEUM_MUNCHEN_PROTOCOL_PROBES]
    return pd.DataFrame(rows, columns=FILMMUSEUM_MUNCHEN_PROTOCOL_COLUMNS)


def build_filmmuseum_munchen_non_incorporated_register(protocol_df):
    return pd.DataFrame(
        [
            {
                "unit_code": "fiaf-filmmuseum-munchen",
                "unit_label": "Filmmuseum München",
                "unit_type": "arquivo_audiovisual_individual",
                "territorial_scope": "Munique / Alemanha",
                "access_category": FILMMUSEUM_MUNCHEN_ACCESS_CATEGORY,
                "public_status": "Arquivo identificado, mas não incluído no corpus do organismo",
                "methodological_decision": "não incorporar ao corpus ativo nesta rodada",
                "negative_reason": (
                    "O Filmmuseum München é um arquivo fílmico confirmado do Münchner Stadtmuseum, mas as rotas "
                    "públicas observadas expõem página institucional, história do acervo, programação de sessões, "
                    "ingressos e vídeos institucionais gerais do museu. Não foi localizada rota pública estável "
                    "de catálogo de vídeos de acervo do Filmmuseum."
                ),
                "collection_route_attempted": (
                    "Página oficial do Filmmuseum, página Geschichte, Spielplan & Tickets, Filmreihen, página geral "
                    "de vídeos do Münchner Stadtmuseum, homepage da Sammlung Online e formulário público de busca "
                    "da Sammlung Online com o termo Film."
                ),
                "attempt_summary": (
                    "A página Geschichte confirma arquivo com cerca de 6.000 cópias, mas não oferece catálogo público "
                    "de vídeo. A programação lista sessões e ingressos. A página geral de vídeos usa YouTube para "
                    "conteúdo institucional do museu inteiro. A consulta controlada à Sammlung Online não produziu "
                    "rota estável de recorte Filmmuseum/Filmarchiv."
                ),
                "methodological_explanation": (
                    "A decisão não nega a existência nem a relevância do acervo. Ela evita tratar programação de sala, "
                    "bilheteria, vídeos institucionais gerais ou busca instável em coleção museológica ampla como "
                    "corpus audiovisual de arquivo. Para entrar no corpus ativo, a unidade precisa expor registros "
                    "públicos de vídeo de acervo ou metadados audiovisuais coletáveis de forma reprodutível."
                ),
                "evidence_status": "arquivo_filmico_confirmado_sem_catalogo_publico_de_video_coletavel",
                "protocol_status": "acervo_preservado_e_programacao_publica_sem_rota_de_video_de_acervo",
                "next_step": "retestar site oficial, Sammlung Online e eventuais catálogos digitais em ciclos futuros",
                "blocks_expansion": False,
                "rule_version": FILMMUSEUM_MUNCHEN_PROTOCOL_RULE_VERSION,
            }
        ],
        columns=EUROPE_CLOSURE_EXCLUDED_UNITS_COLUMNS,
    )


def write_filmmuseum_munchen_protocol_probe(output_dir: Path = OUTPUT_DIR, fetcher=fetch_filmmuseum_munchen_probe):
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol_df = build_filmmuseum_munchen_protocol_probe(fetcher=fetcher)
    protocol_df.to_csv(output_dir / FILMMUSEUM_MUNCHEN_PROTOCOL_FILENAME, index=False, encoding="utf-8-sig")
    excluded_df = merge_existing_excluded_units(
        output_dir,
        build_filmmuseum_munchen_non_incorporated_register(protocol_df),
    )
    excluded_df.to_csv(output_dir / EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME, index=False, encoding="utf-8-sig")
    return protocol_df


__all__ = [
    "FILMMUSEUM_MUNCHEN_ACCESS_CATEGORY",
    "FILMMUSEUM_MUNCHEN_PROTOCOL_COLUMNS",
    "FILMMUSEUM_MUNCHEN_PROTOCOL_FILENAME",
    "FILMMUSEUM_MUNCHEN_PROTOCOL_PROBES",
    "FILMMUSEUM_MUNCHEN_PROTOCOL_RULE_VERSION",
    "build_filmmuseum_munchen_non_incorporated_register",
    "build_filmmuseum_munchen_protocol_probe",
    "write_filmmuseum_munchen_protocol_probe",
]
