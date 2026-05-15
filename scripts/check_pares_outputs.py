import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.output_files import PARES_OUTPUT_FILES


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
        PARES_OUTPUT_FILES[key]
        for key in required_keys
        if not (OUTPUT_DIR / PARES_OUTPUT_FILES[key]).exists()
    ]

    summary_df = load_csv_if_exists(PARES_OUTPUT_FILES["summary"])
    if summary_df is None:
        print("Não foi encontrado o arquivo principal do PARES:")
        print(f"- {PARES_OUTPUT_FILES['summary']}")
        return 1

    if summary_df.empty:
        print("O arquivo principal do PARES foi encontrado, mas está vazio:")
        print(f"- {PARES_OUTPUT_FILES['summary']}")
        return 1

    links_df = load_csv_if_exists(PARES_OUTPUT_FILES["video_links"])
    analytic_summary_df = load_csv_if_exists(PARES_OUTPUT_FILES["analytic_summary"])
    analytic_video_catalog_df = load_csv_if_exists(PARES_OUTPUT_FILES["analytic_video_catalog"])
    visibility_summary_df = load_csv_if_exists(PARES_OUTPUT_FILES["visibility_summary"])
    theme_summary_df = load_csv_if_exists(PARES_OUTPUT_FILES["theme_summary"])

    if links_df is None:
        links_df = pd.DataFrame()
    if analytic_summary_df is None:
        analytic_summary_df = pd.DataFrame()
    if analytic_video_catalog_df is None:
        analytic_video_catalog_df = pd.DataFrame()
    if visibility_summary_df is None:
        visibility_summary_df = pd.DataFrame()
    if theme_summary_df is None:
        theme_summary_df = pd.DataFrame()

    print("Validação do corpus PARES")
    print(f"- instituições na base: {len(summary_df)}")
    print(f"- links/registros audiovisuais detectados: {len(links_df)}")
    print(f"- instituições na camada analítica: {len(analytic_summary_df)}")
    print(f"- registros no catálogo analítico: {len(analytic_video_catalog_df)}")
    print(f"- situações de visibilidade: {len(visibility_summary_df)}")
    print(f"- temas analíticos: {len(theme_summary_df)}")

    if missing_files:
        print("- arquivos ausentes:")
        for filename in missing_files:
            print(f"  - {filename}")
    else:
        print("- todos os arquivos esperados do PARES foram encontrados")

    snapshot_metadata = load_json_if_exists(PARES_OUTPUT_FILES["snapshot_metadata"])
    if snapshot_metadata:
        print("- metadados da rodada:")
        print(f"  - fonte PARES: {snapshot_metadata.get('source_url', '-')}")
        print(f"  - chave de observação: {snapshot_metadata.get('observation_key', '-')}")
        print(f"  - camada analítica atualizada em {snapshot_metadata.get('analytic_outputs_last_modified_at', '-')}")
        print(f"  - metadados gerados em {snapshot_metadata.get('generated_at', '-')}")
    else:
        print(f"- arquivo de metadados ausente: {PARES_OUTPUT_FILES['snapshot_metadata']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
