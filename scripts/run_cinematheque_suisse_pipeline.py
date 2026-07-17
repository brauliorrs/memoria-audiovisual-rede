import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.pipeline import run_cinematheque_suisse_pipeline


if __name__ == "__main__":
    run_cinematheque_suisse_pipeline()
