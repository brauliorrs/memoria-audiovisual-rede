import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.output_files import FORUM_DES_IMAGES_OUTPUT_FILES


def load_csv(key):
    path = OUTPUT_DIR / FORUM_DES_IMAGES_OUTPUT_FILES[key]
    return pd.read_csv(path) if path.exists() else None


def main():
    required = [
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
    missing = [
        FORUM_DES_IMAGES_OUTPUT_FILES[key]
        for key in required
        if not (OUTPUT_DIR / FORUM_DES_IMAGES_OUTPUT_FILES[key]).exists()
    ]
    summary = load_csv("summary")
    links = load_csv("video_links")
    internal = load_csv("internal_pages")
    if summary is None or summary.empty:
        print("Forum des images: resumo ausente ou vazio.")
        return 1
    if links is None or links.empty:
        print("Forum des images: nenhum registro audiovisual materializado.")
        return 1
    if internal is None or internal.empty:
        print("Forum des images: trilha de páginas internas ausente.")
        return 1
    if "platform" not in links.columns or not links["platform"].eq(
        "Collections du Forum des images"
    ).any():
        print("Forum des images: plataforma esperada não encontrada.")
        return 1
    if not links["video_link"].astype(str).str.contains(
        r"collections\.forumdesimages\.fr", regex=True
    ).any():
        print("Forum des images: nenhum permalink público do catálogo materializado.")
        return 1
    metadata_path = OUTPUT_DIR / FORUM_DES_IMAGES_OUTPUT_FILES["snapshot_metadata"]
    if not metadata_path.exists():
        print("Forum des images: snapshot metadata ausente.")
        return 1
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if payload.get("dataset") != "forum_des_images":
        print("Forum des images: dataset incorreto no snapshot metadata.")
        return 1
    if missing:
        print("Forum des images: arquivos ausentes:")
        for name in missing:
            print(f"- {name}")
        return 1
    print("Validação do corpus Forum des images")
    print(f"- registros materializados: {len(links)}")
    print(f"- páginas observadas: {len(internal)}")
    print("- todos os arquivos esperados foram encontrados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
