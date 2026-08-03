"""Persistência local append-only para entidades e proveniência."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


class JsonlRepository:
    """Repositório simples, auditável e sem sobrescrita.

    Cada gravação cria uma nova linha JSON. Registros anteriores permanecem intactos.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, collection: str) -> Path:
        if not collection or any(part in collection for part in ("/", "\\", "..")):
            raise ValueError("collection deve ser um nome simples")
        return self.root / f"{collection}.jsonl"

    def append(self, collection: str, record: Mapping[str, Any]) -> Path:
        path = self._path(collection)
        serialized = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized + "\n")
        return path

    def append_many(self, collection: str, records: Iterable[Mapping[str, Any]]) -> Path:
        path = self._path(collection)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        return path

    def read_all(self, collection: str) -> list[dict[str, Any]]:
        path = self._path(collection)
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"JSON inválido em {path}:{line_number}") from exc
        return records

    def latest_by(self, collection: str, key: str) -> dict[str, dict[str, Any]]:
        latest: dict[str, dict[str, Any]] = {}
        for record in self.read_all(collection):
            value = record.get(key)
            if value is not None:
                latest[str(value)] = record
        return latest
