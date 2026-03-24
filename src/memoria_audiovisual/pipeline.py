from .config import OUTPUT_DIR, OUTPUT_PREFIX, START_URL
from .crawler import collect_dataset
from .excel_export import save_excel_report
from .reporting import build_report_payload, save_csv, save_json_report, save_txt_report


def run_pipeline():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== ETAPA 1: Coletando instituicoes da IASA ===")
    entries, rows_summary, rows_video_links, rows_internal_pages = collect_dataset()
    payload = build_report_payload(START_URL, len(entries), rows_summary, rows_video_links)

    save_csv(
        OUTPUT_DIR / f"{OUTPUT_PREFIX}_resumo_instituicoes.csv",
        rows_summary,
        [
            "institution",
            "slug",
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
        ["institution", "slug", "partner_site", "platform", "video_link"],
    )
    save_csv(
        OUTPUT_DIR / f"{OUTPUT_PREFIX}_paginas_internas.csv",
        rows_internal_pages,
        [
            "institution",
            "slug",
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
    save_json_report(OUTPUT_DIR / f"{OUTPUT_PREFIX}_relatorio.json", payload)
    save_txt_report(OUTPUT_DIR / f"{OUTPUT_PREFIX}_relatorio.txt", payload, rows_summary)
    save_excel_report(
        OUTPUT_DIR / f"{OUTPUT_PREFIX}_relatorio.xlsx",
        payload,
        rows_summary,
        rows_video_links,
        rows_internal_pages,
    )

    print("\nArquivos gerados:")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_resumo_instituicoes.csv'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_links_video.csv'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_paginas_internas.csv'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_relatorio.json'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_relatorio.txt'}")
    print(f" - {OUTPUT_DIR / f'{OUTPUT_PREFIX}_relatorio.xlsx'}")
