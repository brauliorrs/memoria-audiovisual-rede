import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.atresmedia_protocol import ATRESMEDIA_PROTOCOL_FILENAME, write_atresmedia_protocol_probe
from memoria_audiovisual.config import OUTPUT_DIR


def main():
    protocol_df = write_atresmedia_protocol_probe(OUTPUT_DIR)
    print("Protocolo Atresmedia concluído.")
    print(f"- sondagens registradas: {len(protocol_df)}")
    print(f"- arquivo: {ATRESMEDIA_PROTOCOL_FILENAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
