import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    BFI_ARCHIVE_FAQ_URL,
    BFI_ARCHIVE_SEARCH_URL,
    BFI_MEDIATHEQUE_URL,
    BFI_NATIONAL_ARCHIVE_URL,
    BFI_PLAYER_FREE_URL,
    BFI_REPLAY_ABOUT_URL,
    BFI_REPLAY_COLLECTIONS_URL,
    BFI_REPLAY_HOME_URL,
    BFI_REPLAY_SEARCH_URL,
    BFI_RESEARCH_VIEWING_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


BFI_REPOSITORY_CODE = "GB-BFI-NATIONAL-ARCHIVE"
BFI_ARCHIVE_TYPE = "Film and television archive"
BFI_COUNTRY = normalize_country("United Kingdom")
BFI_INSTITUTION_NAME = "BFI National Archive"
BFI_PLATFORM_LABEL = "BFI Replay"
BFI_DETAIL_WORKERS = 4

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "en-GB,en;q=0.9,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url, **kwargs):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True, **kwargs)


def _unwrap_livewire(value):
    if isinstance(value, list):
        if len(value) == 2 and isinstance(value[1], dict) and ("s" in value[1] or "class" in value[1]):
            return _unwrap_livewire(value[0])
        return [_unwrap_livewire(item) for item in value]
    if isinstance(value, dict):
        return {key: _unwrap_livewire(item) for key, item in value.items()}
    return value


def _iter_livewire_snapshots(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    for tag in soup.find_all(attrs={"wire:snapshot": True}):
        try:
            snapshot = json.loads(tag.get("wire:snapshot", ""))
        except Exception:
            continue
        yield snapshot.get("memo", {}).get("name", ""), _unwrap_livewire(snapshot.get("data", {}))


def _extract_search_payload(html_text):
    for name, data in _iter_livewire_snapshots(html_text):
        if name == "search-page":
            works_data = data.get("worksData") or {}
            return {
                "records": works_data.get("data") or [],
                "meta": data.get("paginationMeta") or works_data.get("meta") or {},
            }
    return {"records": [], "meta": {}}


def _extract_detail_payload(html_text):
    best_payload = {}
    for name, data in _iter_livewire_snapshots(html_text):
        if name == "components.video-player":
            return {
                "work": data.get("work") or {},
                "video": data.get("workVideo") or data.get("work", {}).get("video") or {},
                "video_accessible": bool(data.get("videoAccessible")),
                "account_id": data.get("accountId", ""),
                "asset_id": data.get("assetId", ""),
                "player_id": data.get("playerId", ""),
            }
        if name == "video-page":
            best_payload = {
                "work": data.get("work") or {},
                "video": (data.get("work") or {}).get("video") or {},
                "video_accessible": True,
                "account_id": "",
                "asset_id": "",
                "player_id": "",
            }
    return best_payload


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if isinstance(value, dict):
        return _as_list(value.get("locations") or value.get("data"))
    text = _clean_text(value)
    return [text] if text else []


def _join(values):
    return "; ".join(_as_list(values))


def _extract_year(*values):
    text = " ".join(str(value or "") for value in values)
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text)
    return match.group(1) if match else ""


def _page_url(page_number):
    return BFI_REPLAY_SEARCH_URL if page_number == 1 else f"{BFI_REPLAY_SEARCH_URL}?page={page_number}"


def collect_bfi_institutions():
    return [
        {
            "institution": BFI_INSTITUTION_NAME,
            "slug": slugify(BFI_INSTITUTION_NAME),
            "country": BFI_COUNTRY,
            "continent": country_to_continent(BFI_COUNTRY),
            "repository_code": BFI_REPOSITORY_CODE,
            "archive_type": BFI_ARCHIVE_TYPE,
            "bfi_detail_url": BFI_NATIONAL_ARCHIVE_URL,
            "external_url": BFI_NATIONAL_ARCHIVE_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_bfi_replay_record(record, detail_payload=None, page_number=1):
    detail_payload = detail_payload or {}
    work = detail_payload.get("work") or {}
    video = detail_payload.get("video") or work.get("video") or record
    record_id = _clean_text(work.get("id") or record.get("workUuid"))
    video_link = urljoin(BFI_REPLAY_HOME_URL, f"/video/{record_id}") if record_id else ""
    title = _clean_text(work.get("displayTitle") or record.get("displayTitle"))
    genres = _as_list(work.get("genres") or record.get("genres"))
    subjects = _as_list(work.get("subjects") or record.get("subjects"))
    locations = _as_list(work.get("locations") or record.get("locations"))
    source_archive = _clean_text(work.get("sourceArchive") or record.get("sourceArchive"))
    availability = _join((video.get("availability") or record.get("availability") or {}).get("locations"))
    asset_id = _clean_text(detail_payload.get("asset_id") or video.get("assetId") or record.get("assetId"))
    account_id = _clean_text(detail_payload.get("account_id") or video.get("accountId") or record.get("accountId"))
    date_value = ""
    dates = work.get("dates")
    if isinstance(dates, dict):
        date_value = _clean_text(dates.get("start"))
    description_parts = [
        "Registro público materializado no BFI Replay.",
        f"disponibilidade: {availability}" if availability else "",
        f"gêneros: {_join(genres)}" if genres else "",
        f"assuntos: {_join(subjects)}" if subjects else "",
        f"locais: {_join(locations)}" if locations else "",
        f"arquivo de origem: {source_archive}" if source_archive else "",
        f"som: {_clean_text(video.get('sound') or record.get('sound'))}" if video.get("sound") or record.get("sound") else "",
        f"duração: {_clean_text(work.get('runningTime') or video.get('duration') or record.get('duration'))} min"
        if work.get("runningTime") or video.get("duration") or record.get("duration")
        else "",
        f"Brightcove: {account_id}/{asset_id}" if account_id and asset_id else "",
        _clean_text(work.get("synopsis")),
        _clean_text(work.get("standfirst")),
        _clean_text(work.get("context")),
        _clean_text(work.get("additionalContext")),
    ]
    return {
        "record_id": record_id,
        "source_kind": "bfi_replay_search_record",
        "video_link": video_link,
        "page_url": video_link,
        "platform": BFI_PLATFORM_LABEL,
        "title": title,
        "subject": _join(genres or subjects),
        "description": _clean_text(" | ".join(part for part in description_parts if part), limit=1400),
        "date": date_value or _extract_year(title),
        "page_number": page_number,
        "embedded": bool(asset_id and account_id),
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": BFI_REPOSITORY_CODE,
        "archive_type": BFI_ARCHIVE_TYPE,
        "bfi_detail_url": BFI_NATIONAL_ARCHIVE_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": BFI_REPLAY_SEARCH_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": BFI_REPLAY_SEARCH_URL,
        "platform": record.get("platform", BFI_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_detail(record):
    record_id = _clean_text(record.get("workUuid"))
    url = urljoin(BFI_REPLAY_HOME_URL, f"/video/{record_id}") if record_id else ""
    if not url:
        return record_id, url, {}, "erro", "", "registro sem identificador"
    try:
        response = _fetch(url)
        response.raise_for_status()
        payload = _extract_detail_payload(response.text)
        return record_id, response.url, payload, "ok", response.status_code, ""
    except Exception as error:
        return record_id, url, {}, "erro", "", str(error)


def collect_bfi_dataset():
    institutions = collect_bfi_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    declared_total = 0
    max_page = 1
    records_by_id = {}
    page_by_id = {}

    contextual_pages = [
        (BFI_NATIONAL_ARCHIVE_URL, "Página institucional do BFI National Archive."),
        (BFI_ARCHIVE_SEARCH_URL, "Collections Search; catálogo de pesquisa, não streaming público integral."),
        (BFI_ARCHIVE_FAQ_URL, "FAQ oficial; documenta Player, Mediatheque, YouTube e acesso presencial."),
        (BFI_RESEARCH_VIEWING_URL, "Research Viewing; acesso por agendamento, sem acesso remoto e com taxas."),
        (BFI_MEDIATHEQUE_URL, "Mediatheque; acesso gratuito em espaços físicos selecionados."),
        (BFI_PLAYER_FREE_URL, "BFI Player Free; superfície de exibição doméstica separada do corpus Replay."),
        (BFI_REPLAY_HOME_URL, "BFI Replay; superfície pública de vídeos e porta de entrada do corpus."),
        (BFI_REPLAY_ABOUT_URL, "About BFI Replay; distingue acesso em casa e vídeos exclusivos em bibliotecas."),
        (BFI_REPLAY_COLLECTIONS_URL, "Coleções do BFI Replay; contexto curatorial, não usada como rota principal."),
    ]
    for url, warning in contextual_pages:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    page = 1
    while page <= max_page:
        url = _page_url(page)
        try:
            response = _fetch(url)
            response.raise_for_status()
            payload = _extract_search_payload(response.text)
            meta = payload.get("meta") or {}
            if page == 1:
                max_page = int(meta.get("last_page") or 1)
                declared_total = int(meta.get("total") or 0)
            page_records = []
            for record in payload.get("records") or []:
                record_id = _clean_text(record.get("workUuid"))
                if not record_id:
                    continue
                records_by_id.setdefault(record_id, record)
                page_by_id.setdefault(record_id, page)
                page_records.append(record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_records),
                    sum(1 for record in page_records if record.get("assetId") and record.get("accountId")),
                    f"Página {page} de {max_page} da busca pública BFI Replay; interface declara {declared_total or 'n/d'} vídeos encontrados.",
                )
            )
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    url,
                    "erro",
                    warning="Falha em página paginada do BFI Replay; completude da rodada fica parcial.",
                    error=str(error),
                )
            )
        page += 1

    detail_payloads = {}
    with ThreadPoolExecutor(max_workers=BFI_DETAIL_WORKERS) as executor:
        futures = {
            executor.submit(_fetch_detail, record): record_id
            for record_id, record in records_by_id.items()
        }
        for future in as_completed(futures):
            record_id, url, payload, status, http_code, error = future.result()
            detail_payloads[record_id] = payload
            embedded = bool(payload.get("asset_id") or (payload.get("video") or {}).get("assetId"))
            internal_pages.append(
                _internal_page_row(
                    institution,
                    url,
                    status,
                    http_code,
                    1 if status == "ok" else 0,
                    1 if embedded else 0,
                    "Página de detalhe do vídeo no BFI Replay; usada para data, descrição e sinal de player.",
                    error,
                )
            )
            if error:
                errors.append(f"{url}: {error}")

    records = [
        parse_bfi_replay_record(record, detail_payloads.get(record_id), page_by_id.get(record_id, 1))
        for record_id, record in records_by_id.items()
    ]
    video_links = [_record_to_video_row(institution, record) for record in records]
    rendered_total = len(video_links)
    embedded_total = sum(1 for record in records if record.get("embedded"))
    missing_from_declared = max(declared_total - rendered_total, 0)
    complete_rendered_route = bool(rendered_total) and not any("search?page" in error for error in errors)
    summary_warning = (
        "Corpus institucional incorporado pelo BFI Replay, recorte público 'Watch anywhere'. "
        f"A interface declarou {declared_total} vídeos encontrados e a rodada materializou {rendered_total} cards "
        f"públicos renderizados em {max_page} páginas; {missing_from_declared} itens declarados não foram expostos "
        "como cards reprodutíveis no HTML público observado. O recorte não equivale ao catálogo total do BFI, "
        "ao Collections Search, ao BFI Player, à Mediatheque, ao acesso presencial de pesquisa ou ao licenciamento."
    )
    summary = [
        {
            **_base_row(institution),
            "partner_site": BFI_REPLAY_SEARCH_URL,
            "partner_domain": normalize_domain(BFI_REPLAY_HOME_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "acessivel" if complete_rendered_route else "instavel",
            "final_url": BFI_REPLAY_SEARCH_URL,
            "video_links_found_total": rendered_total,
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "media" if missing_from_declared else "baixa",
            "warning": summary_warning,
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "BFI_PLATFORM_LABEL",
    "collect_bfi_dataset",
    "collect_bfi_institutions",
    "parse_bfi_replay_record",
]
