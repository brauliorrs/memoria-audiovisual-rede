import json
import re
from datetime import UTC, datetime

import pandas as pd

from .analysis import filter_curatorial_video_catalog
from .analysis import filter_in_scope_video_links_df
from .config import (
    AAPB_FAQ_URL,
    AAMOD_HOME_URL,
    ANF_EVENTBOOK_URL,
    AQSHF_MOTION_PICTURES_URL,
    APE_CONTENT_PDF_URL,
    ASIM_EFG_SEARCH_URL,
    ARSENAL_FILM_DATABASE_BROWSE_URL,
    ARCHIPOP_FILMS_URL,
    AUTREFOIS_VIDEOS_API_URL,
    BARCH_EFG_COLLECTION_URL,
    BBC_ARCHIVE_TOPIC_URL,
    BFI_REPLAY_SEARCH_URL,
    BNFA_EFG_COLLECTION_URL,
    BNT_ARCHIVE_AZ_URL,
    CCMA_SEARCH_API_URL,
    CZECH_TELEVISION_IVYSILANI_URL,
    DFF_FILMPORTAL_VIDEOS_URL,
    DHM_MARSHALL_PLAN_URL,
    EAFA_HOME_URL,
    ECPAD_ONLINE_ARCHIVES_URL,
    ERT_ARCHIVE_HOME_URL,
    EYE_FILM_FRAGMENT_LIST_URL,
    ARKAADER_FILM_SHELF_URL,
    CSC_CINETECA_VIDEO_CATALOG_URL,
    FAR_FILMS_URL,
    FINA_VIDEO_LIST_URL,
    MEMORYSCAPES_ARCHIVE_URL,
    FILMARCHIV_AUSTRIA_ON_URL,
    DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL,
    FILMOTECA_CATALUNYA_PLATFO_URL,
    FILMOTECA_ESPANOLA_PLATFO_URL,
    FILMOTECA_VALENCIANA_RESTORATIONS_URL,
    DEUTSCHE_KINEMATHEK_STREAMING_URL,
    DR_GENSYN_URL,
    CICLIC_FILMS_ARCHIVES_URL,
    CINEAM_FILMS_URL,
    CINEMEMOIRE_SEARCH_URL,
    CINEARCHIVES_CATALOG_URL,
    CDNA_FILMS_URL,
    CINEMATHEQUE_BRETAGNE_FILMS_URL,
    CINEMATHEQUE_FRANCAISE_HENRI_URL,
    CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL,
    CINEMATEK_BE_FILM_URL,
    CPSA_FILMS_URL,
    CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
    SAINT_ETIENNE_COLLECTIONS_URL,
    CINEMATECA_PT_VIDEO_LIST_URL,
    FILMOTECA_VASCA_MULTIMEDIA_URL,
    CNCAFF_EFG_SEARCH_URL,
    CNA_SEARCH_PROFILE_URL,
    EUSCREEN_COLLECTIONS_URL,
    EUROPEAN_FILM_GATEWAY_HOME_URL,
    EUROPEANA_HOME_URL,
    IAM_MEDIAS_API_URL,
    INA_INSTITUTION_URL,
    LUCE_CATALOG_FILMS_URL,
    PARES_HOME_URL,
    PPA_HOME_URL,
    SFA_HOME_URL,
)
from .output_files import (
    AAPB_OUTPUT_FILES,
    AAMOD_OUTPUT_FILES,
    ANF_OUTPUT_FILES,
    AQSHF_OUTPUT_FILES,
    APE_OUTPUT_FILES,
    ASIM_OUTPUT_FILES,
    ARSENAL_OUTPUT_FILES,
    ARCHIPOP_OUTPUT_FILES,
    AUTREFOIS_OUTPUT_FILES,
    BARCH_OUTPUT_FILES,
    BBC_OUTPUT_FILES,
    BFI_OUTPUT_FILES,
    BNFA_OUTPUT_FILES,
    BNT_OUTPUT_FILES,
    CCMA_OUTPUT_FILES,
    CZECH_TELEVISION_OUTPUT_FILES,
    DFF_OUTPUT_FILES,
    DHM_OUTPUT_FILES,
    EAFA_OUTPUT_FILES,
    ECPAD_OUTPUT_FILES,
    ERT_OUTPUT_FILES,
    EYE_OUTPUT_FILES,
    ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES,
    CSC_CINETECA_OUTPUT_FILES,
    FAR_OUTPUT_FILES,
    FINA_OUTPUT_FILES,
    HOME_MOVIES_OUTPUT_FILES,
    FILMARCHIV_AUSTRIA_OUTPUT_FILES,
    FILMMUSEUM_DUSSELDORF_OUTPUT_FILES,
    FILMOTECA_CATALUNYA_OUTPUT_FILES,
    FILMOTECA_ESPANOLA_OUTPUT_FILES,
    FILMOTECA_VALENCIANA_OUTPUT_FILES,
    DEUTSCHE_KINEMATHEK_OUTPUT_FILES,
    DR_OUTPUT_FILES,
    CICLIC_OUTPUT_FILES,
    CINEAM_OUTPUT_FILES,
    CINEMEMOIRE_OUTPUT_FILES,
    CINEARCHIVES_OUTPUT_FILES,
    CDNA_OUTPUT_FILES,
    CINEMATHEQUE_BRETAGNE_OUTPUT_FILES,
    CINEMATHEQUE_FRANCAISE_OUTPUT_FILES,
    CINEMATHEQUE_SUISSE_OUTPUT_FILES,
    CINEMATEK_OUTPUT_FILES,
    CRNOGORSKA_KINOTEKA_OUTPUT_FILES,
    CPSA_OUTPUT_FILES,
    SAINT_ETIENNE_OUTPUT_FILES,
    CINEMATECA_PT_OUTPUT_FILES,
    FILMOTECA_VASCA_OUTPUT_FILES,
    CNCAFF_OUTPUT_FILES,
    CNA_OUTPUT_FILES,
    EUSCREEN_OUTPUT_FILES,
    EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
    EUROPEANA_OUTPUT_FILES,
    IAM_OUTPUT_FILES,
    INA_OUTPUT_FILES,
    LUCE_OUTPUT_FILES,
    PARES_OUTPUT_FILES,
    PPA_OUTPUT_FILES,
    SFA_OUTPUT_FILES,
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


def build_aamod_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="aamod",
        source_url=AAMOD_HOME_URL,
        output_files=AAMOD_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_sfa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="sfa",
        source_url=SFA_HOME_URL,
        output_files=SFA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_anf_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="anf",
        source_url=ANF_EVENTBOOK_URL,
        output_files=ANF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_aqshf_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="aqshf",
        source_url=AQSHF_MOTION_PICTURES_URL,
        output_files=AQSHF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_iam_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="iam",
        source_url=IAM_MEDIAS_API_URL,
        output_files=IAM_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_autrefois_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="autrefois",
        source_url=AUTREFOIS_VIDEOS_API_URL,
        output_files=AUTREFOIS_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_bbc_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="bbc",
        source_url=BBC_ARCHIVE_TOPIC_URL,
        output_files=BBC_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_bfi_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="bfi",
        source_url=BFI_REPLAY_SEARCH_URL,
        output_files=BFI_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_bnt_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="bnt",
        source_url=BNT_ARCHIVE_AZ_URL,
        output_files=BNT_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_ciclic_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="ciclic",
        source_url=CICLIC_FILMS_ARCHIVES_URL,
        output_files=CICLIC_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cineam_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cineam",
        source_url=CINEAM_FILMS_URL,
        output_files=CINEAM_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cinememoire_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cinememoire",
        source_url=CINEMEMOIRE_SEARCH_URL,
        output_files=CINEMEMOIRE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_ccma_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="ccma",
        source_url=CCMA_SEARCH_API_URL,
        output_files=CCMA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_czech_television_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="czech-television",
        source_url=CZECH_TELEVISION_IVYSILANI_URL,
        output_files=CZECH_TELEVISION_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_dff_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="dff",
        source_url=DFF_FILMPORTAL_VIDEOS_URL,
        output_files=DFF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_dhm_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="dhm",
        source_url=DHM_MARSHALL_PLAN_URL,
        output_files=DHM_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_ecpad_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="ecpad",
        source_url=ECPAD_ONLINE_ARCHIVES_URL,
        output_files=ECPAD_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_eafa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="eafa",
        source_url=EAFA_HOME_URL,
        output_files=EAFA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_ert_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="ert",
        source_url=ERT_ARCHIVE_HOME_URL,
        output_files=ERT_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_deutsche_kinemathek_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="deutsche-kinemathek",
        source_url=DEUTSCHE_KINEMATHEK_STREAMING_URL,
        output_files=DEUTSCHE_KINEMATHEK_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_dr_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="dr",
        source_url=DR_GENSYN_URL,
        output_files=DR_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cinearchives_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cinearchives",
        source_url=CINEARCHIVES_CATALOG_URL,
        output_files=CINEARCHIVES_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cinematheque_bretagne_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cinematheque_bretagne",
        source_url=CINEMATHEQUE_BRETAGNE_FILMS_URL,
        output_files=CINEMATHEQUE_BRETAGNE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cinematheque_francaise_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cinematheque_francaise",
        source_url=CINEMATHEQUE_FRANCAISE_HENRI_URL,
        output_files=CINEMATHEQUE_FRANCAISE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cinematek_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cinematek",
        source_url=CINEMATEK_BE_FILM_URL,
        output_files=CINEMATEK_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_eye_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="eye",
        source_url=EYE_FILM_FRAGMENT_LIST_URL,
        output_files=EYE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_estonian_film_archive_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="estonian_film_archive",
        source_url=ARKAADER_FILM_SHELF_URL,
        output_files=ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_filmarchiv_austria_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="filmarchiv_austria",
        source_url=FILMARCHIV_AUSTRIA_ON_URL,
        output_files=FILMARCHIV_AUSTRIA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_fina_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="fina",
        source_url=FINA_VIDEO_LIST_URL,
        output_files=FINA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_csc_cineteca_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="csc-cineteca-nazionale",
        source_url=CSC_CINETECA_VIDEO_CATALOG_URL,
        output_files=CSC_CINETECA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_far_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="far",
        source_url=FAR_FILMS_URL,
        output_files=FAR_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_home_movies_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="home-movies-memoryscapes",
        source_url=MEMORYSCAPES_ARCHIVE_URL,
        output_files=HOME_MOVIES_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_filmmuseum_dusseldorf_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="filmmuseum_dusseldorf",
        source_url=DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL,
        output_files=FILMMUSEUM_DUSSELDORF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_filmoteca_catalunya_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="filmoteca_catalunya",
        source_url=FILMOTECA_CATALUNYA_PLATFO_URL,
        output_files=FILMOTECA_CATALUNYA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_filmoteca_espanola_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="filmoteca_espanola",
        source_url=FILMOTECA_ESPANOLA_PLATFO_URL,
        output_files=FILMOTECA_ESPANOLA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_filmoteca_valenciana_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="filmoteca_valenciana",
        source_url=FILMOTECA_VALENCIANA_RESTORATIONS_URL,
        output_files=FILMOTECA_VALENCIANA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cinematheque_suisse_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cinematheque-suisse",
        source_url=CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL,
        output_files=CINEMATHEQUE_SUISSE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cpsa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cpsa",
        source_url=CPSA_FILMS_URL,
        output_files=CPSA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_saint_etienne_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="saint_etienne",
        source_url=SAINT_ETIENNE_COLLECTIONS_URL,
        output_files=SAINT_ETIENNE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cdna_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cdna",
        source_url=CDNA_FILMS_URL,
        output_files=CDNA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cna_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cna",
        source_url=CNA_SEARCH_PROFILE_URL,
        output_files=CNA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cinemateca_portuguesa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cinemateca-portuguesa",
        source_url=CINEMATECA_PT_VIDEO_LIST_URL,
        output_files=CINEMATECA_PT_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_filmoteca_vasca_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="filmoteca-vasca",
        source_url=FILMOTECA_VASCA_MULTIMEDIA_URL,
        output_files=FILMOTECA_VASCA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_luce_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="luce",
        source_url=LUCE_CATALOG_FILMS_URL,
        output_files=LUCE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_cnc_aff_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="cnc-aff",
        source_url=CNCAFF_EFG_SEARCH_URL,
        output_files=CNCAFF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_bnfa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="bnfa",
        source_url=BNFA_EFG_COLLECTION_URL,
        output_files=BNFA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_barch_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="barch",
        source_url=BARCH_EFG_COLLECTION_URL,
        output_files=BARCH_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_arsenal_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="arsenal",
        source_url=ARSENAL_FILM_DATABASE_BROWSE_URL,
        output_files=ARSENAL_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_asim_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="asim",
        source_url=ASIM_EFG_SEARCH_URL,
        output_files=ASIM_OUTPUT_FILES,
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


def write_aamod_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="aamod",
        source_url=AAMOD_HOME_URL,
        output_files=AAMOD_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_sfa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="sfa",
        source_url=SFA_HOME_URL,
        output_files=SFA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_anf_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="anf",
        source_url=ANF_EVENTBOOK_URL,
        output_files=ANF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_aqshf_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="aqshf",
        source_url=AQSHF_MOTION_PICTURES_URL,
        output_files=AQSHF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_iam_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="iam",
        source_url=IAM_MEDIAS_API_URL,
        output_files=IAM_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_autrefois_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="autrefois",
        source_url=AUTREFOIS_VIDEOS_API_URL,
        output_files=AUTREFOIS_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_bbc_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="bbc",
        source_url=BBC_ARCHIVE_TOPIC_URL,
        output_files=BBC_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_bfi_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="bfi",
        source_url=BFI_REPLAY_SEARCH_URL,
        output_files=BFI_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_bnt_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="bnt",
        source_url=BNT_ARCHIVE_AZ_URL,
        output_files=BNT_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_ciclic_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="ciclic",
        source_url=CICLIC_FILMS_ARCHIVES_URL,
        output_files=CICLIC_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cineam_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cineam",
        source_url=CINEAM_FILMS_URL,
        output_files=CINEAM_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cinememoire_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cinememoire",
        source_url=CINEMEMOIRE_SEARCH_URL,
        output_files=CINEMEMOIRE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_ccma_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="ccma",
        source_url=CCMA_SEARCH_API_URL,
        output_files=CCMA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_czech_television_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="czech-television",
        source_url=CZECH_TELEVISION_IVYSILANI_URL,
        output_files=CZECH_TELEVISION_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_dff_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="dff",
        source_url=DFF_FILMPORTAL_VIDEOS_URL,
        output_files=DFF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_dhm_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="dhm",
        source_url=DHM_MARSHALL_PLAN_URL,
        output_files=DHM_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_deutsche_kinemathek_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="deutsche-kinemathek",
        source_url=DEUTSCHE_KINEMATHEK_STREAMING_URL,
        output_files=DEUTSCHE_KINEMATHEK_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_dr_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="dr",
        source_url=DR_GENSYN_URL,
        output_files=DR_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cinearchives_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cinearchives",
        source_url=CINEARCHIVES_CATALOG_URL,
        output_files=CINEARCHIVES_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cinematheque_bretagne_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cinematheque_bretagne",
        source_url=CINEMATHEQUE_BRETAGNE_FILMS_URL,
        output_files=CINEMATHEQUE_BRETAGNE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cinematheque_francaise_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cinematheque_francaise",
        source_url=CINEMATHEQUE_FRANCAISE_HENRI_URL,
        output_files=CINEMATHEQUE_FRANCAISE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cinematek_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cinematek",
        source_url=CINEMATEK_BE_FILM_URL,
        output_files=CINEMATEK_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_eye_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="eye",
        source_url=EYE_FILM_FRAGMENT_LIST_URL,
        output_files=EYE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_estonian_film_archive_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="estonian_film_archive",
        source_url=ARKAADER_FILM_SHELF_URL,
        output_files=ESTONIAN_FILM_ARCHIVE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cinematheque_suisse_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cinematheque-suisse",
        source_url=CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL,
        output_files=CINEMATHEQUE_SUISSE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cpsa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cpsa",
        source_url=CPSA_FILMS_URL,
        output_files=CPSA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_saint_etienne_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="saint_etienne",
        source_url=SAINT_ETIENNE_COLLECTIONS_URL,
        output_files=SAINT_ETIENNE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cdna_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cdna",
        source_url=CDNA_FILMS_URL,
        output_files=CDNA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cna_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cna",
        source_url=CNA_SEARCH_PROFILE_URL,
        output_files=CNA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cinemateca_portuguesa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cinemateca-portuguesa",
        source_url=CINEMATECA_PT_VIDEO_LIST_URL,
        output_files=CINEMATECA_PT_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_luce_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="luce",
        source_url=LUCE_CATALOG_FILMS_URL,
        output_files=LUCE_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_cnc_aff_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="cnc-aff",
        source_url=CNCAFF_EFG_SEARCH_URL,
        output_files=CNCAFF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_bnfa_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="bnfa",
        source_url=BNFA_EFG_COLLECTION_URL,
        output_files=BNFA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_barch_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="barch",
        source_url=BARCH_EFG_COLLECTION_URL,
        output_files=BARCH_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_arsenal_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="arsenal",
        source_url=ARSENAL_FILM_DATABASE_BROWSE_URL,
        output_files=ARSENAL_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_asim_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="asim",
        source_url=ASIM_EFG_SEARCH_URL,
        output_files=ASIM_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def build_crnogorska_kinoteka_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return build_snapshot_metadata(
        output_dir,
        dataset="crnogorska-kinoteka",
        source_url=CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
        output_files=CRNOGORSKA_KINOTEKA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_crnogorska_kinoteka_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="crnogorska-kinoteka",
        source_url=CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
        output_files=CRNOGORSKA_KINOTEKA_OUTPUT_FILES,
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


def write_filmarchiv_austria_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="filmarchiv_austria",
        source_url=FILMARCHIV_AUSTRIA_ON_URL,
        output_files=FILMARCHIV_AUSTRIA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_filmmuseum_dusseldorf_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="filmmuseum_dusseldorf",
        source_url=DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL,
        output_files=FILMMUSEUM_DUSSELDORF_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_filmoteca_catalunya_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="filmoteca_catalunya",
        source_url=FILMOTECA_CATALUNYA_PLATFO_URL,
        output_files=FILMOTECA_CATALUNYA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_filmoteca_espanola_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="filmoteca_espanola",
        source_url=FILMOTECA_ESPANOLA_PLATFO_URL,
        output_files=FILMOTECA_ESPANOLA_OUTPUT_FILES,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )


def write_filmoteca_valenciana_snapshot_metadata(
    output_dir,
    *,
    summary_df,
    links_df,
    analysis_frames,
    generated_by,
):
    return write_snapshot_metadata(
        output_dir,
        dataset="filmoteca_valenciana",
        source_url=FILMOTECA_VALENCIANA_RESTORATIONS_URL,
        output_files=FILMOTECA_VALENCIANA_OUTPUT_FILES,
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
    "build_aamod_snapshot_metadata",
    "build_anf_snapshot_metadata",
    "build_ape_snapshot_metadata",
    "build_aqshf_snapshot_metadata",
    "build_asim_snapshot_metadata",
    "build_arsenal_snapshot_metadata",
    "build_archipop_snapshot_metadata",
    "build_autrefois_snapshot_metadata",
    "build_barch_snapshot_metadata",
    "build_bbc_snapshot_metadata",
    "build_bfi_snapshot_metadata",
    "build_bnfa_snapshot_metadata",
    "build_bnt_snapshot_metadata",
    "build_ccma_snapshot_metadata",
    "build_czech_television_snapshot_metadata",
    "build_dff_snapshot_metadata",
    "build_dhm_snapshot_metadata",
    "build_csc_cineteca_snapshot_metadata",
    "build_eafa_snapshot_metadata",
    "build_ecpad_snapshot_metadata",
    "build_ert_snapshot_metadata",
    "build_deutsche_kinemathek_snapshot_metadata",
    "build_dr_snapshot_metadata",
    "build_ciclic_snapshot_metadata",
    "build_cineam_snapshot_metadata",
    "build_cinememoire_snapshot_metadata",
    "build_cinearchives_snapshot_metadata",
    "build_cdna_snapshot_metadata",
    "build_cinematheque_bretagne_snapshot_metadata",
    "build_cinematheque_francaise_snapshot_metadata",
    "build_cinematheque_suisse_snapshot_metadata",
    "build_cinematek_snapshot_metadata",
    "build_eye_snapshot_metadata",
    "build_estonian_film_archive_snapshot_metadata",
    "build_far_snapshot_metadata",
    "build_home_movies_snapshot_metadata",
    "build_fina_snapshot_metadata",
    "build_filmarchiv_austria_snapshot_metadata",
    "build_filmmuseum_dusseldorf_snapshot_metadata",
    "build_filmoteca_catalunya_snapshot_metadata",
    "build_filmoteca_espanola_snapshot_metadata",
    "build_filmoteca_valenciana_snapshot_metadata",
    "build_crnogorska_kinoteka_snapshot_metadata",
    "build_cpsa_snapshot_metadata",
    "build_saint_etienne_snapshot_metadata",
    "build_cinemateca_portuguesa_snapshot_metadata",
    "build_filmoteca_vasca_snapshot_metadata",
    "build_cnc_aff_snapshot_metadata",
    "build_cna_snapshot_metadata",
    "build_luce_snapshot_metadata",
    "build_euscreen_snapshot_metadata",
    "build_european_film_gateway_snapshot_metadata",
    "build_europeana_snapshot_metadata",
    "build_iam_snapshot_metadata",
    "build_ina_snapshot_metadata",
    "build_pares_snapshot_metadata",
    "build_ppa_snapshot_metadata",
    "build_sfa_snapshot_metadata",
    "build_snapshot_metadata",
    "save_snapshot_metadata_payload",
    "write_aapb_snapshot_metadata",
    "write_aamod_snapshot_metadata",
    "write_anf_snapshot_metadata",
    "write_ape_snapshot_metadata",
    "write_aqshf_snapshot_metadata",
    "write_asim_snapshot_metadata",
    "write_arsenal_snapshot_metadata",
    "write_archipop_snapshot_metadata",
    "write_autrefois_snapshot_metadata",
    "write_barch_snapshot_metadata",
    "write_bbc_snapshot_metadata",
    "write_bfi_snapshot_metadata",
    "write_bnfa_snapshot_metadata",
    "write_bnt_snapshot_metadata",
    "write_ccma_snapshot_metadata",
    "write_czech_television_snapshot_metadata",
    "write_dff_snapshot_metadata",
    "write_dhm_snapshot_metadata",
    "write_deutsche_kinemathek_snapshot_metadata",
    "write_dr_snapshot_metadata",
    "write_ciclic_snapshot_metadata",
    "write_cineam_snapshot_metadata",
    "write_cinememoire_snapshot_metadata",
    "write_cinearchives_snapshot_metadata",
    "write_cdna_snapshot_metadata",
    "write_cinematheque_bretagne_snapshot_metadata",
    "write_cinematheque_francaise_snapshot_metadata",
    "write_cinematheque_suisse_snapshot_metadata",
    "write_cinematek_snapshot_metadata",
    "write_eye_snapshot_metadata",
    "write_estonian_film_archive_snapshot_metadata",
    "write_filmarchiv_austria_snapshot_metadata",
    "write_filmmuseum_dusseldorf_snapshot_metadata",
    "write_filmoteca_catalunya_snapshot_metadata",
    "write_filmoteca_espanola_snapshot_metadata",
    "write_filmoteca_valenciana_snapshot_metadata",
    "write_crnogorska_kinoteka_snapshot_metadata",
    "write_cpsa_snapshot_metadata",
    "write_saint_etienne_snapshot_metadata",
    "write_cinemateca_portuguesa_snapshot_metadata",
    "write_cnc_aff_snapshot_metadata",
    "write_cna_snapshot_metadata",
    "write_luce_snapshot_metadata",
    "write_euscreen_snapshot_metadata",
    "write_european_film_gateway_snapshot_metadata",
    "write_europeana_snapshot_metadata",
    "write_iam_snapshot_metadata",
    "write_ina_snapshot_metadata",
    "write_pares_snapshot_metadata",
    "write_ppa_snapshot_metadata",
    "write_sfa_snapshot_metadata",
    "write_snapshot_metadata",
]
