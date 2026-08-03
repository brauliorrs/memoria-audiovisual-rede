"""Persistência verificável de índices derivados do ledger."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .integrity import LedgerIndex
from .ledger import AtomicLedger


def _ledger_digest(ledger: AtomicLedger) -> str:
    if not ledger.path.exists():
        return hashlib.sha256(b"").hexdigest()
    digest = hashlib.sha256()
    with ledger.path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_index_snapshot(ledger: AtomicLedger) -> dict[str, Any]:
    index = LedgerIndex.build(ledger)
    return {
        "index_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ledger_sha256": _ledger_digest(ledger),
        "entities": sorted(index.entities),
        "versions": sorted(index.versions),
        "evidences": sorted(index.evidences),
        "latest_version_by_entity": dict(sorted(index.latest_version_by_entity.items())),
    }


def write_index_snapshot(ledger: AtomicLedger, destination: str | Path) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = build_index_snapshot(ledger)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def verify_index_snapshot(ledger: AtomicLedger, source: str | Path) -> bool:
    path = Path(source)
    if not path.exists():
        return False
    stored = json.loads(path.read_text(encoding="utf-8"))
    current = build_index_snapshot(ledger)
    for volatile in ("generated_at",):
        stored.pop(volatile, None)
        current.pop(volatile, None)
    return stored == current
