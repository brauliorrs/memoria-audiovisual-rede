from .ape import collect_ape_dataset
from .config import (
    APE_CONTENT_PDF_URL,
    APE_OUTPUT_PREFIX,
    CCAAA_MEMBERS_URL,
    CCAAA_OUTPUT_PREFIX,
    OUTPUT_DIR,
    OUTPUT_PREFIX,
    START_URL,
)
from .ccaaa import collect_ccaaa_dataset, collect_ccaaa_members
from .crawler import collect_dataset
from .excel_export import save_basic_excel_report, save_excel_report
from .reporting import build_report_payload, save_csv, save_json_report, save_txt_report


def run_pipeline():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== ETAPA 1: Coletando instituicoes do Archives Portal Europe ===")
    ape_institutions, ape_rows_summary, ape_rows_video_links, ape_rows_internal_pages = collect_ape_dataset()
    print("=== ETAPA 2: Coletando instituicoes da IASA ===")
    entries, rows_summary, rows_video_links, rows_internal_pages = collect_dataset()
    print("=== ETAPA 3: Coletando membros da CCAAA ===")
    ccaaa_members = collect_ccaaa_members()
    print("=== ETAPA 4: Verificando sites da CCAAA ===")
    ccaaa_entries, ccaaa_rows_summary, ccaaa_rows_video_links, ccaaa_rows_internal_pages = (
        collect_ccaaa_dataset(ccaaa_members)
    )
    ape_payload = build_report_payload(
        APE_CONTENT_PDF_URL,
        len(ape_institutions),
        ape_rows_summary,
        ape_rows_video_links,
    )
    payload = build_report_payload(START_URL, len(entries), rows_summary, rows_video_links)
    ccaaa_payload = build_report_payload(
        CCAAA_MEMBERS_URL,
        len(ccaaa_entries),
        ccaaa_rows_summary,
        ccaaa_rows_video_links,
    )

    save_csv(
        OUTPUT_DIR / f"{APE_OUTPUT_PREFIX}_instituicoes.csv",
        ape_institutions,
        [
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
        ],
    )
    save_csv(
        OUTPUT_DIR / f"{APE_OUTPUT_PREFIX}_resumo_instituicoes.csv",
        ape_rows_summary,
        [
            "institution",
            "slug",
            "country",
            "continent",
            "repository_code",
            "archive_type",
            "ape_detail_url",
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
        ],
    )
    save_csv(
        OUTPUT_DIR / f"{APE_OUTPUT_PREFIX}_links_video.csv",
        ape_rows_video_links,
        [
            "institution",
            "slug",
            "country",
            "continent",
            "repository_code",
            "archive_type",
            "ape_detail_url",
            "website_available",
            "partner_site",
            "platform",
            "video_link",
        ],
    )
    save_csv(
        OUTPUT_DIR / f"{APE_OUTPUT_PREFIX}_paginas_internas.csv",
        ape_rows_internal_pages,
        [
            "institution",
            "slug",
            "country",
            "continent",
            "repository_code",
            "archive_type",
            "ape_detail_url",
            "website_available",
            "partner_site",
            "internal_page",
            "status",
            "http_code",
            "video_links_found",
            "embedded_signals",
            "warning",
            "error",
        ],
    )
    save_csv(
        OUTPUT_DIR / f"{OUTPUT_PREFIX}_resumo_instituicoes.csv",
        rows_summary,
        [
            "institution",
            "slug",
            "country",
            "continent",
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
        ],
    )
    save_csv(
        OUTPUT_DIR / f"{OUTPUT_PREFIX}_links_video.csv",
        rows_video_links,
        ["institution", "slug", "country", "continent", "partner_site", "platform", "video_link"],
    )
    save_csv(
        OUTPUT_DIR / f"{OUTPUT_PREFIX}_paginas_internas.csv",
        rows_internal_pages,
        [
            "institution",
            "slug",
            "country",
            "continent",
            "partner_site",
            "internal_page",
            "status",
            "http_code",
            "video_links_found",
            "embedded_signals",
            "warning",
            "error",
        ],
    )
    save_csv(
        OUTPUT_DIR / "ccaaa_membros.csv",
        ccaaa_members,
        ["organization", "abbreviation", "role", "website", "domain", "description", "source"],
    )
    save_csv(
        OUTPUT_DIR / f"{CCAAA_OUTPUT_PREFIX}_resumo_sites.csv",
        ccaaa_rows_summary,
        [
            "institution",
            "slug",
            "abbreviation",
            "role",
            "country",
            "continent",
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
            "member_source",
            "error",
        ],
    )
    save_csv(
        OUTPUT_DIR / f"{CCAAA_OUTPUT_PREFIX}_links_video.csv",
        ccaaa_rows_video_links,
        [
            "institution",
            "slug",
            "abbreviation",
            "role",
            "country",
            "continent",
            "partner_site",
            "platform",
            "video_link",
            "member_source",
        ],
    )
    save_csv(
        OUTPUT_DIR / f"{CCAAA_OUTPUT_PREFIX}_paginas_internas.csv",
        ccaaa_rows_internal_pages,
        [
            "institution",
            "slug",
            "abbreviation",
            "role",
            "country",
            "continent",
            "partner_site",
            "internal_page",
            "status",
            "http_code",
            "video_links_found",
            "embedded_signals",
            "warning",
            "member_source",
            "error",
        ],
    )
    save_json_report(OUTPUT_DIR / f"{APE_OUTPUT_PREFIX}_relatorio.json", ape_payload)
    save_json_report(OUTPUT_DIR / f"{OUTPUT_PREFIX}_relatorio.json", payload)
    save_json_report(OUTPUT_DIR / "ccaaa_membros.json", ccaaa_members)
    save_json_report(OUTPUT_DIR / f"{CCAAA_OUTPUT_PREFIX}_relatorio.json", ccaaa_payload)
    save_txt_report(
        OUTPUT_DIR / f"{APE_OUTPUT_PREFIX}_relatorio.txt",
        ape_payload,
        ape_rows_summary,
        report_title="RELATORIO - ARCHIVES PORTAL EUROPE",
    )
    save_txt_report(OUTPUT_DIR / f"{OUTPUT_PREFIX}_relatorio.txt", payload, rows_summary)
    save_txt_report(
        OUTPUT_DIR / f"{CCAAA_OUTPUT_PREFIX}_relatorio.txt",
        ccaaa_payload,
        ccaaa_rows_summary,
        report_title="RELATORIO - CCAAA MEMBER SITES",
    )
    save_basic_excel_report(
        OUTPUT_DIR / f"{APE_OUTPUT_PREFIX}_relatorio.xlsx",
        ape_payload,
        ape_rows_summary,
        ape_rows_video_links,
        ape_rows_internal_pages,
        extra_sheets=[
            {
                "title": "APE Institutions",
                "rows": ape_institutions,
                "fieldnames": [
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
                ],
            }
        ],
    )
    save_excel_report(
        OUTPUT_DIR / f"{OUTPUT_PREFIX}_relatorio.xlsx",
        payload,
        rows_summary,
        rows_video_links,
        rows_internal_pages,
        ccaaa_members,
        ccaaa_rows_summary,
        ccaaa_rows_video_links,
        ccaaa_rows_internal_pages,
    )

    print("\nArquivos gerados:")
    print(f" - {OUTPUT_DIR / f'{APE_OUTPUT_PREFIX}_instituicoes.csv'}")
    print(f" - {OUTPUT_DIR / f'{APE_OUTPUT_PREFIX}_resumo_instituicoes.csv'}")
    print(f" - {OUTPUT_DIR / f'{APE_OUTPUT_PREFIX}_links_video.csv'}")
    print(f" - {OUTPUT_DIR / f'{APE_OUTPUT_PREFIX}_paginas_internas.csv'}")
    print(f" - {OUTPUT_DIR / f'{APE_OUTPUT_PREFIX}_relatorio.json'}")
    print(f" - {OUTPUT_DIR / f'{APE_OUTPUT_PREFIX}_relatorio.txt'}")
    print(f" - {OUTPUT_DIR / f'{APE_OUTPUT_PREFIX}_relatorio.xlsx'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_resumo_instituicoes.csv'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_links_video.csv'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_paginas_internas.csv'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_relatorio.json'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_relatorio.txt'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_relatorio.xlsx'}")
    print(f" - {OUTPUT_DIR / 'ccaaa_membros.csv'}")
    print(f" - {OUTPUT_DIR / 'ccaaa_membros.json'}")
    print(f" - {OUTPUT_DIR / f'{CCAAA_OUTPUT_PREFIX}_resumo_sites.csv'}")
    print(f" - {OUTPUT_DIR / f'{CCAAA_OUTPUT_PREFIX}_links_video.csv'}")
    print(f" - {OUTPUT_DIR / f'{CCAAA_OUTPUT_PREFIX}_paginas_internas.csv'}")
    print(f" - {OUTPUT_DIR / f'{CCAAA_OUTPUT_PREFIX}_relatorio.json'}")
    print(f" - {OUTPUT_DIR / f'{CCAAA_OUTPUT_PREFIX}_relatorio.txt'}")
