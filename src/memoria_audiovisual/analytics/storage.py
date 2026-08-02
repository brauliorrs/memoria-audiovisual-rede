"""Persistência imutável e auditável das execuções analíticas."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from memoria_audiovisual.digital_infrastructure.models import utc_now_iso

from .engine import AnalyticsRun


@dataclass(frozen=True, slots=True)
class AnalyticsManifest:
    snapshot_id: str
    methodology_version: str
    indicators_path: str
    indicators_sha256: str
    indicator_count: int
    result_keys: tuple[str, ...]
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["result_keys"] = list(self.result_keys)
        return payload


def result_key(result: Mapping[str, Any]) -> str:
    """Identifica univocamente um resultado analítico versionado."""
    parts = (
        str(result.get("snapshot_id") or "").strip(),
        str(result.get("indicator_id") or "").strip(),
        str(result.get("indicator_version") or "").strip(),
        str(result.get("methodology_version") or "").strip(),
    )
    if not all(parts):
        raise ValueError("resultado analítico sem chave versionada completa")
    return "|".join(parts)


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        newline="\n",
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


class AnalyticsStore:
    """Grava uma execução por snapshot sem sobrescrever resultados anteriores."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.history_path = self.root / "indicator_history.jsonl"

    def _history_keys(self) -> set[str]:
        if not self.history_path.exists():
            return set()
        keys: set[str] = set()
        with self.history_path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"histórico analítico inválido na linha {line_number}"
                    ) from exc
                key = result_key(record)
                if key in keys:
                    raise ValueError(f"histórico contém chave duplicada: {key}")
                keys.add(key)
        return keys

    def write(self, run: AnalyticsRun) -> AnalyticsManifest:
        if run.status != "completed":
            raise ValueError("somente execuções concluídas sem erro podem ser persistidas")
        if run.indicator_count != len(run.results):
            raise ValueError("indicator_count diverge dos resultados")

        results = tuple(item.to_dict() for item in run.results)
        keys = tuple(result_key(item) for item in results)
        if len(set(keys)) != len(keys):
            raise ValueError("execução contém resultados analíticos duplicados")

        existing_keys = self._history_keys()
        conflicts = sorted(existing_keys.intersection(keys))
        if conflicts:
            raise FileExistsError(
                "resultado analítico já persistido: " + ", ".join(conflicts)
            )

        snapshot_dir = self.root / run.snapshot_id
        indicators_path = snapshot_dir / "snapshot_indicators.json"
        manifest_path = snapshot_dir / "manifest.json"
        if indicators_path.exists() or manifest_path.exists():
            raise FileExistsError(f"execução analítica já existe para {run.snapshot_id}")

        payload = {
            "snapshot_id": run.snapshot_id,
            "methodology_version": run.methodology_version,
            "status": run.status,
            "indicator_count": run.indicator_count,
            "results": list(results),
        }
        digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
        manifest = AnalyticsManifest(
            snapshot_id=run.snapshot_id,
            methodology_version=run.methodology_version,
            indicators_path=str(indicators_path),
            indicators_sha256=digest,
            indicator_count=run.indicator_count,
            result_keys=keys,
        )

        _atomic_write_json(indicators_path, payload)
        _atomic_write_json(manifest_path, manifest.to_dict())
        with self.history_path.open("a", encoding="utf-8", newline="\n") as handle:
            for result in results:
                history_record = dict(result)
                history_record["indicators_sha256"] = digest
                history_record["persisted_at"] = manifest.generated_at
                handle.write(
                    json.dumps(history_record, ensure_ascii=False, sort_keys=True) + "\n"
                )
            handle.flush()
            os.fsync(handle.fileno())
        return manifest

    def verify(self, snapshot_id: str) -> AnalyticsManifest:
        snapshot_dir = self.root / snapshot_id
        indicators_path = snapshot_dir / "snapshot_indicators.json"
        manifest_path = snapshot_dir / "manifest.json"
        if not indicators_path.exists() or not manifest_path.exists():
            raise FileNotFoundError(f"produtos analíticos ausentes para {snapshot_id}")
        payload = json.loads(indicators_path.read_text(encoding="utf-8"))
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = str(manifest_payload.get("indicators_sha256") or "")
        actual = hashlib.sha256(_canonical_json(payload)).hexdigest()
        if actual != expected:
            raise ValueError("hash dos indicadores diverge do manifesto")
        results = payload.get("results", [])
        if int(manifest_payload.get("indicator_count", -1)) != len(results):
            raise ValueError("contagem do manifesto diverge dos indicadores")
        manifest_payload["result_keys"] = tuple(manifest_payload.get("result_keys", ()))
        return AnalyticsManifest(**manifest_payload)
