"""Manifestos append-only para acompanhar e retomar lotes de ingestão."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from .ids import stable_id
from .models import utc_now_iso

BatchStatus = Literal["prepared", "running", "completed", "failed"]


@dataclass(frozen=True, slots=True)
class BatchManifest:
    batch_id: str
    adapter_name: str
    adapter_version: str
    source_artifact_id: str
    record_count: int
    status: BatchStatus = "prepared"
    committed_keys: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["committed_keys"] = list(self.committed_keys)
        return data


class BatchManifestStore:
    """Mantém o estado mais recente de cada lote em um log JSONL reconstruível."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def build_batch_id(
        *, adapter_name: str, adapter_version: str, source_artifact_id: str
    ) -> str:
        return stable_id(
            "ingestion-batch",
            "|".join((adapter_name, adapter_version, source_artifact_id)),
        )

    def append(self, manifest: BatchManifest) -> None:
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True)
                + "\n"
            )
            handle.flush()

    def latest(self, batch_id: str) -> BatchManifest | None:
        latest: BatchManifest | None = None
        if not self.path.exists():
            return None
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"manifesto de lote inválido em {self.path}:{line_number}"
                    ) from exc
                if payload.get("batch_id") != batch_id:
                    continue
                payload["committed_keys"] = tuple(payload.get("committed_keys", ()))
                latest = BatchManifest(**payload)
        return latest
