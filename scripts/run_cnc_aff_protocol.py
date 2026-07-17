import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.cnc_aff_protocol import write_cnc_aff_protocol_probe


if __name__ == "__main__":
    protocol_df = write_cnc_aff_protocol_probe()
    print("Protocolo CNC/AFF concluído.")
    print(f"- sondagens registradas: {len(protocol_df)}")
