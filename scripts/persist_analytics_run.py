#!/usr/bin/env python3
"""Persiste e verifica uma execução produzida pelo motor analítico."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from memoria_audiovisual.analytics.base import IndicatorResult
from memoria_audiovisual.analytics.engine import AnalyticsRun
from memoria_audiovisual.analytics.storage import AnalyticsStore


def _load_run(path: Path) -> AnalyticsRun:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    results = []
    for raw in payload.get("results", []):
        item = dict(raw)
        item["notes"] = tuple(item.get("notes", ()))
        item["dimensions"] = dict(item.get("dimensions", {}))
        results.append(IndicatorResult(**item))
    return AnalyticsRun(
        snapshot_id=str(payload.get("snapshot_id") or ""),
        methodology_version=str(payload.get("methodology_version") or ""),
        indicator_count=int(payload.get("indicator_count", len(results))),
        results=tuple(results),
        status=str(payload.get("status") or "completed"),
        errors=tuple(payload.get("errors", ())),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True, help="JSON da execução analítica")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/digital_infrastructure/analytics"),
    )
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--snapshot-id")
    args = parser.parse_args()

    store = AnalyticsStore(args.output_root)
    if args.verify_only:
        snapshot_id = str(args.snapshot_id or "").strip()
        if not snapshot_id:
            parser.error("--snapshot-id é obrigatório com --verify-only")
        manifest = store.verify(snapshot_id)
    else:
        run = _load_run(args.run)
        manifest = store.write(run)
        store.verify(run.snapshot_id)

    print(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
