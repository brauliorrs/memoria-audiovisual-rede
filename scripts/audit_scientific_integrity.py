"""Executa o contrato permanente de integridade científica."""

from __future__ import annotations

from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.scientific_integrity_audit import (
    assert_scientific_integrity,
    audit_scientific_integrity,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = audit_scientific_integrity(root)
    assert_scientific_integrity(report)

    print("Infraestrutura científica íntegra.")
    print(f"- versão do registro: {report.registry_version}")
    print(f"- indicadores canônicos: {report.indicator_count}")
    print(f"- implementações analíticas: {report.implementation_count}")
    print(f"- metodologias registradas: {report.methodology_count}")
    if report.pending_methodologies:
        print("- metodologias explicitamente pendentes:")
        for indicator_id in report.pending_methodologies:
            print(f"  - {indicator_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
