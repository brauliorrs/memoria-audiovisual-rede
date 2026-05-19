import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.europe_closure import (
    EUROPE_CLOSURE_DOSSIER_FILENAME,
    EUROPE_CLOSURE_QUEUE_FILENAME,
    write_europe_closure_outputs,
)


def main():
    outputs = write_europe_closure_outputs(OUTPUT_DIR)
    matrix_df = outputs["matrix"]
    queue_df = outputs["queue"]
    summary_df = outputs["summary"]

    print("Relatório de fechamento europeu atualizado:")
    print(f"- unidades na matriz: {len(matrix_df)}")
    print(f"- unidades na fila: {len(queue_df)}")
    print(f"- fila europeia: {EUROPE_CLOSURE_QUEUE_FILENAME}")
    print(f"- dossiê MVP: {EUROPE_CLOSURE_DOSSIER_FILENAME}")
    print(f"- critérios de fechamento: {len(summary_df)}")
    for _, row in summary_df.iterrows():
        print(f"- {row['criterion']}: {row['status']}")


if __name__ == "__main__":
    raise SystemExit(main())
