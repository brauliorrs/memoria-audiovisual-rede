import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.corpora import list_active_corpora
from memoria_audiovisual.europe_research import EUROPE_RESEARCH_QUEUE_FILENAME
from memoria_audiovisual.organism import ORGANISM_ACTIVE_CORPORA_FILENAME
from memoria_audiovisual.public_access_index import (
    PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME,
    PUBLIC_ACCESS_INDEX_FILENAME,
    PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME,
)


def main():
    required_paths = [
        ROOT_DIR / "requirements.txt",
        ROOT_DIR / ".streamlit" / "config.toml",
        ROOT_DIR / "app" / "streamlit_app.py",
        OUTPUT_DIR / ORGANISM_ACTIVE_CORPORA_FILENAME,
        OUTPUT_DIR / EUROPE_RESEARCH_QUEUE_FILENAME,
        OUTPUT_DIR / PUBLIC_ACCESS_INDEX_FILENAME,
        OUTPUT_DIR / PUBLIC_ACCESS_INDEX_BY_CORPUS_FILENAME,
        OUTPUT_DIR / PUBLIC_ACCESS_RESTRICTED_UNITS_FILENAME,
    ]

    for corpus_def in list_active_corpora(monthly_only=True):
        for filename in corpus_def["list_output_filenames"]():
            required_paths.append(OUTPUT_DIR / filename)

    missing_paths = [path for path in required_paths if not path.exists()]
    if missing_paths:
        print("Implantacao bloqueada: arquivos obrigatorios ausentes.")
        for path in missing_paths:
            print(f"- {path.relative_to(ROOT_DIR)}")
        return 1

    queue_df = pd.read_csv(OUTPUT_DIR / EUROPE_RESEARCH_QUEUE_FILENAME)
    if queue_df.empty:
        print("Implantacao bloqueada: fila europeia vazia.")
        return 1

    if "video_location_candidate_url" not in queue_df.columns:
        print("Implantacao bloqueada: fila europeia sem local inicial dos videos.")
        return 1

    snapshot_size = sum(path.stat().st_size for path in OUTPUT_DIR.glob("*") if path.is_file())
    print("Implantacao pronta")
    print(f"- corpora ativos: {len(list_active_corpora(monthly_only=True))}")
    print(f"- itens na fila europeia: {len(queue_df)}")
    print(f"- snapshot publico: {snapshot_size / (1024 * 1024):.2f} MB")
    print("- entrada Streamlit: app/streamlit_app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
