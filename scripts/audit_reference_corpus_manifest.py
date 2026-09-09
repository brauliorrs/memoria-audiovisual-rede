"""Audita o Scientific Reference Corpus Manifest."""

from __future__ import annotations

from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.reference_corpus_manifest import (
    assert_reference_corpus_manifest,
    audit_reference_corpus_manifest,
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = audit_reference_corpus_manifest(root)
    assert_reference_corpus_manifest(report)
    print("Manifesto científico do corpus de referência íntegro.")
    print(f"- versão: {report.version}")
    print(f"- fonte: {report.dataset_path}")
    print(f"- unidades: {report.entity_count}")
    print(f"- hash: {report.content_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
