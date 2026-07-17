import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.fina import FINA_MIN_VIDEO_TOTAL
from memoria_audiovisual.output_files import FINA_OUTPUT_FILES


OUTPUT_DIR = ROOT_DIR / "data" / "output"


def load_csv_if_exists(filename):
    path = OUTPUT_DIR / filename
    return pd.read_csv(path) if path.exists() else None


def load_json_if_exists(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def main():
    required_keys = [
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
    missing_files = [
        FINA_OUTPUT_FILES[key]
        for key in required_keys
        if not (OUTPUT_DIR / FINA_OUTPUT_FILES[key]).exists()
    ]
    summary_df = load_csv_if_exists(FINA_OUTPUT_FILES["summary"])
    links_df = load_csv_if_exists(FINA_OUTPUT_FILES["video_links"])
    analytic_video_catalog_df = load_csv_if_exists(FINA_OUTPUT_FILES["analytic_video_catalog"])
    links_df = links_df if links_df is not None else pd.DataFrame()
    analytic_video_catalog_df = analytic_video_catalog_df if analytic_video_catalog_df is not None else pd.DataFrame()

    print("Validação do corpus FINA / Ninateka")
    print(f"- instituições na base: {0 if summary_df is None else len(summary_df)}")
    print(f"- vídeos públicos Ninateka: {len(links_df)}")
    print(f"- registros no catálogo analítico: {len(analytic_video_catalog_df)}")

    if missing_files:
        print("- arquivos ausentes:")
        for filename in missing_files:
            print(f"  - {filename}")

    snapshot_metadata = load_json_if_exists(FINA_OUTPUT_FILES["snapshot_metadata"])
    if snapshot_metadata:
        print("- metadados da rodada:")
        print(f"  - fonte Ninateka: {snapshot_metadata.get('source_url', '-')}")
        print(f"  - chave de observação: {snapshot_metadata.get('observation_key', '-')}")
    else:
        print(f"- arquivo de metadados ausente: {FINA_OUTPUT_FILES['snapshot_metadata']}")

    if summary_df is None or summary_df.empty:
        print("- resumo principal ausente ou vazio")
        return 1
    if len(links_df) < FINA_MIN_VIDEO_TOTAL:
        print(f"- total abaixo do piso metodológico: {len(links_df)} de {FINA_MIN_VIDEO_TOTAL}")
        return 1
    if links_df["video_link"].duplicated().any():
        print("- há vídeos duplicados; o corpus deve ser deduplicado por URL")
        return 1
    if not links_df["video_link"].astype(str).str.contains("ninateka.pl/", regex=False).all():
        print("- há registros sem URL pública Ninateka")
        return 1
    if "platform" not in links_df.columns or not links_df["platform"].astype(str).eq("Ninateka").all():
        print("- plataforma esperada Ninateka não foi aplicada a todos os registros")
        return 1
    if missing_files:
        return 1

    print("- todos os arquivos esperados da FINA / Ninateka foram encontrados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
