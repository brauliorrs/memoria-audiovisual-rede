from __future__ import annotations

from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.scientific_snapshot import (
    assert_scientific_snapshot,
    audit_scientific_snapshot,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = audit_scientific_snapshot(root)
    assert_scientific_snapshot(report)
    print("Snapshot científico consistente.")
    print(f"- versão: {report.version}")
    print(f"- estado: {report.status}")
    print(f"- unidades referenciadas: {report.entity_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
