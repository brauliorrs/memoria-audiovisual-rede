"""Preservação content-addressed e imutável das entradas brutas."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

from .locking import FileWriteLock


@dataclass(frozen=True, slots=True)
class RawArtifact:
    artifact_id: str
    sha256: str
    media_type: str
    byte_size: int
    path: str


def canonical_json_bytes(value: Any) -> bytes:
    if is_dataclass(value):
        value = asdict(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


class RawArtifactStore:
    """Armazena JSON imutável e deduplicado por SHA-256."""

    def __init__(self, root: str | Path, *, lock_timeout: float = 10.0) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock_timeout = lock_timeout

    def preserve(self, value: Any) -> RawArtifact:
        payload = canonical_json_bytes(value)
        digest = hashlib.sha256(payload).hexdigest()
        artifact_id = f"artifact_sha256_{digest}"
        target = self.root / digest[:2] / f"{digest}.json"
        target.parent.mkdir(parents=True, exist_ok=True)

        with FileWriteLock(target, timeout=self.lock_timeout):
            if target.exists():
                existing = target.read_bytes()
                if hashlib.sha256(existing).hexdigest() != digest:
                    raise ValueError(
                        f"artefato existente diverge do hash esperado: {target}"
                    )
            else:
                temporary = target.with_name(f"{target.name}.{os.getpid()}.tmp")
                try:
                    with temporary.open("wb") as handle:
                        handle.write(payload)
                        handle.flush()
                        os.fsync(handle.fileno())
                    temporary.replace(target)
                finally:
                    temporary.unlink(missing_ok=True)

        return RawArtifact(
            artifact_id=artifact_id,
            sha256=digest,
            media_type="application/json",
            byte_size=len(payload),
            path=str(target),
        )
