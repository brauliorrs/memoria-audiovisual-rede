import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

PLAYWRIGHT_DIR = ROOT_DIR / ".playwright"
if PLAYWRIGHT_DIR.exists() and "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(PLAYWRIGHT_DIR)

from memoria_audiovisual.pipeline import run_ppa_pipeline


if __name__ == "__main__":
    run_ppa_pipeline()
