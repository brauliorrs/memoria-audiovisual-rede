import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.european_protocols import write_archiveshub_protocol_probe


def main():
    protocol_df = write_archiveshub_protocol_probe(OUTPUT_DIR)

    print("Protótipo de protocolo Archives Hub atualizado:")
    print(f"- sondagens leves: {len(protocol_df)}")
    for _, row in protocol_df.iterrows():
        print(
            f"- {row['probe_label']}: {row['protocol_conclusion']} | "
            f"status={row['access_status']}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
