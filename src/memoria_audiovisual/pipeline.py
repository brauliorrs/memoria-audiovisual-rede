import pandas as pd

from .ape import collect_ape_dataset
from .ape_exports import build_ape_analysis_extra_sheets
from .ape_exports import write_ape_analysis_outputs
from .config import APE_CONTENT_PDF_URL, OUTPUT_DIR
from .excel_export import save_basic_excel_report
from .output_files import APE_OUTPUT_FILES
from .reporting import build_report_payload, save_csv, save_json_report, save_txt_report
from .snapshot_metadata import write_ape_snapshot_metadata


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


def ensure_fields(rows, fieldnames):
    normalized = []
    for row in rows:
        normalized.append({field: row.get(field, "") for field in fieldnames})
    return normalized


def run_pipeline():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== ETAPA 1: Coletando instituicoes do Archives Portal Europe ===")
    ape_institutions, ape_rows_summary, ape_rows_video_links, ape_rows_internal_pages = collect_ape_dataset()
    ape_payload = build_report_payload(
        APE_CONTENT_PDF_URL,
        len(ape_institutions),
        ape_rows_summary,
        ape_rows_video_links,
    )
    summary_df = pd.DataFrame(ape_rows_summary)
    links_df = pd.DataFrame(ape_rows_video_links)
    analysis_frames = write_ape_analysis_outputs(
        OUTPUT_DIR,
        summary_df,
        links_df,
    )

    save_csv(
        OUTPUT_DIR / APE_OUTPUT_FILES["institutions"],
        ensure_fields(ape_institutions, APE_INSTITUTION_FIELDS),
        APE_INSTITUTION_FIELDS,
    )
    save_csv(
        OUTPUT_DIR / APE_OUTPUT_FILES["summary"],
        ensure_fields(ape_rows_summary, APE_SUMMARY_FIELDS),
        APE_SUMMARY_FIELDS,
    )
    save_csv(
        OUTPUT_DIR / APE_OUTPUT_FILES["video_links"],
        ensure_fields(ape_rows_video_links, APE_VIDEO_LINK_FIELDS),
        APE_VIDEO_LINK_FIELDS,
    )
    save_csv(
        OUTPUT_DIR / APE_OUTPUT_FILES["internal_pages"],
        ensure_fields(ape_rows_internal_pages, APE_INTERNAL_PAGE_FIELDS),
        APE_INTERNAL_PAGE_FIELDS,
    )
    save_json_report(OUTPUT_DIR / APE_OUTPUT_FILES["report_json"], ape_payload)
    save_txt_report(
        OUTPUT_DIR / APE_OUTPUT_FILES["report_txt"],
        ape_payload,
        ape_rows_summary,
        report_title="RELATORIO - ARCHIVES PORTAL EUROPE",
    )
    save_basic_excel_report(
        OUTPUT_DIR / APE_OUTPUT_FILES["report_xlsx"],
        ape_payload,
        ape_rows_summary,
        ape_rows_video_links,
        ape_rows_internal_pages,
        extra_sheets=[
            {
                "title": "APE Institutions",
                "rows": ensure_fields(ape_institutions, APE_INSTITUTION_FIELDS),
                "fieldnames": APE_INSTITUTION_FIELDS,
            },
            *build_ape_analysis_extra_sheets(analysis_frames),
        ],
    )
    write_ape_snapshot_metadata(
        OUTPUT_DIR,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by="scripts/run_pipeline.py",
    )

    print("\nArquivos gerados:")
    for filename in APE_OUTPUT_FILES.values():
        print(f" - {OUTPUT_DIR / filename}")
