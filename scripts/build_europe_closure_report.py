import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.europe_closure import (
    EUROPE_CLOSURE_DOSSIER_FILENAME,
    EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME,
    EUROPE_CLOSURE_GAP_AUDIT_FILENAME,
    EUROPE_CLOSURE_QUEUE_FILENAME,
    write_europe_closure_outputs,
)


def main():
    outputs = write_europe_closure_outputs(OUTPUT_DIR)
    matrix_df = outputs["matrix"]
    queue_df = outputs["queue"]
    excluded_units_df = outputs["excluded_units"]
    gap_audit_df = outputs["gap_audit"]
    summary_df = outputs["summary"]

    print("Relatório de fechamento europeu atualizado:")
    print(f"- unidades na matriz: {len(matrix_df)}")
    print(f"- unidades na fila: {len(queue_df)}")
    print(f"- unidades identificadas fora do corpus: {len(excluded_units_df)}")
    print(f"- lacunas europeias auditadas: {len(gap_audit_df)}")
    print(f"- fila europeia: {EUROPE_CLOSURE_QUEUE_FILENAME}")
    print(f"- unidades fora do corpus: {EUROPE_CLOSURE_EXCLUDED_UNITS_FILENAME}")
    print(f"- auditoria de lacunas: {EUROPE_CLOSURE_GAP_AUDIT_FILENAME}")
    print(f"- dossiê MVP: {EUROPE_CLOSURE_DOSSIER_FILENAME}")
    print(f"- critérios de fechamento: {len(summary_df)}")
    for _, row in summary_df.iterrows():
        print(f"- {row['criterion']}: {row['status']}")


if __name__ == "__main__":
    raise SystemExit(main())
