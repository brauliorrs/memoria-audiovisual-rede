import json
import re
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import (
    IFI_ARCHIVE_PLAYER_SITEMAP_INDEX_URL,
    OUTPUT_DIR,
)
from memoria_audiovisual.output_files import IFI_ARCHIVE_PLAYER_OUTPUT_FILES


def load_csv(key):
    path = OUTPUT_DIR / IFI_ARCHIVE_PLAYER_OUTPUT_FILES[key]
    return pd.read_csv(path) if path.exists() else None


def main():
    summary = load_csv("summary")
    links = load_csv("video_links")
    internal = load_csv("internal_pages")
    if summary is None or summary.empty:
        print("IFI Archive Player: resumo ausente ou vazio.")
        return 1
    if links is None or links.empty:
        print("IFI Archive Player: nenhum permalink materializado.")
        return 1
    if internal is None or internal.empty:
        print("IFI Archive Player: trilha de enumeração ausente.")
        return 1

    row = summary.iloc[0]
    print("IFI Archive Player: resumo staged")
    print(f"- integridade: {row.get('integrity_status', '-')}")
    print(f"- registros: {row.get('video_links_found_total', 0)}")
    print(f"- nota: {row.get('warning', '')}")
    if row.get("integrity_status") != "integro":
        print("IFI Archive Player: snapshot não íntegro.")
        return 1

    link_pattern = re.compile(r"^https://ifiarchiveplayer\.ie/[^/?#]+/$")
    if not links["video_link"].astype(str).map(
        lambda value: bool(link_pattern.match(value))
    ).all():
        print("IFI Archive Player: permalink fora do contrato esperado.")
        return 1
    if links["video_link"].astype(str).duplicated().any():
        print("IFI Archive Player: permalinks duplicados.")
        return 1

    partitions = internal[
        internal["internal_page"].astype(str).str.match(
            r"^https://ifiarchiveplayer\.ie/post-sitemap(?:\d+)?\.xml$"
        )
    ]
    if partitions.empty:
        print("IFI Archive Player: nenhuma partição post-sitemap registrada.")
        return 1
    if not (partitions["status"].astype(str) == "ok").all():
        print("IFI Archive Player: partição obrigatória falhou.")
        return 1

    metadata_path = OUTPUT_DIR / IFI_ARCHIVE_PLAYER_OUTPUT_FILES["snapshot_metadata"]
    if not metadata_path.exists():
        print("IFI Archive Player: snapshot metadata ausente.")
        return 1
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if payload.get("dataset") != "ifi_archive_player":
        print("IFI Archive Player: dataset incorreto no snapshot metadata.")
        return 1
    if payload.get("source_url") != IFI_ARCHIVE_PLAYER_SITEMAP_INDEX_URL:
        print("IFI Archive Player: fonte canônica incorreta.")
        return 1

    print("Validação staged do IFI Archive Player")
    print(f"- registros materializados: {len(links)}")
    print(f"- post-sitemaps materializados: {len(partitions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
