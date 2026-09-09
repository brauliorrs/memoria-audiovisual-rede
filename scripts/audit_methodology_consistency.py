"""Executa a auditoria comparativa das metodologias registradas."""

from __future__ import annotations

import json
from pathlib import Path

from memoria_audiovisual.analytics.pipeline import default_indicator_registry
from memoria_audiovisual.scientific_infrastructure.methodology_consistency_audit import (
    assert_methodology_consistency,
    audit_methodologies,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    path = root / "data/templates/analytics/methodology_registry.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = audit_methodologies(
        payload.get("methodologies", []),
        default_indicator_registry(),
    )
    assert_methodology_consistency(report)

    print("Metodologias científicas consistentes.")
    print(f"- metodologias registradas: {report.methodology_count}")
    print(f"- metodologias completas: {report.complete_count}")
    print(f"- classes metodológicas: {len(report.methodology_classes)}")
    for methodology_class in report.methodology_classes:
        print(f"  - {methodology_class}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
