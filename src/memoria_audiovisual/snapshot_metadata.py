import json
import re
from datetime import UTC, datetime

import pandas as pd

from .analysis import filter_curatorial_video_catalog
from .analysis import filter_in_scope_video_links_df
from .config import (
    AAPB_FAQ_URL,
    APE_CONTENT_PDF_URL,
    ARCHIPOP_FILMS_URL,
    EUSCREEN_COLLECTIONS_URL,
    EUROPEAN_FILM_GATEWAY_HOME_URL,
    EUROPEANA_HOME_URL,
    INA_INSTITUTION_URL,
    PARES_HOME_URL,
    PPA_HOME_URL,
)
from .output_files import (
    AAPB_OUTPUT_FILES,
    APE_OUTPUT_FILES,
    ARCHIPOP_OUTPUT_FILES,
    EUSCREEN_OUTPUT_FILES,
    EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
    EUROPEANA_OUTPUT_FILES,
    INA_OUTPUT_FILES,
    PARES_OUTPUT_FILES,
    PPA_OUTPUT_FILES,
)


RAW_OUTPUT_KEYS = [
    "institutions",
    "summary",
    "video_links",
    "internal_pages",
    "report_json",
    "report_txt",
    "report_xlsx",
]

ANALYTIC_OUTPUT_KEYS = [
    "analytic_summary",
    "analytic_video_catalog",
    "availability_summary",
    "availability_reasons",
    "visibility_summary",
    "theme_summary",
    "theme_country",
    "archive_type_summary",
    "theme_platform",
    "theme_archive_type",
    "visibility_archive_type",
]


def _utcnow_iso():
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _extract_source_status_date(source_url):
    match = re.search(r"(20\d{2})(\d{2})(\d{2})", source_url)
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{year}-{month}-{day}"


def _build_observation_key(dataset, raw_outputs_last_modified_at, analytic_outputs_last_modified_at, source_status_date):
    stable_anchor = raw_outputs_last_modified_at or analytic_outputs_last_modified_at or source_status_date or _utcnow_iso()
    return f"{dataset}:{stable_anchor}"


def _safe_count(frame):
    if frame is None or frame.empty:
        return 0
    return int(len(frame))


def _safe_sum(frame, column):
    if frame is None or frame.empty or column not in frame.columns:
        return 0
    return int(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


def _count_distinct(frame, column):
    if frame is None or frame.empty or column not in frame.columns:
        return 0
    return int(frame[column].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique())


def _timestamp_from_keys(output_dir, output_files, keys):
    timestamps = []
    for key in keys:
        path = output_dir / output_files[key]
        if path.exists():
            timestamps.append(
                datetime.fromtimestamp(path.stat().st_mtime, UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
    return max(timestamps) if timestamps else ""


def _build_file_manifest(output_dir, output_files):
    manifest = {}
    for key, filename in output_files.items():
        path = output_dir / filename
        manifest[key] = {
            "filename": filename,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "last_modified_at": (
                datetime.fromtimestamp(path.stat().st_mtime, UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
                if path.exists()
                else ""
            ),
        }
    return manifest


def build_snapshot_metadata(
    output_dir,
    *,
    dataset,
    source_url,
    output_files,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    raw_outputs_last_modified_at = _timestamp_from_keys(output_dir, output_files, RAW_OUTPUT_KEYS)
    analytic_outputs_last_modified_at = _timestamp_from_keys(output_dir, output_files, ANALYTIC_OUTPUT_KEYS)
    source_status_date = _extract_source_status_date(source_url)
    curatorial_catalog_df = filter_curatorial_video_catalog(
        analysis_frames.get("analytic_video_catalog", pd.DataFrame())
    )
    curatorial_links_df = filter_in_scope_video_links_df(links_df)
    analytic_summary_df = analysis_frames.get("analytic_summary", summary_df)
    return {
        "dataset": dataset,
        "generated_at": _utcnow_iso(),
        "generated_by": generated_by,
        "observation_key": _build_observation_key(
            dataset,
            raw_outputs_last_modified_at,
            analytic_outputs_last_modified_at,
            source_status_date,
        ),
        "source_url": source_url,
        "source_status_date": source_status_date,
        "raw_outputs_last_modified_at": raw_outputs_last_modified_at,
        "analytic_outputs_last_modified_at": analytic_outputs_last_modified_at,
        "counts": {
            "institutions": _safe_count(summary_df),
            "institutions_with_website": _safe_sum(summary_df, "website_available"),
            "institutions_with_video_links": int(
                pd.to_numeric(
                    analytic_summary_df.get("video_links_found_total", 0),
                    errors="coerce",
                ).fillna(0).gt(0).sum()
            )
            if analytic_summary_df is not None and not analytic_summary_df.empty
            else 0,
            "video_links_total": _safe_count(curatorial_links_df),
            "videos_in_curatorial_catalog": _safe_count(curatorial_catalog_df),
            "visibility_categories": _safe_count(analysis_frames.get("visibility_summary")),
            "theme_categories": _safe_count(analysis_frames.get("theme_summary")),
            "archive_type_categories": _safe_count(analysis_frames.get("archive_type_summary")),
            "platforms_detected": _count_distinct(curatorial_links_df, "platform"),
            "countries_with_videos": _count_distinct(curatorial_catalog_df, "country"),
        },
        "files": _build_file_manifest(output_dir, output_files),
    }


def save_snapshot_metadata_payload(output_dir, *, output_files, payload):
    path = output_dir / output_files["snapshot_metadata"]
    payload["files"] = _build_file_manifest(output_dir, output_files)
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False, indent=2)

    payload["files"] = _build_file_manifest(output_dir, output_files)
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False, indent=2)
    return payload


def write_snapshot_metadata(
    output_dir,
    *,
    dataset,
    source_url,
    output_files,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    payload = build_snapshot_metadata(
        output_dir,
        dataset=dataset,
        source_url=source_url,
        output_files=output_files,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )
    return save_snapshot_metadata_payload(
        output_dir,
        output_files=output_files,
        payload=payload,
    )


def build_ape_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="ape",
        source_url=APE_CONTENT_PDF_URL,
        output_files=APE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_aapb_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="aapb",
        source_url=AAPB_FAQ_URL,
        output_files=AAPB_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_archipop_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="archipop",
        source_url=ARCHIPOP_FILMS_URL,
        output_files=ARCHIPOP_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_ape_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="ape",
        source_url=APE_CONTENT_PDF_URL,
        output_files=APE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_aapb_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="aapb",
        source_url=AAPB_FAQ_URL,
        output_files=AAPB_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_archipop_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="archipop",
        source_url=ARCHIPOP_FILMS_URL,
        output_files=ARCHIPOP_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_ina_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="ina",
        source_url=INA_INSTITUTION_URL,
        output_files=INA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_euscreen_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="euscreen",
        source_url=EUSCREEN_COLLECTIONS_URL,
        output_files=EUSCREEN_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_pares_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="pares",
        source_url=PARES_HOME_URL,
        output_files=PARES_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_ppa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="portal-portugues-arquivos",
        source_url=PPA_HOME_URL,
        output_files=PPA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_european_film_gateway_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="european-film-gateway",
        source_url=EUROPEAN_FILM_GATEWAY_HOME_URL,
        output_files=EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_europeana_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="europeana",
        source_url=EUROPEANA_HOME_URL,
        output_files=EUROPEANA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_euscreen_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="euscreen",
        source_url=EUSCREEN_COLLECTIONS_URL,
        output_files=EUSCREEN_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_pares_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="pares",
        source_url=PARES_HOME_URL,
        output_files=PARES_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_ppa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="portal-portugues-arquivos",
        source_url=PPA_HOME_URL,
        output_files=PPA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_european_film_gateway_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="european-film-gateway",
        source_url=EUROPEAN_FILM_GATEWAY_HOME_URL,
        output_files=EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_europeana_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="europeana",
        source_url=EUROPEANA_HOME_URL,
        output_files=EUROPEANA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_ina_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="ina",
        source_url=INA_INSTITUTION_URL,
        output_files=INA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


__all__ = [
    "ANALYTIC_OUTPUT_KEYS",
    "RAW_OUTPUT_KEYS",
    "build_aapb_snapshot_metadata",
    "build_ape_snapshot_metadata",
    "build_archipop_snapshot_metadata",
    "build_euscreen_snapshot_metadata",
    "build_european_film_gateway_snapshot_metadata",
    "build_europeana_snapshot_metadata",
    "build_ina_snapshot_metadata",
    "build_pares_snapshot_metadata",
    "build_ppa_snapshot_metadata",
    "build_snapshot_metadata",
    "save_snapshot_metadata_payload",
    "write_aapb_snapshot_metadata",
    "write_ape_snapshot_metadata",
    "write_archipop_snapshot_metadata",
    "write_euscreen_snapshot_metadata",
    "write_european_film_gateway_snapshot_metadata",
    "write_europeana_snapshot_metadata",
    "write_ina_snapshot_metadata",
    "write_pares_snapshot_metadata",
    "write_ppa_snapshot_metadata",
    "write_snapshot_metadata",
]
