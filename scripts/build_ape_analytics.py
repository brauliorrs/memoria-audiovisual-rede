import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.ape_exports import write_ape_analysis_outputs
from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.output_files import APE_OUTPUT_FILES
from memoria_audiovisual.snapshot_metadata import write_ape_snapshot_metadata


def load_required_csv(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return pd.read_csv(path)


def main():
    summary_df = load_required_csv(APE_OUTPUT_FILES["summary"])
    links_df = load_required_csv(APE_OUTPUT_FILES["video_links"])

    if summary_df.empty:
        raise ValueError(
            f"O arquivo {APE_OUTPUT_FILES['summary']} está vazio e não permite reconstruir a camada analítica."
        )

    analysis_frames = write_ape_analysis_outputs(OUTPUT_DIR, summary_df, links_df)
    write_ape_snapshot_metadata(
        OUTPUT_DIR,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by="scripts/build_ape_analytics.py",
    )

    print("Saídas analíticas do APE atualizadas a partir dos CSVs brutos:")
    for key, dataframe in analysis_frames.items():
        print(f"- {APE_OUTPUT_FILES[key]} | linhas={len(dataframe)}")


if __name__ == "__main__":
    raise SystemExit(main())
