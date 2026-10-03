import json
import re
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import IMAGE_EST_SITEMAP_URL, OUTPUT_DIR
from memoria_audiovisual.output_files import IMAGE_EST_OUTPUT_FILES


def load_csv(key):
    path = OUTPUT_DIR / IMAGE_EST_OUTPUT_FILES[key]
    return pd.read_csv(path) if path.exists() else None


def _type_count(internal, type_code):
    target = f"{IMAGE_EST_SITEMAP_URL}#type={type_code}"
    rows = internal.loc[
        internal["internal_page"].astype(str) == target
    ]
    if len(rows) != 1:
        raise ValueError(f"Image'Est: type={type_code} row ausente ou duplicada.")
    row = rows.iloc[0]
    if str(row.get("status", "")) != "ok":
        raise ValueError(f"Image'Est: type={type_code} não validado.")
    return int(row.get("video_links_found", 0))


def main():
    summary = load_csv("summary")
    links = load_csv("video_links")
    internal = load_csv("internal_pages")
    if summary is None or summary.empty:
        print("Image'Est: resumo ausente ou vazio.")
        return 1
    if links is None or links.empty:
        print("Image'Est: nenhum permalink audiovisual materializado.")
        return 1
    if internal is None or internal.empty:
        print("Image'Est: trilha de enumeração ausente.")
        return 1

    row = summary.iloc[0]
    print("Image'Est: resumo staged")
    print(f"- integridade: {row.get('integrity_status', '-')}")
    print(f"- registros: {row.get('video_links_found_total', 0)}")
    print(f"- nota: {row.get('warning', '')}")
    if row.get("integrity_status") != "integro":
        print("Image'Est: snapshot não íntegro.")
        return 1

    permalink_pattern = re.compile(
        r"^https://www\.image-est\.fr/"
        r"fiche-documentaire-[^?#]+-1284-[^/?#]+-(?:1|3)-0\.html$",
        re.I,
    )
    values = links["video_link"].astype(str)
    if not values.map(lambda value: bool(permalink_pattern.match(value))).all():
        print("Image'Est: permalink fora dos tipos audiovisuais 1/3.")
        return 1
    if values.duplicated().any():
        print("Image'Est: permalinks duplicados.")
        return 1
    if values.str.contains(r"-1284-[^/]+-2-0\.html$", regex=True).any():
        print("Image'Est: tipo 2 não audiovisual vazou para o corpus.")
        return 1

    try:
        type_1 = _type_count(internal, "1")
        type_2 = _type_count(internal, "2")
        type_3 = _type_count(internal, "3")
    except ValueError as exc:
        print(str(exc))
        return 1

    if min(type_1, type_2, type_3) <= 0:
        print("Image'Est: classificação de tipos incompleta.")
        return 1
    if len(links) != type_1 + type_3:
        print(
            "Image'Est: total audiovisual não coincide com "
            f"type1+type3 ({len(links)} != {type_1}+{type_3})."
        )
        return 1

    metadata_path = OUTPUT_DIR / IMAGE_EST_OUTPUT_FILES["snapshot_metadata"]
    if not metadata_path.exists():
        print("Image'Est: snapshot metadata ausente.")
        return 1
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if payload.get("dataset") != "image_est":
        print("Image'Est: dataset incorreto no snapshot metadata.")
        return 1
    if payload.get("source_url") != IMAGE_EST_SITEMAP_URL:
        print("Image'Est: fonte canônica incorreta.")
        return 1

    print("Validação staged da Image'Est")
    print(f"- registros audiovisuais: {len(links)}")
    print(f"- type 1: {type_1}")
    print(f"- type 2 excluído: {type_2}")
    print(f"- type 3: {type_3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
