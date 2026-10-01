import json
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.output_files import MURNAU_STIFTUNG_OUTPUT_FILES


def _load(key):
    path = OUTPUT_DIR / MURNAU_STIFTUNG_OUTPUT_FILES[key]
    return pd.read_csv(path) if path.exists() else None


def main():
    required = [
        "institutions", "summary", "video_links", "internal_pages",
        "analytic_summary", "analytic_video_catalog", "visibility_summary",
        "theme_summary", "snapshot_metadata", "timeline_corpus",
        "timeline_institutions", "extinction_signals",
    ]
    missing = [
        MURNAU_STIFTUNG_OUTPUT_FILES[key] for key in required
        if not (OUTPUT_DIR / MURNAU_STIFTUNG_OUTPUT_FILES[key]).exists()
    ]
    summary = _load("summary")
    links = _load("video_links")
    internal = _load("internal_pages")
    if summary is None or summary.empty:
        print("Murnau-Stiftung: resumo ausente ou vazio.")
        return 1
    if links is None or links.empty:
        print("Murnau-Stiftung: nenhum registro materializado.")
        return 1
    if internal is None or internal.empty:
        print("Murnau-Stiftung: trilha de páginas ausente.")
        return 1
    if not links["video_link"].astype(str).str.contains(
        r"murnau-stiftung\.de/movie/\d+", regex=True
    ).any():
        print("Murnau-Stiftung: nenhum permalink /movie/<id> materializado.")
        return 1
    payload = json.loads(
        (OUTPUT_DIR / MURNAU_STIFTUNG_OUTPUT_FILES["snapshot_metadata"]).read_text(
            encoding="utf-8"
        )
    )
    if payload.get("dataset") != "murnau_stiftung":
        print("Murnau-Stiftung: dataset incorreto no snapshot.")
        return 1
    if missing:
        print("Murnau-Stiftung: arquivos ausentes:")
        for name in missing:
            print(f"- {name}")
        return 1
    print("Validação do corpus Murnau-Stiftung")
    print(f"- registros materializados: {len(links)}")
    print(f"- páginas observadas: {len(internal)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
