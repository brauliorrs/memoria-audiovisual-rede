import json
import re
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import IWM_FILM_SITEMAP_INDEX_URL, OUTPUT_DIR
from memoria_audiovisual.iwm_film import IWM_FILM_MAX_DETAIL_PAGES
from memoria_audiovisual.output_files import IWM_FILM_OUTPUT_FILES


def load_csv(key):
    path = OUTPUT_DIR / IWM_FILM_OUTPUT_FILES[key]
    return pd.read_csv(path) if path.exists() else None


def main():
    summary = load_csv("summary")
    links = load_csv("video_links")
    internal = load_csv("internal_pages")
    if summary is None or summary.empty:
        print("IWM Film: resumo ausente ou vazio.")
        return 1
    if links is None or links.empty:
        print("IWM Film: nenhum permalink materializado.")
        return 1
    if internal is None or internal.empty:
        print("IWM Film: trilha de enumeração ausente.")
        return 1

    row = summary.iloc[0]
    print("IWM Film: resumo staged")
    print(f"- integridade: {row.get('integrity_status', '-')}")
    print(f"- registros: {row.get('video_links_found_total', 0)}")
    print(f"- nota: {row.get('warning', '')}")
    if row.get("integrity_status") != "integro":
        print("IWM Film: snapshot não íntegro.")
        return 1

    link_pattern = re.compile(
        r"^https://film\.iwmcollections\.org\.uk/record/\d+/?$",
        re.I,
    )
    values = links["video_link"].astype(str)
    if not values.map(lambda value: bool(link_pattern.match(value))).all():
        print("IWM Film: permalink fora do contrato esperado.")
        return 1
    if values.duplicated().any():
        print("IWM Film: permalinks duplicados.")
        return 1

    partitions = internal[
        internal["internal_page"].astype(str).str.match(
            r"^https://film\.iwmcollections\.org\.uk/"
            r"instance/sitemaps/sitemap-records(?:-\d+)?\.xml$"
        )
    ]
    if partitions.empty:
        print("IWM Film: nenhuma partição sitemap-records registrada.")
        return 1
    if not (partitions["status"].astype(str) == "ok").all():
        print("IWM Film: partição obrigatória falhou.")
        return 1
    partition_total = int(
        pd.to_numeric(partitions["video_links_found"], errors="coerce")
        .fillna(0)
        .sum()
    )
    if partition_total != len(links):
        print(
            "IWM Film: total materializado não coincide com as partições "
            f"({len(links)} != {partition_total})."
        )
        return 1

    semantic_rows = internal[
        internal["internal_page"].astype(str).str.match(
            r"^https://film\.iwmcollections\.org\.uk/record/\d+/?$"
        )
    ]
    expected_samples = min(IWM_FILM_MAX_DETAIL_PAGES, len(links))
    if len(semantic_rows) != expected_samples:
        print(
            "IWM Film: amostragem semântica incompleta "
            f"({len(semantic_rows)} != {expected_samples})."
        )
        return 1
    if not (semantic_rows["status"].astype(str) == "ok").all():
        print("IWM Film: amostra semântica contém ficha inválida.")
        return 1

    metadata_path = OUTPUT_DIR / IWM_FILM_OUTPUT_FILES["snapshot_metadata"]
    if not metadata_path.exists():
        print("IWM Film: snapshot metadata ausente.")
        return 1
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if payload.get("dataset") != "iwm_film":
        print("IWM Film: dataset incorreto no snapshot metadata.")
        return 1
    if payload.get("source_url") != IWM_FILM_SITEMAP_INDEX_URL:
        print("IWM Film: fonte canônica incorreta.")
        return 1

    print("Validação staged do IWM Film")
    print(f"- registros materializados: {len(links)}")
    print(f"- partições sitemap-records: {len(partitions)}")
    print(f"- fichas semânticas validadas: {len(semantic_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
