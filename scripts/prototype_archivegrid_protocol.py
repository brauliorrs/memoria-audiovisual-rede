import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.archivegrid_protocol import write_archivegrid_protocol_probe
from memoria_audiovisual.config import OUTPUT_DIR


def main():
    protocol_df = write_archivegrid_protocol_probe(OUTPUT_DIR)
    print("Protótipo de protocolo ArchiveGrid atualizado:")
    print(f"- sondagens: {len(protocol_df)}")
    if "protocol_conclusion" in protocol_df.columns:
        for conclusion, total in protocol_df["protocol_conclusion"].value_counts().sort_index().items():
            print(f"- {conclusion}: {total}")


if __name__ == "__main__":
    raise SystemExit(main())
