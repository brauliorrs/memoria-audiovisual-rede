import sys
import json
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.dashboard_data import (
    DASHBOARD_SOURCE_KEYS,
    build_dashboard_base_data,
    build_dashboard_overview_data,
)
from memoria_audiovisual.output_files import APE_OUTPUT_FILES


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


def load_dashboard_sources():
    return {
        key: load_csv_if_exists(APE_OUTPUT_FILES[key])
        for key in DASHBOARD_SOURCE_KEYS
    }


def main():
    sources = load_dashboard_sources()
    missing_files = [
        APE_OUTPUT_FILES[key]
        for key, dataframe in sources.items()
        if dataframe is None
    ]

    summary_df = sources["summary"]
    if summary_df is None:
        print("Não foi encontrado o arquivo principal do APE para o dashboard:")
        print(f"- {APE_OUTPUT_FILES['summary']}")
        return 1

    if summary_df.empty:
        print("O arquivo principal do APE foi encontrado, mas está vazio:")
        print(f"- {APE_OUTPUT_FILES['summary']}")
        return 1

    base_data = build_dashboard_base_data(
        catalog_df=sources["institutions"],
        summary_df=summary_df,
        links_df=sources["video_links"],
        internal_df=sources["internal_pages"],
        summary_analysis_source_df=sources["analytic_summary"],
        video_catalog_source_df=sources["analytic_video_catalog"],
    )
    overview_data = build_dashboard_overview_data(
        base_data,
        availability_groups_source_df=sources["availability_summary"],
        availability_reasons_source_df=sources["availability_reasons"],
        archive_type_counts_source_df=sources["archive_type_summary"],
        visibility_counts_source_df=sources["visibility_summary"],
        theme_counts_source_df=sources["theme_summary"],
        theme_country_counts_source_df=sources["theme_country"],
        theme_platform_counts_source_df=sources["theme_platform"],
        theme_archive_type_counts_source_df=sources["theme_archive_type"],
        visibility_archive_type_counts_source_df=sources["visibility_archive_type"],
    )

    print("Validação do dashboard do APE")
    print(f"- instituições na base: {len(base_data.summary_df)}")
    print(f"- slugs disponíveis: {len(base_data.available_slugs)}")
    print(f"- vídeos no catálogo: {len(base_data.video_catalog_df)}")
    print(f"- categorias de disponibilidade: {len(overview_data.availability_groups)}")
    print(f"- temas analíticos: {len(overview_data.theme_counts)}")
    print(f"- situações de visibilidade: {len(overview_data.visibility_counts)}")

    if missing_files:
        print("- arquivos ausentes, mas com fallback local disponível:")
        for filename in missing_files:
            print(f"  - {filename}")
    else:
        print("- todos os CSVs esperados para o dashboard foram encontrados")

    snapshot_metadata = load_json_if_exists(APE_OUTPUT_FILES["snapshot_metadata"])
    if snapshot_metadata:
        print("- metadados da rodada:")
        print(f"  - fonte APE com status de {snapshot_metadata.get('source_status_date', '-')}")
        print(f"  - camada analítica atualizada em {snapshot_metadata.get('analytic_outputs_last_modified_at', '-')}")
        print(f"  - metadados gerados em {snapshot_metadata.get('generated_at', '-')}")
    else:
        print(f"- arquivo de metadados ausente: {APE_OUTPUT_FILES['snapshot_metadata']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
