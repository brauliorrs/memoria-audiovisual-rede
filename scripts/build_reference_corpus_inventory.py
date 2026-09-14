"""Gera ou valida o inventário científico derivado do corpus de referência."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.scientific_infrastructure.reference_corpus_inventory import (
    INVENTORY_PATH,
    MANIFEST_PATH,
    assert_reference_corpus_inventory,
    audit_reference_corpus_inventory,
    build_reference_corpus_inventory,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Valida o inventário materializado sem reescrever o arquivo.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    inventory_path = root / INVENTORY_PATH

    if args.check:
        report = audit_reference_corpus_inventory(root)
        assert_reference_corpus_inventory(report)
        print("Inventário científico derivado íntegro.")
        print(f"- unidades: {report.total_entities}")
        print(f"- unidades ativas: {report.active_entities}")
        return 0

    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    payload = build_reference_corpus_inventory(CORPORA, manifest)
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Inventário regenerado: {inventory_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
