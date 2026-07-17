import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.output_files import ECPAD_OUTPUT_FILES


OUTPUT_DIR = ROOT_DIR / "data" / "output"


def load_csv_if_exists(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path, low_memory=False)


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
        "access_surface_summary",
        "access_regime_summary",
        "snapshot_metadata",
        "timeline_corpus",
        "timeline_institutions",
        "extinction_signals",
    ]
    missing_files = [
        ECPAD_OUTPUT_FILES[key]
        for key in required_keys
        if not (OUTPUT_DIR / ECPAD_OUTPUT_FILES[key]).exists()
    ]

    summary_df = load_csv_if_exists(ECPAD_OUTPUT_FILES["summary"])
    links_df = load_csv_if_exists(ECPAD_OUTPUT_FILES["video_links"])
    catalog_df = load_csv_if_exists(ECPAD_OUTPUT_FILES["analytic_video_catalog"])
    summary_df = summary_df if summary_df is not None else pd.DataFrame()
    links_df = links_df if links_df is not None else pd.DataFrame()
    catalog_df = catalog_df if catalog_df is not None else pd.DataFrame()

    print("Validação do corpus ECPAD")
    print(f"- instituições na base: {len(summary_df)}")
    print(f"- registros de vídeo materializados: {len(links_df)}")
    print(f"- registros no catálogo analítico: {len(catalog_df)}")

    if missing_files:
        print("- arquivos ausentes:")
        for filename in missing_files:
            print(f"  - {filename}")
    else:
        print("- todos os arquivos esperados do ECPAD foram encontrados")

    if summary_df.empty or links_df.empty or catalog_df.empty:
        print("- corpus ECPAD vazio ou sem catálogo analítico")
        return 1
    if "platform" not in links_df.columns or not links_df["platform"].eq("ECPAD Archives").any():
        print("- nenhum registro foi atribuído à plataforma ECPAD Archives")
        return 1
    if "access_surface" not in catalog_df.columns:
        print("- catálogo analítico sem campo de modalidade de acesso")
        return 1

    public_count = int((catalog_df["access_surface"].astype(str) == "Arquivo audiovisual institucional").sum())
    restricted_count = int(
        (
            catalog_df["access_surface"].astype(str)
            == "Metadados audiovisuais públicos com mídia local/autorizada"
        ).sum()
    )
    print(f"- vídeos com visual online: {public_count}")
    print(f"- vídeos sem visual online: {restricted_count}")
    if public_count <= 0 or restricted_count <= 0:
        print("- a distinção público/restrito do ECPAD não foi materializada")
        return 1

    snapshot_metadata = load_json_if_exists(ECPAD_OUTPUT_FILES["snapshot_metadata"])
    if snapshot_metadata:
        print("- metadados da rodada:")
        print(f"  - fonte ECPAD: {snapshot_metadata.get('source_url', '-')}")
        print(f"  - chave de observação: {snapshot_metadata.get('observation_key', '-')}")
    else:
        print(f"- arquivo de metadados ausente: {ECPAD_OUTPUT_FILES['snapshot_metadata']}")
        return 1

    return 1 if missing_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
