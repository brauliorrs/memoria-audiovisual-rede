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


def load_csv(key):
    path = OUTPUT_DIR / MURNAU_STIFTUNG_OUTPUT_FILES[key]
    return pd.read_csv(path) if path.exists() else None


def main():
    summary = load_csv("summary")
    links = load_csv("video_links")
    internal = load_csv("internal_pages")
    if summary is None or summary.empty:
        print("Murnau-Stiftung: resumo ausente ou vazio.")
        return 1
    if links is None or links.empty:
        print("Murnau-Stiftung: nenhum registro da Filmsuche materializado.")
        return 1
    if internal is None or internal.empty:
        print("Murnau-Stiftung: trilha de consultas ausente.")
        return 1
    print("Murnau-Stiftung: resumo do probe")
    print(f"- status: {summary.iloc[0].get('status', '-')}")
    print(f"- integridade: {summary.iloc[0].get('integrity_status', '-')}")
    print(f"- registros declarados/materializados: {summary.iloc[0].get('video_links_found_total', 0)}")
    print(f"- nota: {summary.iloc[0].get('warning', '')}")
    if summary.iloc[0].get("integrity_status") != "integro":
        print("Murnau-Stiftung: snapshot de busca não íntegro; revisar partições.")
        return 1
    if not links["video_link"].astype(str).str.match(
        r"https://www\.murnau-stiftung\.de/movie/\d+$"
    ).all():
        print("Murnau-Stiftung: permalink fora do contrato esperado.")
        return 1
    metadata_path = OUTPUT_DIR / MURNAU_STIFTUNG_OUTPUT_FILES["snapshot_metadata"]
    if not metadata_path.exists():
        print("Murnau-Stiftung: snapshot metadata ausente.")
        return 1
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if payload.get("dataset") != "murnau_stiftung":
        print("Murnau-Stiftung: dataset incorreto no snapshot metadata.")
        return 1
    print("Validação staged da Murnau-Stiftung")
    print(f"- registros materializados: {len(links)}")
    print(f"- consultas/páginas observadas: {len(internal)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
