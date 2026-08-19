#!/usr/bin/env python3
"""Executa uma amostra real e controlada para validação M3 de superfícies do MAR.

A execução usa exclusivamente URLs canônicas declaradas em ``CORPORA`` e a
exploração pública já implementada pelo MAR. Os resultados são experimentais,
não alteram o baseline oficial e devem alimentar uma fila cega de revisão humana.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure.ai_surface_discovery import (
    SurfaceDiscoveryPolicy,
    discover_and_materialize_public_surfaces,
)

DEFAULT_ENTITIES = ("ina", "ecpad", "archipop", "bfi", "europeana")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/output"))
    parser.add_argument("--run-id", default="m3-surface-sample-v1")
    parser.add_argument("--entities", nargs="+", default=list(DEFAULT_ENTITIES))
    parser.add_argument("--max-depth", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=6)
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    policy = SurfaceDiscoveryPolicy(
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        timeout_seconds=args.timeout_seconds,
        respect_robots_txt=True,
    )

    summary: list[dict[str, object]] = []
    for entity_id in args.entities:
        corpus = CORPORA.get(entity_id)
        if not isinstance(corpus, dict):
            summary.append({
                "entity_id": entity_id,
                "status": "unknown_corpus",
                "root_url": None,
                "pages_total": 0,
                "fetched_pages": 0,
            })
            continue

        root_url = str(corpus.get("source_url") or "").strip()
        if not root_url:
            summary.append({
                "entity_id": entity_id,
                "status": "missing_source_url",
                "root_url": None,
                "pages_total": 0,
                "fetched_pages": 0,
            })
            continue

        try:
            report, report_path, classifier_path = discover_and_materialize_public_surfaces(
                root_url,
                output_dir=args.output_dir,
                run_id=args.run_id,
                entity_id=entity_id,
                policy=policy,
            )
        except Exception as exc:  # preserve auditability; do not abort other corpora
            summary.append({
                "entity_id": entity_id,
                "status": "execution_error",
                "root_url": root_url,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "pages_total": 0,
                "fetched_pages": 0,
            })
            continue

        summary.append({
            "entity_id": entity_id,
            "status": "completed",
            "root_url": root_url,
            "pages_total": len(report.pages),
            "fetched_pages": report.fetched_pages,
            "errors_total": len(report.errors),
            "report_path": str(report_path),
            "classifier_path": str(classifier_path),
        })

    payload = {
        "schema_version": "1.0.0",
        "run_id": args.run_id,
        "stage": "t2a_mar_surface_typing_real_sample",
        "does_not_modify_official_baseline": True,
        "is_scientific_result": False,
        "entities_requested": list(args.entities),
        "policy": {
            "max_depth": policy.max_depth,
            "max_pages": policy.max_pages,
            "timeout_seconds": policy.timeout_seconds,
            "respect_robots_txt": policy.respect_robots_txt,
        },
        "entities": summary,
    }
    summary_path = args.output_dir / "_ai_surface_discovery" / args.run_id / "sample_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
