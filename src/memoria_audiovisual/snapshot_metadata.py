import json
import re
from datetime import UTC, datetime

import pandas as pd

from .analysis import filter_curatorial_video_catalog
from .config import APE_CONTENT_PDF_URL
from .output_files import APE_OUTPUT_FILES


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


def _timestamp_from_keys(output_dir, keys):
    timestamps = []
    for key in keys:
        path = output_dir / APE_OUTPUT_FILES[key]
        if path.exists():
            timestamps.append(
                datetime.fromtimestamp(path.stat().st_mtime, UTC)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
    return max(timestamps) if timestamps else ""


def _build_file_manifest(output_dir):
    manifest = {}
    for key, filename in APE_OUTPUT_FILES.items():
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


def build_ape_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    curatorial_catalog_df = filter_curatorial_video_catalog(
        analysis_frames.get("analytic_video_catalog", pd.DataFrame())
    )
    return {
        "dataset": "ape",
        "generated_at": _utcnow_iso(),
        "generated_by": generated_by,
        "source_url": APE_CONTENT_PDF_URL,
        "source_status_date": _extract_source_status_date(APE_CONTENT_PDF_URL),
        "raw_outputs_last_modified_at": _timestamp_from_keys(output_dir, RAW_OUTPUT_KEYS),
        "analytic_outputs_last_modified_at": _timestamp_from_keys(output_dir, ANALYTIC_OUTPUT_KEYS),
        "counts": {
            "institutions": _safe_count(summary_df),
            "institutions_with_website": _safe_sum(summary_df, "website_available"),
            "institutions_with_video_links": int(
                pd.to_numeric(
                    summary_df.get("video_links_found_total", 0),
                    errors="coerce",
                ).fillna(0).gt(0).sum()
            )
            if summary_df is not None and not summary_df.empty
            else 0,
            "video_links_total": _safe_count(links_df),
            "videos_in_curatorial_catalog": _safe_count(curatorial_catalog_df),
            "visibility_categories": _safe_count(analysis_frames.get("visibility_summary")),
            "theme_categories": _safe_count(analysis_frames.get("theme_summary")),
            "archive_type_categories": _safe_count(analysis_frames.get("archive_type_summary")),
            "platforms_detected": _count_distinct(links_df, "platform"),
            "countries_with_videos": _count_distinct(curatorial_catalog_df, "country"),
        },
        "files": _build_file_manifest(output_dir),
    }


def write_ape_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    path = output_dir / APE_OUTPUT_FILES["snapshot_metadata"]
    payload = build_ape_snapshot_metadata(
        output_dir,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False, indent=2)
    payload["files"] = _build_file_manifest(output_dir)
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False, indent=2)
    return payload


__all__ = [
    "ANALYTIC_OUTPUT_KEYS",
    "RAW_OUTPUT_KEYS",
    "build_ape_snapshot_metadata",
    "write_ape_snapshot_metadata",
]
