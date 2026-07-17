from pathlib import Path
import json
import sys

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.output_files import CCMA_OUTPUT_FILES


def load_csv_if_exists(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_json_if_exists(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    expected_keys = [
        "institutions",
        "summary",
        "video_links",
        "internal_pages",
        "analytic_summary",
        "analytic_video_catalog",
        "theme_summary",
        "snapshot_metadata",
        "report_json",
        "report_txt",
        "report_xlsx",
    ]
    missing = [CCMA_OUTPUT_FILES[key] for key in expected_keys if not (OUTPUT_DIR / CCMA_OUTPUT_FILES[key]).exists()]
    summary_df = load_csv_if_exists(CCMA_OUTPUT_FILES["summary"])
    links_df = load_csv_if_exists(CCMA_OUTPUT_FILES["video_links"])
    catalog_df = load_csv_if_exists(CCMA_OUTPUT_FILES["analytic_video_catalog"])

    print("Validação do corpus CCMA/3Cat")
    print(f"- instituições na base: {len(load_csv_if_exists(CCMA_OUTPUT_FILES['institutions']))}")
    print(f"- registros audiovisuais materializados: {len(links_df)}")
    print(f"- registros no catálogo analítico: {len(catalog_df)}")
    if missing:
        print("- arquivos ausentes:")
        for filename in missing:
            print(f"  - {filename}")
    else:
        print("- todos os arquivos esperados do CCMA/3Cat foram encontrados")

    snapshot_metadata = load_json_if_exists(CCMA_OUTPUT_FILES["snapshot_metadata"])
    if snapshot_metadata:
        print("- metadados da rodada:")
        print(f"  - fonte CCMA/3Cat: {snapshot_metadata.get('source_url', '-')}")
        print(f"  - chave de observação: {snapshot_metadata.get('observation_key', '-')}")

    if summary_df.empty or links_df.empty or catalog_df.empty:
        raise SystemExit("O corpus CCMA/3Cat não materializou saídas audiovisuais suficientes.")
    if "platform" not in links_df.columns or not links_df["platform"].eq("3Cat").any():
        raise SystemExit("Nenhum registro foi atribuído à plataforma 3Cat.")


if __name__ == "__main__":
    main()
