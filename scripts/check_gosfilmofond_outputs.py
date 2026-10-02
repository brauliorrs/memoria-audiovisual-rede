import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.output_files import GOSFILMOFOND_OUTPUT_FILES


MIN_EXPECTED_PUBLIC_RECORDS = 50_000
MIN_EXPECTED_ENUMERATION_PAGES = 500


def load_csv(key):
    path = OUTPUT_DIR / GOSFILMOFOND_OUTPUT_FILES[key]
    return pd.read_csv(path) if path.exists() else None


def main():
    required = [
        "institutions",
        "summary",
        "video_links",
        "internal_pages",
        "analytic_summary",
        "analytic_video_catalog",
        "visibility_summary",
        "theme_summary",
        "snapshot_metadata",
        "timeline_corpus",
        "timeline_institutions",
        "extinction_signals",
    ]
    missing = [
        GOSFILMOFOND_OUTPUT_FILES[key]
        for key in required
        if not (OUTPUT_DIR / GOSFILMOFOND_OUTPUT_FILES[key]).exists()
    ]
    if missing:
        print("Gosfilmofond: arquivos esperados ausentes:")
        for name in missing:
            print(f"- {name}")
        return 1

    summary = load_csv("summary")
    links = load_csv("video_links")
    internal = load_csv("internal_pages")
    if summary is None or summary.empty:
        print("Gosfilmofond: resumo ausente ou vazio.")
        return 1
    if links is None or links.empty:
        print("Gosfilmofond: catálogo materializado vazio.")
        return 1
    if internal is None or internal.empty:
        print("Gosfilmofond: trilha de enumeração ausente.")
        return 1

    integrity = str(summary.iloc[0].get("integrity_status", ""))
    if integrity != "integro":
        print(f"Gosfilmofond: integridade da rodada = {integrity!r}; promoção bloqueada.")
        return 1

    if len(links) < MIN_EXPECTED_PUBLIC_RECORDS:
        print(
            "Gosfilmofond: enumeração pequena demais para o catálogo público "
            f"observado ({len(links)} < {MIN_EXPECTED_PUBLIC_RECORDS})."
        )
        return 1

    urls = links["video_link"].astype(str)
    if urls.nunique() != len(links):
        print("Gosfilmofond: permalinks duplicados no catálogo materializado.")
        return 1
    if not urls.str.match(r"^https://gosfilmofond\.ru/films/[^/]+/$").all():
        print("Gosfilmofond: há URLs fora do contrato de ficha pública /films/<key>/.")
        return 1

    page_rows = internal[
        internal["internal_page"].astype(str).str.contains(
            r"admin-ajax\.php#page=",
            regex=True,
        )
    ]
    if len(page_rows) < MIN_EXPECTED_ENUMERATION_PAGES:
        print(
            "Gosfilmofond: poucas páginas AJAX foram materializadas "
            f"({len(page_rows)} < {MIN_EXPECTED_ENUMERATION_PAGES})."
        )
        return 1
    if (page_rows["status"].astype(str) != "ok").any():
        print("Gosfilmofond: página AJAX com estado diferente de ok.")
        return 1

    metadata_path = OUTPUT_DIR / GOSFILMOFOND_OUTPUT_FILES["snapshot_metadata"]
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if payload.get("dataset") != "gosfilmofond":
        print("Gosfilmofond: dataset incorreto no snapshot metadata.")
        return 1
    counts = payload.get("counts", {})
    if int(counts.get("video_links_total", -1)) != len(links):
        print("Gosfilmofond: snapshot e catálogo divergem na contagem de registros.")
        return 1

    print("Validação do corpus staged Gosfilmofond")
    print(f"- registros públicos únicos: {len(links)}")
    print(f"- páginas AJAX enumeradas: {len(page_rows)}")
    print("- integridade: integro")
    print("- todos os arquivos esperados foram encontrados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
