import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import DEUTSCHE_KINEMATHEK_STREAMING_URL, OUTPUT_DIR
from memoria_audiovisual.output_files import DEUTSCHE_KINEMATHEK_OUTPUT_FILES


def read_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main():
    missing = [
        filename
        for filename in DEUTSCHE_KINEMATHEK_OUTPUT_FILES.values()
        if not (OUTPUT_DIR / filename).exists()
    ]
    if missing:
        print("Arquivos Deutsche Kinemathek ausentes:")
        for filename in missing:
            print(f"- {filename}")
        return 1

    institutions_df = read_csv(OUTPUT_DIR / DEUTSCHE_KINEMATHEK_OUTPUT_FILES["institutions"])
    links_df = read_csv(OUTPUT_DIR / DEUTSCHE_KINEMATHEK_OUTPUT_FILES["video_links"])
    analytic_catalog_df = read_csv(OUTPUT_DIR / DEUTSCHE_KINEMATHEK_OUTPUT_FILES["analytic_video_catalog"])
    snapshot = json.loads((OUTPUT_DIR / DEUTSCHE_KINEMATHEK_OUTPUT_FILES["snapshot_metadata"]).read_text(encoding="utf-8"))

    print("Validação do corpus Deutsche Kinemathek / Selects")
    print(f"- instituições na base: {len(institutions_df)}")
    print(f"- filmes Selects materializados: {len(links_df)}")
    print(f"- registros no catálogo analítico: {len(analytic_catalog_df)}")

    if institutions_df.empty or links_df.empty or analytic_catalog_df.empty:
        print("- corpus Deutsche Kinemathek vazio ou sem catálogo analítico")
        return 1
    if snapshot.get("source_url") != DEUTSCHE_KINEMATHEK_STREAMING_URL:
        print("- fonte Selects inesperada no snapshot")
        return 1
    if snapshot.get("counts", {}).get("video_links_total", 0) < 1:
        print("- snapshot Deutsche Kinemathek não registra vídeos")
        return 1
    if not links_df["platform"].astype(str).str.contains("Deutsche Kinemathek Selects", regex=False).any():
        print("- plataforma Deutsche Kinemathek Selects não foi encontrada nos links")
        return 1

    print("- todos os arquivos esperados da Deutsche Kinemathek foram encontrados")
    print("- metadados da rodada:")
    print(f"  - fonte Selects: {snapshot.get('source_url')}")
    print(f"  - chave de observação: {snapshot.get('observation_key')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
