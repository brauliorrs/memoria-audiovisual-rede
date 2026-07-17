import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.output_files import CINEMEMOIRE_OUTPUT_FILES


OUTPUT_DIR = ROOT_DIR / "data" / "output"


def load_csv_if_exists(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


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
        CINEMEMOIRE_OUTPUT_FILES[key]
        for key in required_keys
        if not (OUTPUT_DIR / CINEMEMOIRE_OUTPUT_FILES[key]).exists()
    ]

    summary_df = load_csv_if_exists(CINEMEMOIRE_OUTPUT_FILES["summary"])
    if summary_df is None or summary_df.empty:
        print("O arquivo principal do Cinémémoire está ausente ou vazio.")
        return 1

    links_df = load_csv_if_exists(CINEMEMOIRE_OUTPUT_FILES["video_links"])
    analytic_video_catalog_df = load_csv_if_exists(CINEMEMOIRE_OUTPUT_FILES["analytic_video_catalog"])
    links_df = links_df if links_df is not None else pd.DataFrame()
    analytic_video_catalog_df = analytic_video_catalog_df if analytic_video_catalog_df is not None else pd.DataFrame()

    print("Validação do corpus Cinémémoire")
    print(f"- instituições na base: {len(summary_df)}")
    print(f"- registros audiovisuais materializados: {len(links_df)}")
    print(f"- registros no catálogo analítico: {len(analytic_video_catalog_df)}")

    if missing_files:
        print("- arquivos ausentes:")
        for filename in missing_files:
            print(f"  - {filename}")
    else:
        print("- todos os arquivos esperados do Cinémémoire foram encontrados")

    snapshot_metadata = load_json_if_exists(CINEMEMOIRE_OUTPUT_FILES["snapshot_metadata"])
    if snapshot_metadata:
        print("- metadados da rodada:")
        print(f"  - fonte Cinémémoire: {snapshot_metadata.get('source_url', '-')}")
        print(f"  - chave de observação: {snapshot_metadata.get('observation_key', '-')}")
    else:
        print(f"- arquivo de metadados ausente: {CINEMEMOIRE_OUTPUT_FILES['snapshot_metadata']}")

    if links_df.empty:
        print("- a rota Cinémémoire respondeu, mas nenhum vídeo público foi materializado")
        return 1
    if "platform" not in links_df.columns or not links_df["platform"].eq("Cinémémoire").any():
        print("- nenhum registro foi atribuído à plataforma Cinémémoire")
        return 1

    return 1 if missing_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
