import json
import sys
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import CZECH_TELEVISION_IVYSILANI_URL, OUTPUT_DIR
from memoria_audiovisual.output_files import CZECH_TELEVISION_OUTPUT_FILES


def read_csv(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main():
    missing = [filename for filename in CZECH_TELEVISION_OUTPUT_FILES.values() if not (OUTPUT_DIR / filename).exists()]
    if missing:
        print("Arquivos Czech Television ausentes:")
        for filename in missing:
            print(f"- {filename}")
        return 1

    institutions_df = read_csv(OUTPUT_DIR / CZECH_TELEVISION_OUTPUT_FILES["institutions"])
    links_df = read_csv(OUTPUT_DIR / CZECH_TELEVISION_OUTPUT_FILES["video_links"])
    analytic_catalog_df = read_csv(OUTPUT_DIR / CZECH_TELEVISION_OUTPUT_FILES["analytic_video_catalog"])
    snapshot = json.loads((OUTPUT_DIR / CZECH_TELEVISION_OUTPUT_FILES["snapshot_metadata"]).read_text(encoding="utf-8"))

    print("Validação do corpus Czech Television")
    print(f"- instituições na base: {len(institutions_df)}")
    print(f"- registros audiovisuais materializados: {len(links_df)}")
    print(f"- registros no catálogo analítico: {len(analytic_catalog_df)}")

    if institutions_df.empty or links_df.empty or analytic_catalog_df.empty:
        print("- corpus Czech Television vazio ou sem catálogo analítico")
        return 1
    if snapshot.get("source_url") != CZECH_TELEVISION_IVYSILANI_URL:
        print("- fonte iVysílání inesperada no snapshot")
        return 1
    if snapshot.get("counts", {}).get("video_links_total", 0) < 1:
        print("- snapshot Czech Television não registra vídeos")
        return 1
    if not links_df["platform"].astype(str).str.contains("Česká televize iVysílání", regex=False).any():
        print("- plataforma iVysílání não foi encontrada nos links de vídeo")
        return 1

    print("- todos os arquivos esperados da Czech Television foram encontrados")
    print("- metadados da rodada:")
    print(f"  - fonte iVysílání: {snapshot.get('source_url')}")
    print(f"  - chave de observação: {snapshot.get('observation_key')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
