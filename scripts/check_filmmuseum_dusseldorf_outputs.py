import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.filmmuseum_dusseldorf import DKULT_DUSSELDORF_MIN_AV_TOTAL
from memoria_audiovisual.output_files import FILMMUSEUM_DUSSELDORF_OUTPUT_FILES


OUTPUT_DIR = ROOT_DIR / "data" / "output"
RESTRICTED_SURFACE = "Metadados audiovisuais públicos com mídia local/autorizada"


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
        FILMMUSEUM_DUSSELDORF_OUTPUT_FILES[key]
        for key in required_keys
        if not (OUTPUT_DIR / FILMMUSEUM_DUSSELDORF_OUTPUT_FILES[key]).exists()
    ]
    summary_df = load_csv_if_exists(FILMMUSEUM_DUSSELDORF_OUTPUT_FILES["summary"])
    links_df = load_csv_if_exists(FILMMUSEUM_DUSSELDORF_OUTPUT_FILES["video_links"])
    catalog_df = load_csv_if_exists(FILMMUSEUM_DUSSELDORF_OUTPUT_FILES["analytic_video_catalog"])
    links_df = links_df if links_df is not None else pd.DataFrame()
    catalog_df = catalog_df if catalog_df is not None else pd.DataFrame()

    print("Validação do corpus Filmmuseum Düsseldorf / d:kult online")
    print(f"- instituições na base: {0 if summary_df is None else len(summary_df)}")
    print(f"- metadados audiovisuais d:kult: {len(links_df)}")
    print(f"- registros no catálogo analítico: {len(catalog_df)}")

    if missing_files:
        print("- arquivos ausentes:")
        for filename in missing_files:
            print(f"  - {filename}")

    snapshot_metadata = load_json_if_exists(FILMMUSEUM_DUSSELDORF_OUTPUT_FILES["snapshot_metadata"])
    if snapshot_metadata:
        print("- metadados da rodada:")
        print(f"  - fonte d:kult: {snapshot_metadata.get('source_url', '-')}")
        print(f"  - chave de observação: {snapshot_metadata.get('observation_key', '-')}")
    else:
        print(f"- arquivo de metadados ausente: {FILMMUSEUM_DUSSELDORF_OUTPUT_FILES['snapshot_metadata']}")

    if summary_df is None or summary_df.empty:
        print("- resumo principal ausente ou vazio")
        return 1
    if len(links_df) < DKULT_DUSSELDORF_MIN_AV_TOTAL:
        print(f"- total abaixo do piso metodológico: {len(links_df)} de {DKULT_DUSSELDORF_MIN_AV_TOTAL}")
        return 1
    if not links_df["video_link"].astype(str).str.contains("emuseum.duesseldorf.de/objects/", regex=False).all():
        print("- há registros sem URL pública do objeto d:kult")
        return 1
    if links_df["video_link"].duplicated().any():
        print("- há objetos d:kult duplicados; o corpus deve ser deduplicado por URL")
        return 1
    if "platform" not in links_df.columns or not links_df["platform"].astype(str).eq("d:kult online").all():
        print("- plataforma esperada d:kult online não foi aplicada a todos os registros")
        return 1
    if not catalog_df.empty and "access_surface" in catalog_df.columns:
        if not catalog_df["access_surface"].astype(str).eq(RESTRICTED_SURFACE).all():
            print("- a superfície de acesso restrito/local não foi aplicada a todos os registros analíticos")
            return 1
    if missing_files:
        return 1

    print("- todos os arquivos esperados do Filmmuseum Düsseldorf / d:kult online foram encontrados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
