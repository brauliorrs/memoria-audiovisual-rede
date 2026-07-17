from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    ECPAD_ARCHIVES_HOME_URL,
    ECPAD_HOME_URL,
    ECPAD_ONLINE_ARCHIVES_URL,
    ECPAD_SEARCH_API_URL,
    ECPAD_SEARCH_SIMPLE_API_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


ECPAD_REPOSITORY_CODE = "FR-ECPAD"
ECPAD_ARCHIVE_TYPE = "Institutional military audiovisual archive with public Arkothèque catalog"
ECPAD_COUNTRY = normalize_country("France")
ECPAD_INSTITUTION_NAME = "ECPAD - Établissement de communication et de production audiovisuelle de la Défense"
ECPAD_PLATFORM_LABEL = "ECPAD Archives"
ECPAD_SEARCH_PAGE_SIZE = 100
ECPAD_REQUEST_PAUSE = 0.05

ECPAD_MOTOR_REF = "arko_default_6989dacfef00f"
ECPAD_MEDIA_TYPE_FILTER_REF = "arko_default_6989f16835299"
ECPAD_ONLINE_VISUAL_FILTER_REF = "arko_default_69d51ed5efc04"
ECPAD_DATE_FILTER_REF = "arko_default_6989e69505787"
ECPAD_PERIOD_FILTER_REF = "arko_default_6989dceba18de"
ECPAD_REFERENCE_QUERY_FILTER_REF = "arko_default_6989dceba96d8"
ECPAD_PERIOD_AGGREGATION_FIELD = "arko_default_6984539046ba8"
ECPAD_REFERENCE_SORT_REF = "arko_default_69c13a2a819a5"
ECPAD_DATE_SORT_REF = "arko_default_69c13ca1b192c"
ECPAD_AUTHOR_SORT_REF = "arko_default_69ca35f186afb"
ECPAD_PLACE_SORT_REF = "arko_default_69ca369ca3153"
ECPAD_VIDEO_VALUE = "Vidéo"
ECPAD_SEARCH_WINDOW_LIMIT = 10000
ECPAD_PAGE_WORKERS = 6
ECPAD_REFERENCE_QUERY_TERMS = ("F", "D", "B", "1", "2", "3", "5", "6", "7", "8")
ECPAD_DATE_RANGES = (
    (1900, 1919),
    (1920, 1929),
    (1930, 1939),
    (1940, 1949),
    (1950, 1959),
    (1960, 1969),
    (1970, 1979),
    (1980, 1989),
    (1990, 1999),
    (2000, 2009),
    (2010, 2019),
    (2020, 2026),
)

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "application/json,text/html,*/*",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url, *, params=None):
    response = None
    for attempt in range(4):
        response = SESSION.get(
            url,
            params=params or {},
            timeout=(8, REQUEST_TIMEOUT),
            allow_redirects=True,
        )
        if response.status_code not in {429, 500, 502, 503, 504}:
            return response
        time.sleep(1.2 * (attempt + 1))
    return response


def _ecpad_detail_url(detail_id):
    return f"{ECPAD_ONLINE_ARCHIVES_URL}?detail={detail_id}" if detail_id else ECPAD_ONLINE_ARCHIVES_URL


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def _extract_date(value):
    text = str(value or "")
    match = re.search(r"\b(\d{2})/(\d{2})/((?:18|19|20)\d{2})\b", text)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"
    return _extract_year(text)


def _field_text(card, field_name, *, limit=1200):
    node = card.select_one(f'span[data-champ="{field_name}"]')
    return _clean_text(node.get_text(" ", strip=True) if node else "", limit=limit)


def _result_detail_id(card):
    detail_node = card.select_one("[data-detail]")
    if detail_node:
        value = _clean_text(detail_node.get("data-detail", ""))
        if value:
            return value
    anchor = card.find("a", href=re.compile(r"[?&]detail=\d+"))
    if anchor:
        match = re.search(r"[?&]detail=(\d+)", anchor.get("href", ""))
        if match:
            return match.group(1)
    return ""


def _search_params(
    *,
    online_visual,
    offset=0,
    page_size=ECPAD_SEARCH_PAGE_SIZE,
    period_value="",
    date_range=None,
    reference_query="",
    sort_ref="",
    sort_dir="ASC",
):
    online_value = "true" if online_visual else "false"
    prefix = f"{ECPAD_MOTOR_REF}--filtreGroupes[groupes][0]"
    params = {
        f"{ECPAD_MOTOR_REF}--from": int(offset),
        f"{ECPAD_MOTOR_REF}--resultSize": int(page_size),
        f"{prefix}[{ECPAD_MEDIA_TYPE_FILTER_REF}][op]": "AND",
        f"{prefix}[{ECPAD_MEDIA_TYPE_FILTER_REF}][q][0]": ECPAD_VIDEO_VALUE,
        f"{prefix}[{ECPAD_ONLINE_VISUAL_FILTER_REF}][op]": "AND",
        f"{prefix}[{ECPAD_ONLINE_VISUAL_FILTER_REF}][q][0]": online_value,
        f"{prefix}[{ECPAD_ONLINE_VISUAL_FILTER_REF}][extras][mode]": "renseigne",
    }
    if period_value:
        params[f"{prefix}[{ECPAD_PERIOD_FILTER_REF}][op]"] = "AND"
        params[f"{prefix}[{ECPAD_PERIOD_FILTER_REF}][q][0]"] = period_value
    if date_range:
        start_year, end_year = date_range
        params[f"{prefix}[{ECPAD_DATE_FILTER_REF}][op]"] = "AND"
        params[f"{prefix}[{ECPAD_DATE_FILTER_REF}][q][0]"] = f"{start_year}-01-01|{end_year}-12-31"
        params[f"{prefix}[{ECPAD_DATE_FILTER_REF}][extras][mode]"] = "slider"
    if reference_query:
        params[f"{prefix}[{ECPAD_REFERENCE_QUERY_FILTER_REF}][op]"] = "AND"
        params[f"{prefix}[{ECPAD_REFERENCE_QUERY_FILTER_REF}][q][0]"] = reference_query
        params[f"{prefix}[{ECPAD_REFERENCE_QUERY_FILTER_REF}][extras][mode]"] = "input"
    if sort_ref:
        params[f"{ECPAD_MOTOR_REF}--sort[0][recTriRefUnique]"] = sort_ref
        params[f"{ECPAD_MOTOR_REF}--sort[0][dir]"] = sort_dir
    return params


def parse_ecpad_search_results(html_text, *, online_visual, page_url=ECPAD_ONLINE_ARCHIVES_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    access_flag = "true" if online_visual else "false"
    access_note = (
        "visual online indicado pela API do catálogo"
        if online_visual
        else "metadado de vídeo sem visual online indicado pela API do catálogo"
    )

    for card in soup.select(".resultat_container"):
        detail_id = _result_detail_id(card)
        reference = _field_text(card, "reference", limit=250)
        title = _field_text(card, "titre", limit=500) or reference
        description_text = _field_text(card, "resumeint", limit=1400)
        if not detail_id and not reference and not title:
            continue
        record_id = detail_id or slugify(reference or title)
        if record_id in seen:
            continue
        seen.add(record_id)
        detail_url = _ecpad_detail_url(detail_id)
        subject = _clean_text(
            " | ".join(
                value
                for value in [
                    f"referência: {reference}" if reference else "",
                    access_note,
                    "tipo documental: vídeo",
                ]
                if value
            ),
            limit=700,
        )
        description = _clean_text(
            " | ".join(
                value
                for value in [
                    f"Ficha pública no ECPAD Archives; media_type=video; visual_online={access_flag}.",
                    description_text,
                ]
                if value
            ),
            limit=1700,
        )
        records.append(
            {
                "record_id": record_id,
                "detail_id": detail_id,
                "reference": reference,
                "source_kind": "ecpad_video_online" if online_visual else "ecpad_video_without_online_visual",
                "page_url": detail_url,
                "video_link": detail_url,
                "platform": ECPAD_PLATFORM_LABEL,
                "title": title,
                "subject": subject,
                "description": description,
                "date": _extract_date(" ".join([title, description_text])),
                "online_visual": online_visual,
                "embedded": online_visual,
            }
        )
    return records


def _fallback_records_from_results(results, *, online_visual):
    access_flag = "true" if online_visual else "false"
    records = []
    for result in results or []:
        detail_id = str(result.get("id", "")).strip()
        title = _clean_text(result.get("intitule", ""), limit=500)
        if not detail_id and not title:
            continue
        records.append(
            {
                "record_id": detail_id or slugify(title),
                "detail_id": detail_id,
                "reference": title,
                "source_kind": "ecpad_video_online" if online_visual else "ecpad_video_without_online_visual",
                "page_url": _ecpad_detail_url(detail_id),
                "video_link": _ecpad_detail_url(detail_id),
                "platform": ECPAD_PLATFORM_LABEL,
                "title": title,
                "subject": "tipo documental: vídeo",
                "description": f"Ficha pública no ECPAD Archives; media_type=video; visual_online={access_flag}.",
                "date": _extract_date(title),
                "online_visual": online_visual,
                "embedded": online_visual,
            }
        )
    return records


def _payload_records(payload, *, online_visual, page_url):
    parsed = parse_ecpad_search_results(payload.get("html", ""), online_visual=online_visual, page_url=page_url)
    if parsed:
        return parsed
    return _fallback_records_from_results(payload.get("results", []), online_visual=online_visual)


def _period_bucket_values(payload):
    for aggregation in payload.get("aggregations", []):
        period_aggregation = aggregation.get(ECPAD_PERIOD_AGGREGATION_FIELD, {})
        terms = period_aggregation.get(f"{ECPAD_PERIOD_AGGREGATION_FIELD}_terms", {})
        values = [bucket.get("key", "") for bucket in terms.get("buckets", []) if bucket.get("key")]
        if values:
            return values
    return []


def _record_key(record):
    return record.get("detail_id") or record.get("record_id") or record.get("video_link") or record.get("title")


def _merge_records(records_by_key, records):
    added = 0
    for record in records:
        key = _record_key(record)
        if key and key not in records_by_key:
            records_by_key[key] = record
            added += 1
    return added


def _discover_period_values(*, online_visual):
    try:
        page_url, payload = _fetch_payload(
            ECPAD_SEARCH_API_URL,
            _search_params(online_visual=online_visual, offset=0),
        )
        return _period_bucket_values(payload)
    except Exception as error:
        status_label = "online" if online_visual else "sem visual online"
        print(f" - ECPAD {status_label}: não foi possível ler buckets de período ({error}).")
        return []


def _fetch_payload(endpoint_url, params):
    response = _fetch(endpoint_url, params=params)
    response.raise_for_status()
    return response.url, response.json()


def _collect_query_window(
    *,
    online_visual,
    params_builder,
    label,
    max_records=None,
    window_limit=ECPAD_SEARCH_WINDOW_LIMIT,
    endpoint_url=ECPAD_SEARCH_SIMPLE_API_URL,
):
    records = []
    period_values = []
    page_url, payload = _fetch_payload(endpoint_url, params_builder(0))
    period_values = _period_bucket_values(payload)
    declared_total = int(payload.get("total") or 0)
    records.extend(_payload_records(payload, online_visual=online_visual, page_url=page_url))
    if max_records and len(records) >= max_records:
        return records[:max_records], declared_total, period_values, True

    window_end = min(declared_total, window_limit)
    offsets = list(range(ECPAD_SEARCH_PAGE_SIZE, window_end, ECPAD_SEARCH_PAGE_SIZE))
    if max_records:
        offsets = offsets[: max(0, (max_records // ECPAD_SEARCH_PAGE_SIZE) + 1)]

    page_results = []
    with ThreadPoolExecutor(max_workers=ECPAD_PAGE_WORKERS) as executor:
        futures = {
            executor.submit(_fetch_payload, endpoint_url, params_builder(offset)): offset
            for offset in offsets
        }
        for future in as_completed(futures):
            offset = futures[future]
            fetched_page_url, fetched_payload = future.result()
            page_results.append(
                (
                    offset,
                    _payload_records(fetched_payload, online_visual=online_visual, page_url=fetched_page_url),
                )
            )
            if offset and offset % 5000 == 0:
                status_label = "online" if online_visual else "sem visual online"
                print(f" - ECPAD {status_label} ({label}): {offset}/{declared_total}")
            time.sleep(ECPAD_REQUEST_PAUSE)

    for _, page_records in sorted(page_results, key=lambda item: item[0]):
        records.extend(page_records)
        if max_records and len(records) >= max_records:
            return records[:max_records], declared_total, period_values, True
    return records, declared_total, period_values, window_end >= declared_total


def _collect_records_for_status(*, online_visual, max_records=None):
    if max_records:
        records, declared_total, _, _ = _collect_query_window(
            online_visual=online_visual,
            params_builder=lambda offset: _search_params(online_visual=online_visual, offset=offset),
            label="rodada limitada",
            max_records=max_records,
        )
        return records, declared_total

    records_by_key = {}
    period_values = _discover_period_values(online_visual=online_visual)
    declared_total = 0

    def collect_slice(label, params_builder, *, window_limit=ECPAD_SEARCH_WINDOW_LIMIT):
        nonlocal declared_total, period_values
        if declared_total and len(records_by_key) >= declared_total:
            return
        records, total, discovered_period_values, _ = _collect_query_window(
            online_visual=online_visual,
            params_builder=params_builder,
            label=label,
            window_limit=window_limit,
        )
        declared_total = max(declared_total, total)
        if discovered_period_values and not period_values:
            period_values = discovered_period_values
        added = _merge_records(records_by_key, records)
        if added or label.startswith("referência ") or len(records_by_key) >= declared_total:
            status_label = "online" if online_visual else "sem visual online"
            print(f" - ECPAD {status_label} ({label}): +{added}; {len(records_by_key)}/{declared_total}")

    collect_slice(
        "referência ASC",
        lambda offset: _search_params(
            online_visual=online_visual,
            offset=offset,
            sort_ref=ECPAD_REFERENCE_SORT_REF,
            sort_dir="ASC",
        ),
    )
    collect_slice(
        "referência DESC",
        lambda offset: _search_params(
            online_visual=online_visual,
            offset=offset,
            sort_ref=ECPAD_REFERENCE_SORT_REF,
            sort_dir="DESC",
        ),
    )

    for index, period_value in enumerate(period_values, start=1):
        collect_slice(
            f"período {index}/{len(period_values)}",
            lambda offset, value=period_value: _search_params(
                online_visual=online_visual,
                offset=offset,
                period_value=value,
            ),
        )

    if declared_total and len(records_by_key) < declared_total:
        for reference_query in ECPAD_REFERENCE_QUERY_TERMS:
            collect_slice(
                f"referência contém {reference_query}",
                lambda offset, query=reference_query: _search_params(
                    online_visual=online_visual,
                    offset=offset,
                    reference_query=query,
                ),
            )

    if declared_total and len(records_by_key) < declared_total:
        for start_year, end_year in ECPAD_DATE_RANGES:
            collect_slice(
                f"data {start_year}-{end_year}",
                lambda offset, date_range=(start_year, end_year): _search_params(
                    online_visual=online_visual,
                    offset=offset,
                    date_range=date_range,
                ),
            )

    if declared_total and len(records_by_key) < declared_total:
        for sort_ref, sort_label in [
            (ECPAD_DATE_SORT_REF, "data"),
            (ECPAD_AUTHOR_SORT_REF, "autor"),
            (ECPAD_PLACE_SORT_REF, "lugar"),
        ]:
            for sort_dir in ["ASC", "DESC"]:
                collect_slice(
                    f"{sort_label} {sort_dir}",
                    lambda offset, ref=sort_ref, direction=sort_dir: _search_params(
                        online_visual=online_visual,
                        offset=offset,
                        sort_ref=ref,
                        sort_dir=direction,
                    ),
                )

    if declared_total and len(records_by_key) < declared_total:
        status_label = "online" if online_visual else "sem visual online"
        print(
            f" - ECPAD {status_label}: lacuna metodológica de "
            f"{declared_total - len(records_by_key)} registros não alcançados pela API pública."
        )
    return list(records_by_key.values()), declared_total


def _env_max_records():
    value = os.environ.get("ECPAD_MAX_RECORDS", "").strip()
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def collect_ecpad_institutions():
    return [
        {
            "institution": ECPAD_INSTITUTION_NAME,
            "slug": slugify("ecpad"),
            "country": ECPAD_COUNTRY,
            "continent": country_to_continent(ECPAD_COUNTRY),
            "repository_code": ECPAD_REPOSITORY_CODE,
            "archive_type": ECPAD_ARCHIVE_TYPE,
            "ecpad_detail_url": ECPAD_ARCHIVES_HOME_URL,
            "external_url": ECPAD_ONLINE_ARCHIVES_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": ECPAD_REPOSITORY_CODE,
        "archive_type": ECPAD_ARCHIVE_TYPE,
        "ecpad_detail_url": ECPAD_ARCHIVES_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": ECPAD_ONLINE_ARCHIVES_URL,
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
        "partner_site": ECPAD_ONLINE_ARCHIVES_URL,
        "platform": ECPAD_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_ecpad_dataset(max_records_per_status=None):
    max_records_per_status = max_records_per_status or _env_max_records()
    institutions = collect_ecpad_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []

    for url, warning in [
        (ECPAD_HOME_URL, "Site institucional do ECPAD."),
        (ECPAD_ARCHIVES_HOME_URL, "Página oficial de arquivos; informa filmes, vídeos e fotografias acessíveis em parte online."),
        (ECPAD_ONLINE_ARCHIVES_URL, "Catálogo público Arkothèque usado como rota de corpus."),
    ]:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    public_records, public_declared_total = _collect_records_for_status(
        online_visual=True,
        max_records=max_records_per_status,
    )
    restricted_records, restricted_declared_total = _collect_records_for_status(
        online_visual=False,
        max_records=max_records_per_status,
    )
    records = public_records + restricted_records
    video_links = [_record_to_video_row(institution, record) for record in records]

    internal_pages.append(
        _internal_page_row(
            institution,
            ECPAD_SEARCH_API_URL,
            "ok",
            200,
            public_declared_total,
            public_declared_total,
            "Consulta API: tipo Vídeo + Visuel en ligne=true.",
        )
    )
    internal_pages.append(
        _internal_page_row(
            institution,
            ECPAD_SEARCH_API_URL,
            "ok",
            200,
            restricted_declared_total,
            0,
            "Consulta API: tipo Vídeo + Visuel en ligne=false; metadados públicos sem visual online.",
        )
    )

    total_declared = public_declared_total + restricted_declared_total
    collected_total = len(video_links)
    complete_collection = collected_total >= total_declared if total_declared else bool(video_links)
    warning = (
        "Corpus ECPAD incorporado pela API Arkothèque do catálogo público. "
        f"A faceta técnica separa {total_declared} registros do tipo Vídeo: "
        f"{public_declared_total} com visual online e {restricted_declared_total} sem visual online. "
        "A coleta usa janelas oficiais de ordenação, período e data para respeitar o limite público "
        f"de paginação da Arkothèque e materializou {collected_total} registros nesta rodada. "
        "Não baixa mídia e não contorna restrições."
    )
    if not complete_collection and not max_records_per_status:
        warning = (
            f"{warning} Lacuna registrada: {total_declared - collected_total} registros declarados pela API "
            "não foram alcançados pelas rotas públicas testadas."
        )
    if max_records_per_status:
        warning = (
            f"{warning} Rodada limitada por ECPAD_MAX_RECORDS={max_records_per_status}; "
            "os totais declarados permanecem registrados para auditoria metodológica."
        )

    summary = [
        {
            **_base_row(institution),
            "partner_site": ECPAD_ONLINE_ARCHIVES_URL,
            "partner_domain": normalize_domain(ECPAD_ONLINE_ARCHIVES_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_collection or max_records_per_status else "parcial",
            "final_url": ECPAD_ONLINE_ARCHIVES_URL,
            "video_links_found_total": collected_total,
            "embedded_video_signals_total": len(public_records),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if video_links else "alta",
            "warning": warning,
            "error": "; ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "ECPAD_ARCHIVE_TYPE",
    "ECPAD_INSTITUTION_NAME",
    "ECPAD_PLATFORM_LABEL",
    "ECPAD_REPOSITORY_CODE",
    "collect_ecpad_dataset",
    "collect_ecpad_institutions",
    "parse_ecpad_search_results",
]
