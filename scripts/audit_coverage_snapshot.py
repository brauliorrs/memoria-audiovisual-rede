"""Valida o Coverage Snapshot v1.0 materializado."""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.scientific_infrastructure.coverage_snapshot import (
    assert_coverage_snapshot,
    audit_coverage_snapshot,
)


def main() -> int:
    report = audit_coverage_snapshot(BASE_DIR)
    assert_coverage_snapshot(report)
    print("Coverage Snapshot v1.0 válido.")
    print(f"- corpora: {report.corpus_count}")
    print(f"- estados de cobertura: {report.parameter_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
