import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.bnfa_protocol import write_bnfa_protocol_probe


def main():
    protocol_df = write_bnfa_protocol_probe()
    print("Protocolo Bulgarian National Film Archive concluído.")
    print(f"- sondagens: {len(protocol_df)}")
    print("- decisão: rota pública BNFA/EFG monitorada para sustentar corpus ativo quando disponível")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
