"""Audita o registro canônico contra o catálogo legado e a metodologia."""

from __future__ import annotations

import json
from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.indicator_consistency import (
    assert_consolidated_identity,
    compare_indicator_sources,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = ROOT / "data/templates/analytics/indicator_registry.json"
LEGACY_PATH = ROOT / "data/templates/analytics/indicator_catalog.json"
METHODOLOGY_PATH = ROOT / "data/templates/analytics/methodology_registry.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    canonical = _load(CANONICAL_PATH)
    legacy = _load(LEGACY_PATH)
    methodology = _load(METHODOLOGY_PATH)

    report = compare_indicator_sources(
        canonical.get("indicators", []),
        legacy.get("indicators", []),
        methodology.get("methodologies", []),
    )
    assert_consolidated_identity(report)

    print("Identidade científica consolidada.")
    print(f"- indicadores canônicos: {len(report.canonical_ids)}")
    print(f"- indicadores legados: {len(report.legacy_ids)}")
    print(f"- metodologias registradas: {len(report.methodology_ids)}")
    if report.missing_methodologies:
        print("- metodologias pendentes para o Sprint 2B:")
        for indicator_id in report.missing_methodologies:
            print(f"  - {indicator_id}")
    if report.orphan_methodologies:
        print("- metodologias órfãs:")
        for indicator_id in report.orphan_methodologies:
            print(f"  - {indicator_id}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
