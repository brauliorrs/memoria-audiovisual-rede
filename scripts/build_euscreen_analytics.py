import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.euscreen_exports import write_euscreen_analysis_outputs
from memoria_audiovisual.output_files import EUSCREEN_OUTPUT_FILES
from memoria_audiovisual.snapshot_metadata import (
    build_euscreen_snapshot_metadata,
    save_snapshot_metadata_payload,
)
from memoria_audiovisual.timeline import write_timeline_outputs


def load_required_csv(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    return pd.read_csv(path)


def main():
    summary_df = load_required_csv(EUSCREEN_OUTPUT_FILES["summary"])
    links_df = load_required_csv(EUSCREEN_OUTPUT_FILES["video_links"])

    if summary_df.empty:
        raise ValueError(
            f"O arquivo {EUSCREEN_OUTPUT_FILES['summary']} está vazio e não permite reconstruir a camada analítica."
        )

    analysis_frames = write_euscreen_analysis_outputs(OUTPUT_DIR, summary_df, links_df)
    snapshot_payload = build_euscreen_snapshot_metadata(
        OUTPUT_DIR,
        summary_df=summary_df,
        links_df=links_df,
        analysis_frames=analysis_frames,
        generated_by="scripts/build_euscreen_analytics.py",
    )
    write_timeline_outputs(
        OUTPUT_DIR,
        dataset=snapshot_payload["dataset"],
        output_files=EUSCREEN_OUTPUT_FILES,
        snapshot_metadata=snapshot_payload,
        summary_df=summary_df,
        analysis_frames=analysis_frames,
    )
    save_snapshot_metadata_payload(
        OUTPUT_DIR,
        output_files=EUSCREEN_OUTPUT_FILES,
        payload=snapshot_payload,
    )

    print("Saídas analíticas do EUscreen atualizadas a partir dos CSVs brutos:")
    for key, dataframe in analysis_frames.items():
        print(f"- {EUSCREEN_OUTPUT_FILES[key]} | linhas={len(dataframe)}")


if __name__ == "__main__":
    raise SystemExit(main())
