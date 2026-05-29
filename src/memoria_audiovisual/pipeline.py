import pandas as pd

from .analysis import filter_in_scope_video_links_df
from .aapb import collect_aapb_dataset
from .aapb_exports import build_aapb_analysis_extra_sheets
from .aapb_exports import write_aapb_analysis_outputs
from .ape import collect_ape_dataset
from .ape_exports import build_ape_analysis_extra_sheets
from .ape_exports import write_ape_analysis_outputs
from .archipop import collect_archipop_dataset
from .archipop_exports import build_archipop_analysis_extra_sheets
from .archipop_exports import write_archipop_analysis_outputs
from .config import (
    AAPB_FAQ_URL,
    APE_CONTENT_PDF_URL,
    ARCHIPOP_FILMS_URL,
    EUSCREEN_COLLECTIONS_URL,
    EUROPEAN_FILM_GATEWAY_HOME_URL,
    EUROPEANA_HOME_URL,
    INA_INSTITUTION_URL,
    OUTPUT_DIR,
    PARES_HOME_URL,
    PPA_HOME_URL,
)
from .efg import collect_european_film_gateway_dataset
from .efg_exports import (
    build_european_film_gateway_analysis_extra_sheets,
    write_european_film_gateway_analysis_outputs,
)
from .excel_export import save_basic_excel_report
from .europeana import collect_europeana_dataset
from .europeana_exports import build_europeana_analysis_extra_sheets
from .europeana_exports import write_europeana_analysis_outputs
from .euscreen import collect_euscreen_dataset
from .euscreen_exports import build_euscreen_analysis_extra_sheets
from .euscreen_exports import write_euscreen_analysis_outputs
from .ina import collect_ina_dataset
from .ina_exports import build_ina_analysis_extra_sheets
from .ina_exports import write_ina_analysis_outputs
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
from .pares import collect_pares_dataset
from .pares_exports import build_pares_analysis_extra_sheets
from .pares_exports import write_pares_analysis_outputs
from .ppa import collect_ppa_dataset
from .ppa_exports import build_ppa_analysis_extra_sheets
from .ppa_exports import write_ppa_analysis_outputs
from .reporting import build_report_payload, save_csv, save_json_report, save_txt_report
from .snapshot_metadata import (
    build_aapb_snapshot_metadata,
    build_ape_snapshot_metadata,
    build_archipop_snapshot_metadata,
    build_euscreen_snapshot_metadata,
    build_european_film_gateway_snapshot_metadata,
    build_europeana_snapshot_metadata,
    build_ina_snapshot_metadata,
    build_pares_snapshot_metadata,
    build_ppa_snapshot_metadata,
    save_snapshot_metadata_payload,
)
from .timeline import write_timeline_outputs


APE_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "ape_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_ape",
]

APE_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ape_detail_url",
    "content_available_in_ape",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

APE_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ape_detail_url",
    "content_available_in_ape",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

APE_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ape_detail_url",
    "content_available_in_ape",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

ARCHIPOP_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archipop_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

ARCHIPOP_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "archipop_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

ARCHIPOP_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "archipop_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

ARCHIPOP_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "archipop_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

INA_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "ina_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

INA_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ina_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

INA_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ina_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

INA_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "ina_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

EUSCREEN_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "euscreen_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

EUSCREEN_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "euscreen_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

EUSCREEN_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "euscreen_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

EUSCREEN_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "euscreen_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

EUROPEAN_FILM_GATEWAY_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "efg_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

EUROPEAN_FILM_GATEWAY_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "efg_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

EUROPEAN_FILM_GATEWAY_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "efg_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

EUROPEAN_FILM_GATEWAY_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "efg_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

EUROPEANA_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "europeana_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

EUROPEANA_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "europeana_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

EUROPEANA_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "europeana_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

EUROPEANA_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "europeana_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

PARES_INSTITUTION_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "pares_detail_url",
    "archive_type",
    "external_url",
    "website_available",
    "content_available_in_source",
]

PARES_SUMMARY_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "pares_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "partner_domain",
    "status",
    "http_code",
    "integrity_status",
    "final_url",
    "video_links_found_total",
    "embedded_video_signals_total",
    "candidate_internal_pages",
    "priority_review",
    "warning",
    "error",
]

PARES_VIDEO_LINK_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "pares_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "platform",
    "video_link",
    "video_title",
    "video_subject",
    "video_description",
    "video_published_at",
]

PARES_INTERNAL_PAGE_FIELDS = [
    "institution",
    "slug",
    "country",
    "continent",
    "repository_code",
    "archive_type",
    "pares_detail_url",
    "content_available_in_source",
    "website_available",
    "partner_site",
    "internal_page",
    "status",
    "http_code",
    "video_links_found",
    "embedded_signals",
    "warning",
    "error",
]

PPA_INSTITUTION_FIELDS = [field.replace("pares_detail_url", "ppa_detail_url") for field in PARES_INSTITUTION_FIELDS]
PPA_SUMMARY_FIELDS = [field.replace("pares_detail_url", "ppa_detail_url") for field in PARES_SUMMARY_FIELDS]
PPA_VIDEO_LINK_FIELDS = [field.replace("pares_detail_url", "ppa_detail_url") for field in PARES_VIDEO_LINK_FIELDS]
PPA_INTERNAL_PAGE_FIELDS = [field.replace("pares_detail_url", "ppa_detail_url") for field in PARES_INTERNAL_PAGE_FIELDS]
AAPB_INSTITUTION_FIELDS = [field.replace("pares_detail_url", "aapb_detail_url") for field in PARES_INSTITUTION_FIELDS]
AAPB_SUMMARY_FIELDS = [field.replace("pares_detail_url", "aapb_detail_url") for field in PARES_SUMMARY_FIELDS]
AAPB_VIDEO_LINK_FIELDS = [field.replace("pares_detail_url", "aapb_detail_url") for field in PARES_VIDEO_LINK_FIELDS]
AAPB_INTERNAL_PAGE_FIELDS = [field.replace("pares_detail_url", "aapb_detail_url") for field in PARES_INTERNAL_PAGE_FIELDS]


def ensure_fields(rows, fieldnames):
    normalized = []
    for row in rows:
        normalized.append({field: row.get(field, "") for field in fieldnames})
    return normalized


def sync_summary_video_counts(rows_summary, links_df):
    if not rows_summary:
        return rows_summary
    counts = {}
    if links_df is not None and not links_df.empty and "slug" in links_df.columns:
        counts = links_df.groupby("slug").size().to_dict()
    synced_rows = []
    for row in rows_summary:
        synced_row = dict(row)
        if "video_links_found_total" in synced_row:
            synced_row["video_links_found_total"] = int(counts.get(synced_row.get("slug"), 0))
        synced_rows.append(synced_row)
    return synced_rows


def _run_corpus_pipeline(
    *,
    source_label,
    source_url,
    collect_dataset,
    institution_fields,
    summary_fields,
    video_link_fields,
    internal_page_fields,
    output_files,
    analysis_output_writer,
    analysis_extra_sheets_builder,
    snapshot_builder,
    report_title,
    institutions_sheet_title,
    generated_by,
):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== ETAPA 1: Coletando instituições do {source_label} ===")
    institutions, rows_summary, rows_video_links, rows_internal_pages = collect_dataset()
    links_df = filter_in_scope_video_links_df(pd.DataFrame(rows_video_links))
    rows_video_links = links_df.to_dict(orient="records")
    rows_summary = sync_summary_video_counts(rows_summary, links_df)
    payload = build_report_payload(
        source_url,
        len(institutions),
        rows_summary,
        rows_video_links,
    )
    summary_df = pd.DataFrame(rows_summary)
    analysis_frames = analysis_output_writer(
        OUTPUT_DIR,
        summary_df,
        links_df,
    )

    save_csv(
        OUTPUT_DIR / output_files["institutions"],
        ensure_fields(institutions, institution_fields),
        institution_fields,
    )
    save_csv(
        OUTPUT_DIR / output_files["summary"],
        ensure_fields(rows_summary, summary_fields),
        summary_fields,
    )
    save_csv(
        OUTPUT_DIR / output_files["video_links"],
        ensure_fields(rows_video_links, video_link_fields),
        video_link_fields,
    )
    save_csv(
        OUTPUT_DIR / output_files["internal_pages"],
        ensure_fields(rows_internal_pages, internal_page_fields),
        internal_page_fields,
    )
    save_json_report(OUTPUT_DIR / output_files["report_json"], payload)
    save_txt_report(
        OUTPUT_DIR / output_files["report_txt"],
        payload,
        rows_summary,
        report_title=report_title,
    )
    save_basic_excel_report(
        OUTPUT_DIR / output_files["report_xlsx"],
        payload,
        rows_summary,
        rows_video_links,
        rows_internal_pages,
        extra_sheets=[
            {
                "title": institutions_sheet_title,
                "rows": ensure_fields(institutions, institution_fields),
                "fieldnames": institution_fields,
            },
            *analysis_extra_sheets_builder(analysis_frames),
        ],
    )
    snapshot_payload = snapshot_builder(
        OUTPUT_DIR,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by=generated_by,
    )
    write_timeline_outputs(
        OUTPUT_DIR,
        dataset=snapshot_payload["dataset"],
        output_files=output_files,
        snapshot_metadata=snapshot_payload,
        summary_df=summary_df,
        analysis_frames=analysis_frames,
    )
    save_snapshot_metadata_payload(
        OUTPUT_DIR,
        output_files=output_files,
        payload=snapshot_payload,
    )

    print("\nArquivos gerados:")
    for filename in output_files.values():
        print(f" - {OUTPUT_DIR / filename}")


def run_pipeline():
    _run_corpus_pipeline(
        source_label="Archives Portal Europe",
        source_url=APE_CONTENT_PDF_URL,
        collect_dataset=collect_ape_dataset,
        institution_fields=APE_INSTITUTION_FIELDS,
        summary_fields=APE_SUMMARY_FIELDS,
        video_link_fields=APE_VIDEO_LINK_FIELDS,
        internal_page_fields=APE_INTERNAL_PAGE_FIELDS,
        output_files=APE_OUTPUT_FILES,
        analysis_output_writer=write_ape_analysis_outputs,
        analysis_extra_sheets_builder=build_ape_analysis_extra_sheets,
        snapshot_builder=build_ape_snapshot_metadata,
        report_title="RELATORIO - ARCHIVES PORTAL EUROPE",
        institutions_sheet_title="APE Institutions",
        generated_by="scripts/run_pipeline.py",
    )


def run_ina_pipeline():
    _run_corpus_pipeline(
        source_label="Institut national de l'audiovisuel (INA)",
        source_url=INA_INSTITUTION_URL,
        collect_dataset=collect_ina_dataset,
        institution_fields=INA_INSTITUTION_FIELDS,
        summary_fields=INA_SUMMARY_FIELDS,
        video_link_fields=INA_VIDEO_LINK_FIELDS,
        internal_page_fields=INA_INTERNAL_PAGE_FIELDS,
        output_files=INA_OUTPUT_FILES,
        analysis_output_writer=write_ina_analysis_outputs,
        analysis_extra_sheets_builder=build_ina_analysis_extra_sheets,
        snapshot_builder=build_ina_snapshot_metadata,
        report_title="RELATORIO - INA",
        institutions_sheet_title="INA Institutions",
        generated_by="scripts/run_ina_pipeline.py",
    )


def run_archipop_pipeline():
    _run_corpus_pipeline(
        source_label="ARCHIPOP",
        source_url=ARCHIPOP_FILMS_URL,
        collect_dataset=collect_archipop_dataset,
        institution_fields=ARCHIPOP_INSTITUTION_FIELDS,
        summary_fields=ARCHIPOP_SUMMARY_FIELDS,
        video_link_fields=ARCHIPOP_VIDEO_LINK_FIELDS,
        internal_page_fields=ARCHIPOP_INTERNAL_PAGE_FIELDS,
        output_files=ARCHIPOP_OUTPUT_FILES,
        analysis_output_writer=write_archipop_analysis_outputs,
        analysis_extra_sheets_builder=build_archipop_analysis_extra_sheets,
        snapshot_builder=build_archipop_snapshot_metadata,
        report_title="RELATORIO - ARCHIPOP",
        institutions_sheet_title="ARCHIPOP Institutions",
        generated_by="scripts/run_archipop_pipeline.py",
    )


def run_euscreen_pipeline():
    _run_corpus_pipeline(
        source_label="EUscreen",
        source_url=EUSCREEN_COLLECTIONS_URL,
        collect_dataset=collect_euscreen_dataset,
        institution_fields=EUSCREEN_INSTITUTION_FIELDS,
        summary_fields=EUSCREEN_SUMMARY_FIELDS,
        video_link_fields=EUSCREEN_VIDEO_LINK_FIELDS,
        internal_page_fields=EUSCREEN_INTERNAL_PAGE_FIELDS,
        output_files=EUSCREEN_OUTPUT_FILES,
        analysis_output_writer=write_euscreen_analysis_outputs,
        analysis_extra_sheets_builder=build_euscreen_analysis_extra_sheets,
        snapshot_builder=build_euscreen_snapshot_metadata,
        report_title="RELATORIO - EUSCREEN",
        institutions_sheet_title="EUscreen Institutions",
        generated_by="scripts/run_euscreen_pipeline.py",
    )


def run_european_film_gateway_pipeline():
    _run_corpus_pipeline(
        source_label="European Film Gateway",
        source_url=EUROPEAN_FILM_GATEWAY_HOME_URL,
        collect_dataset=collect_european_film_gateway_dataset,
        institution_fields=EUROPEAN_FILM_GATEWAY_INSTITUTION_FIELDS,
        summary_fields=EUROPEAN_FILM_GATEWAY_SUMMARY_FIELDS,
        video_link_fields=EUROPEAN_FILM_GATEWAY_VIDEO_LINK_FIELDS,
        internal_page_fields=EUROPEAN_FILM_GATEWAY_INTERNAL_PAGE_FIELDS,
        output_files=EUROPEAN_FILM_GATEWAY_OUTPUT_FILES,
        analysis_output_writer=write_european_film_gateway_analysis_outputs,
        analysis_extra_sheets_builder=build_european_film_gateway_analysis_extra_sheets,
        snapshot_builder=build_european_film_gateway_snapshot_metadata,
        report_title="RELATORIO - EUROPEAN FILM GATEWAY",
        institutions_sheet_title="EFG Institutions",
        generated_by="scripts/run_european_film_gateway_pipeline.py",
    )


def run_europeana_pipeline():
    _run_corpus_pipeline(
        source_label="Europeana",
        source_url=EUROPEANA_HOME_URL,
        collect_dataset=collect_europeana_dataset,
        institution_fields=EUROPEANA_INSTITUTION_FIELDS,
        summary_fields=EUROPEANA_SUMMARY_FIELDS,
        video_link_fields=EUROPEANA_VIDEO_LINK_FIELDS,
        internal_page_fields=EUROPEANA_INTERNAL_PAGE_FIELDS,
        output_files=EUROPEANA_OUTPUT_FILES,
        analysis_output_writer=write_europeana_analysis_outputs,
        analysis_extra_sheets_builder=build_europeana_analysis_extra_sheets,
        snapshot_builder=build_europeana_snapshot_metadata,
        report_title="RELATORIO - EUROPEANA",
        institutions_sheet_title="Europeana Institutions",
        generated_by="scripts/run_europeana_pipeline.py",
    )


def run_pares_pipeline():
    _run_corpus_pipeline(
        source_label="PARES",
        source_url=PARES_HOME_URL,
        collect_dataset=collect_pares_dataset,
        institution_fields=PARES_INSTITUTION_FIELDS,
        summary_fields=PARES_SUMMARY_FIELDS,
        video_link_fields=PARES_VIDEO_LINK_FIELDS,
        internal_page_fields=PARES_INTERNAL_PAGE_FIELDS,
        output_files=PARES_OUTPUT_FILES,
        analysis_output_writer=write_pares_analysis_outputs,
        analysis_extra_sheets_builder=build_pares_analysis_extra_sheets,
        snapshot_builder=build_pares_snapshot_metadata,
        report_title="RELATORIO - PARES",
        institutions_sheet_title="PARES Institutions",
        generated_by="scripts/run_pares_pipeline.py",
    )


def run_ppa_pipeline():
    _run_corpus_pipeline(
        source_label="Portal Português de Arquivos",
        source_url=PPA_HOME_URL,
        collect_dataset=collect_ppa_dataset,
        institution_fields=PPA_INSTITUTION_FIELDS,
        summary_fields=PPA_SUMMARY_FIELDS,
        video_link_fields=PPA_VIDEO_LINK_FIELDS,
        internal_page_fields=PPA_INTERNAL_PAGE_FIELDS,
        output_files=PPA_OUTPUT_FILES,
        analysis_output_writer=write_ppa_analysis_outputs,
        analysis_extra_sheets_builder=build_ppa_analysis_extra_sheets,
        snapshot_builder=build_ppa_snapshot_metadata,
        report_title="RELATORIO - PORTAL PORTUGUES DE ARQUIVOS",
        institutions_sheet_title="PPA Institutions",
        generated_by="scripts/run_ppa_pipeline.py",
    )


def run_aapb_pipeline():
    _run_corpus_pipeline(
        source_label="American Archive of Public Broadcasting",
        source_url=AAPB_FAQ_URL,
        collect_dataset=collect_aapb_dataset,
        institution_fields=AAPB_INSTITUTION_FIELDS,
        summary_fields=AAPB_SUMMARY_FIELDS,
        video_link_fields=AAPB_VIDEO_LINK_FIELDS,
        internal_page_fields=AAPB_INTERNAL_PAGE_FIELDS,
        output_files=AAPB_OUTPUT_FILES,
        analysis_output_writer=write_aapb_analysis_outputs,
        analysis_extra_sheets_builder=build_aapb_analysis_extra_sheets,
        snapshot_builder=build_aapb_snapshot_metadata,
        report_title="RELATORIO - AMERICAN ARCHIVE OF PUBLIC BROADCASTING",
        institutions_sheet_title="AAPB Institutions",
        generated_by="scripts/run_aapb_pipeline.py",
    )


__all__ = [
    "run_aapb_pipeline",
    "run_archipop_pipeline",
    "run_pipeline",
    "run_ina_pipeline",
    "run_euscreen_pipeline",
    "run_european_film_gateway_pipeline",
    "run_europeana_pipeline",
    "run_pares_pipeline",
    "run_ppa_pipeline",
]
