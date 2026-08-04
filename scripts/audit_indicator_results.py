#!/usr/bin/env python3
"""Valida o Scientific Indicator Results Registry v1.0."""

from __future__ import annotations

from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.indicator_results_registry import (
    assert_indicator_results_registry,
    audit_indicator_results_registry,
)


def main() -> int:
    report = audit_indicator_results_registry(Path.cwd())
    assert_indicator_results_registry(report)
    print("Registro científico de resultados consistente.")
    print(f"- versão: {report.version}")
    print(f"- indicadores: {report.indicator_count}")
    print(f"- status: {report.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
