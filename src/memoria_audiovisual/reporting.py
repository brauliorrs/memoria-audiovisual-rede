import csv
import json
from collections import Counter


def save_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_report_payload(source_url, total_institutions, rows_summary, rows_video_links):
    summary_counter = Counter(row["status"] for row in rows_summary)
    integrity_counter = Counter(row["integrity_status"] for row in rows_summary)
    platform_counter = Counter(row["platform"] for row in rows_video_links)
    domain_counter = Counter(row["partner_domain"] for row in rows_summary)

    ok_count = sum(1 for row in rows_summary if row["status"] == "ok")
    with_video = sum(1 for row in rows_summary if int(row["video_links_found_total"]) > 0)
    with_embeds = sum(1 for row in rows_summary if int(row["embedded_video_signals_total"]) > 0)
    ranking = sorted(
        rows_summary,
        key=lambda row: (
            int(row["video_links_found_total"]),
            int(row["embedded_video_signals_total"]),
        ),
        reverse=True,
    )

    return {
        "source": source_url,
        "total_institutions": total_institutions,
        "ok_count": ok_count,
        "with_video_count": with_video,
        "with_embeds_count": with_embeds,
        "status_summary": dict(summary_counter.most_common()),
        "integrity_summary": dict(integrity_counter.most_common()),
        "platform_summary": dict(platform_counter.most_common()),
        "top_domains": domain_counter.most_common(20),
        "top_institutions": ranking[:20],
    }


def save_json_report(path, payload):
    with path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False, indent=2)


def save_txt_report(path, payload, rows_summary):
    with path.open("w", encoding="utf-8") as file_handle:
        file_handle.write("RELATORIO - IASA NATIONAL ARCHIVES\n")
        file_handle.write("=" * 60 + "\n\n")
        file_handle.write(f"Fonte: {payload['source']}\n")
        file_handle.write(f"Total de instituicoes analisadas: {payload['total_institutions']}\n")
        file_handle.write(f"Instituicoes com acesso OK: {payload['ok_count']}\n")
        file_handle.write(f"Instituicoes com ao menos 1 link de video/plataforma: {payload['with_video_count']}\n")
        file_handle.write(f"Instituicoes com sinais de midia embutida: {payload['with_embeds_count']}\n\n")

        file_handle.write("Status dos sites parceiros:\n")
        for status, count in payload["status_summary"].items():
            file_handle.write(f"  - {status}: {count}\n")
        file_handle.write("\n")

        file_handle.write("Integridade dos links institucionais:\n")
        for status, count in payload["integrity_summary"].items():
            file_handle.write(f"  - {status}: {count}\n")
        file_handle.write("\n")

        file_handle.write("Plataformas detectadas:\n")
        for platform, count in payload["platform_summary"].items():
            file_handle.write(f"  - {platform}: {count}\n")
        file_handle.write("\n")

        file_handle.write("Dominios parceiros mais frequentes:\n")
        for domain, count in payload["top_domains"]:
            file_handle.write(f"  - {domain}: {count}\n")
        file_handle.write("\n")

        file_handle.write("Top 20 instituicoes com mais links de video detectados:\n")
        for row in payload["top_institutions"]:
            file_handle.write(
                f"  - {row['institution']} | links_video={row['video_links_found_total']} | "
                f"embeds={row['embedded_video_signals_total']} | status={row['status']} | "
                f"prioridade={row['priority_review']} | url={row['final_url']}\n"
            )
        file_handle.write("\n")

        suspeitos = [row for row in rows_summary if row["integrity_status"] == "suspeito"]
        if suspeitos:
            file_handle.write("Instituicoes suspeitas (respondem, mas parecem paginas genericas):\n")
            for row in suspeitos:
                file_handle.write(
                    f"  - {row['institution']} | url={row['final_url']} | aviso={row['warning']}\n"
                )
            file_handle.write("\n")

        file_handle.write("Instituicoes com erro ou restricao:\n")
        for row in rows_summary:
            if row["status"] in {"erro", "restrito", "http_error"}:
                file_handle.write(
                    f"  - {row['institution']} | status={row['status']} | http={row['http_code']} | "
                    f"url={row['partner_site']} | erro={row['error']}\n"
                )
