#!/usr/bin/env python3
"""Valida o Scientific Indicator Results Registry v1.0."""

from __future__ import annotations

from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.indicator_results_registry import (
    assert_indicator_results_registry,
    audit_indicator_results_registry,
)

EXPECTED_VERSION = "1.0.0"
EXPECTED_STATUS = "completed"
EXPECTED_INDICATOR_COUNT = 9


def main() -> int:
    report = audit_indicator_results_registry(Path.cwd())
    assert_indicator_results_registry(report)

    if report.version != EXPECTED_VERSION:
        raise ValueError(
            f"versão inesperada: {report.version!r}; esperada={EXPECTED_VERSION!r}"
        )
    if report.status != EXPECTED_STATUS:
        raise ValueError(
            f"status inesperado: {report.status!r}; esperado={EXPECTED_STATUS!r}"
        )
    if report.indicator_count != EXPECTED_INDICATOR_COUNT:
        raise ValueError(
            "quantidade inesperada de indicadores: "
            f"{report.indicator_count}; esperada={EXPECTED_INDICATOR_COUNT}"
        )

    print("Registro científico de resultados consistente.")
    print(f"- versão: {report.version}")
    print(f"- indicadores: {report.indicator_count}")
    print(f"- status: {report.status}")
    print("- saída reproduzida pelo Analytics Engine: sim")
    print("- proveniência dos cinco artefatos de origem: verificada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
