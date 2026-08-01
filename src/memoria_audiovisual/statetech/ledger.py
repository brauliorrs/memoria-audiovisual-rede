"""Ledger append-only para gravações logicamente atômicas."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .locking import FileWriteLock


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    transaction_id: str
    records: tuple[dict[str, Any], ...]


class AtomicLedger:
    """Armazena um conjunto de registros em uma única linha JSONL.

    A linha é a unidade lógica de commit. Escritas cooperativas são serializadas
    por lock de arquivo. Isso não equivale a uma transação ACID.
    """

    def __init__(self, path: str | Path, *, lock_timeout: float = 10.0) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_timeout = lock_timeout

    def append(self, records: Sequence[Mapping[str, Any]]) -> LedgerEntry:
        if not records:
            raise ValueError("a transação deve conter ao menos um registro")
        entry = LedgerEntry(
            transaction_id=f"txn_{uuid4().hex}",
            records=tuple(dict(record) for record in records),
        )
        payload = {
            "transaction_id": entry.transaction_id,
            "records": list(entry.records),
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str) + "\n"
        with FileWriteLock(self.path, timeout=self.lock_timeout):
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(serialized)
                handle.flush()
        return entry

    def read_all(self) -> list[LedgerEntry]:
        if not self.path.exists():
            return []
        entries: list[LedgerEntry] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"transação inválida em {self.path}:{line_number}") from exc
                entries.append(
                    LedgerEntry(
                        transaction_id=str(payload["transaction_id"]),
                        records=tuple(dict(record) for record in payload["records"]),
                    )
                )
        return entries
