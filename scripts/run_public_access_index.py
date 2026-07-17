import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.public_access_index import write_public_access_index


if __name__ == "__main__":
    outputs = write_public_access_index()
    print("Índice de dados públicos materializado.")
    print(f"- recortes World/continente: {len(outputs['index'])}")
    print(f"- corpora avaliados: {len(outputs['by_corpus'])}")
    print(f"- unidades restritas no índice: {len(outputs['restricted_units'])}")
