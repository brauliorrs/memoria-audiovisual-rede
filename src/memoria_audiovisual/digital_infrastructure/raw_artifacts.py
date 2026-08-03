"""Preservação content-addressed de entradas brutas da ingestão.

Os artefatos são serializados canonicamente em JSON, identificados por SHA-256 e
escritos apenas quando ainda não existem. Um mesmo conteúdo sempre produz o
mesmo ``artifact_id``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any


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
    """Armazena artefatos JSON de forma imutável e deduplicada por conteúdo."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def preserve(self, value: Any) -> RawArtifact:
        payload = canonical_json_bytes(value)
        digest = hashlib.sha256(payload).hexdigest()
        artifact_id = f"artifact_sha256_{digest}"
        target = self.root / digest[:2] / f"{digest}.json"
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            existing = target.read_bytes()
            if hashlib.sha256(existing).hexdigest() != digest:
                raise ValueError(f"artefato existente diverge do hash esperado: {target}")
        else:
            temporary = target.with_suffix(".json.tmp")
            temporary.write_bytes(payload)
            temporary.replace(target)

        return RawArtifact(
            artifact_id=artifact_id,
            sha256=digest,
            media_type="application/json",
            byte_size=len(payload),
            path=str(target),
        )
