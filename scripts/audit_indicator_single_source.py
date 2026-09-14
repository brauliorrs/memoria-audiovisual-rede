"""Verifica se o registro canônico é a única fonte das definições científicas."""

from __future__ import annotations

from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.single_source_audit import (
    assert_single_source,
    find_duplicate_definitions,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    findings = find_duplicate_definitions(ROOT)
    assert_single_source(findings)
    print("Fonte única validada: nenhuma definição científica concorrente foi localizada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
