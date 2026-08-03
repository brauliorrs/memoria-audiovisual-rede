"""Carregadores tipados para os artefatos da infraestrutura científica."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .registry import ArtifactFormat, InfrastructureRegistry


class ArtifactState(str, Enum):
    FOUND = "found"
    EMPTY = "empty"
    MISSING = "missing"
    INVALID = "invalid"
    OUTDATED = "outdated"


@dataclass(frozen=True, slots=True)
class LoadedArtifact:
    key: str
    name: str
    path: Path
    state: ArtifactState
    payload: Any = None
    error: str = ""

    @property
    def available(self) -> bool:
        return self.state in {ArtifactState.FOUND, ArtifactState.EMPTY, ArtifactState.OUTDATED}

    @property
    def is_usable(self) -> bool:
        return self.state is ArtifactState.FOUND


class ScientificInfrastructureLoader:
    """Resolve e carrega artefatos exclusivamente pelo registro central."""

    def __init__(self, registry: InfrastructureRegistry):
        self.registry = registry

    @staticmethod
    def snapshot_directories(root: Path) -> tuple[Path, ...]:
        if not root.exists():
            return ()
        return tuple(
            sorted(
                (item for item in root.iterdir() if item.is_dir()),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
        )

    def latest_analytics_snapshot_dir(self) -> Path | None:
        snapshots = self.snapshot_directories(self.registry.analytics_root)
        return snapshots[0] if snapshots else None

    def latest_coverage_snapshot_dir(self) -> Path | None:
        snapshots = self.snapshot_directories(self.registry.coverage_root)
        return snapshots[0] if snapshots else None

    def load(self, key: str, *, snapshot_dir: Path | None = None) -> LoadedArtifact:
        spec = self.registry.get(key)
        candidates = self.registry.resolve(key, snapshot_dir=snapshot_dir)
        path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
        if not path.exists():
            return LoadedArtifact(key, spec.label, path, ArtifactState.MISSING)
        try:
            if spec.format is ArtifactFormat.JSON:
                payload = json.loads(path.read_text(encoding="utf-8"))
            elif spec.format is ArtifactFormat.JSONL:
                payload = self._read_jsonl(path)
            else:
                return LoadedArtifact(
                    key,
                    spec.label,
                    path,
                    ArtifactState.INVALID,
                    error=f"Unsupported artifact format: {spec.format}",
                )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            return LoadedArtifact(key, spec.label, path, ArtifactState.INVALID, error=str(exc))

        state = ArtifactState.EMPTY if self._is_empty(payload) else ArtifactState.FOUND
        return LoadedArtifact(key, spec.label, path, state, payload=payload)

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                item = json.loads(line)
                if isinstance(item, dict):
                    rows.append(item)
                else:
                    rows.append({"line": line_number, "value": item})
        return rows

    @staticmethod
    def _is_empty(payload: Any) -> bool:
        if payload is None:
            return True
        if isinstance(payload, (dict, list, tuple, str)):
            return len(payload) == 0
        return False

    def load_static(self) -> dict[str, LoadedArtifact]:
        return {
            key: self.load(key)
            for key in ("indicator_catalog", "methodology_registry")
        }

    def load_latest_analytics_snapshot(self) -> dict[str, LoadedArtifact]:
        snapshot_dir = self.latest_analytics_snapshot_dir()
        if snapshot_dir is None:
            return {}
        return {
            "snapshot": LoadedArtifact(
                "snapshot",
                "Snapshot analítico",
                snapshot_dir,
                ArtifactState.FOUND,
                payload={"snapshot_id": snapshot_dir.name},
            ),
            "indicators": self.load("snapshot_indicators", snapshot_dir=snapshot_dir),
            "manifest": self.load("analytics_manifest", snapshot_dir=snapshot_dir),
            "run": self.load("analytics_run", snapshot_dir=snapshot_dir),
            "sensitivity": self.load("interoperability_sensitivity", snapshot_dir=snapshot_dir),
        }

    def load_latest_coverage_snapshot(self) -> dict[str, LoadedArtifact]:
        snapshot_dir = self.latest_coverage_snapshot_dir()
        if snapshot_dir is None:
            return {}
        return {
            "snapshot": LoadedArtifact(
                "snapshot",
                "Snapshot de cobertura",
                snapshot_dir,
                ArtifactState.FOUND,
                payload={"snapshot_id": snapshot_dir.name},
            ),
            "coverage": self.load("parameter_coverage", snapshot_dir=snapshot_dir),
            "manifest": self.load("coverage_manifest", snapshot_dir=snapshot_dir),
            "changes": self.load("coverage_changes", snapshot_dir=snapshot_dir),
        }

    def load_governance(self) -> dict[str, LoadedArtifact]:
        return {
            "ledger": self.load("ledger"),
            "ingestion_batches": self.load("ingestion_batches"),
            "indicator_history": self.load("indicator_history"),
        }
