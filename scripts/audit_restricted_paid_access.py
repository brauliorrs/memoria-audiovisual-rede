import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.restricted_access_audit import (
    RESTRICTED_ACCESS_AUDIT_FILENAME,
    RESTRICTED_ACCESS_SUMMARY_FILENAME,
    write_restricted_access_audit,
)


def main():
    outputs = write_restricted_access_audit(OUTPUT_DIR)
    print("Auditoria de acesso pago/restrito concluída.")
    print(f"- casos auditados: {len(outputs['audit'])}")
    print(f"- categorias: {len(outputs['summary'])}")
    print(f"- auditoria: {RESTRICTED_ACCESS_AUDIT_FILENAME}")
    print(f"- resumo: {RESTRICTED_ACCESS_SUMMARY_FILENAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
