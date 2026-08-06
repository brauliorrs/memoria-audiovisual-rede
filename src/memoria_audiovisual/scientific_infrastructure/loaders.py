"""Carregadores tipados para os artefatos da infraestrutura científica."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .indicator_registry import IndicatorRegistry, validate_indicator_registry
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

        if key == "indicator_registry":
            try:
                validate_indicator_registry(payload)
            except (TypeError, ValueError) as exc:
                return LoadedArtifact(
                    key,
                    spec.label,
                    path,
                    ArtifactState.INVALID,
                    payload=payload,
                    error=str(exc),
                )

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

    @staticmethod
    def _valid_snapshot_id(value: object) -> str | None:
        snapshot_id = str(value or "").strip()
        if not snapshot_id:
            return None
        if Path(snapshot_id).name != snapshot_id:
            return None
        if snapshot_id in {".", ".."} or any(part in snapshot_id for part in ("/", "\\")):
            return None
        return snapshot_id

    def load_indicator_registry(self) -> LoadedArtifact:
        """Carrega e valida a fonte operacional única dos indicadores."""
        return self.load("indicator_registry")

    def parsed_indicator_registry(self) -> IndicatorRegistry | None:
        """Retorna o registro tipado quando o artefato canônico é válido."""
        artifact = self.load_indicator_registry()
        if artifact.state is not ArtifactState.FOUND:
            return None
        return validate_indicator_registry(artifact.payload)

    def load_static(self) -> dict[str, LoadedArtifact]:
        return {
            key: self.load(key)
            for key in (
                "indicator_registry",
                "methodology_registry",
                "indicator_results_registry",
            )
        }

    def load_latest_analytics_snapshot(self) -> dict[str, LoadedArtifact]:
        snapshot_dir = self.latest_analytics_snapshot_dir()
        if snapshot_dir is None:
            return {}
        return self._load_analytics_snapshot(snapshot_dir)

    def _load_analytics_snapshot(self, snapshot_dir: Path) -> dict[str, LoadedArtifact]:
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

    def load_operational_baseline(self) -> dict[str, LoadedArtifact]:
        """Carrega apenas o baseline apontado pelo artefato oficial `latest`.

        A ausência do ponteiro ou do diretório não é interpretada como resultado
        científico negativo. Nesses casos, o retorno preserva o estado do ponteiro
        para que a interface informe que a materialização operacional está pendente.
        """
        pointer = self.load("operational_baseline_latest")
        loaded: dict[str, LoadedArtifact] = {"pointer": pointer}
        if pointer.state is not ArtifactState.FOUND or not isinstance(pointer.payload, dict):
            return loaded

        snapshot_id = self._valid_snapshot_id(pointer.payload.get("snapshot_id"))
        if snapshot_id is None:
            loaded["pointer"] = LoadedArtifact(
                pointer.key,
                pointer.name,
                pointer.path,
                ArtifactState.INVALID,
                payload=pointer.payload,
                error="snapshot_id ausente ou inseguro no ponteiro operacional",
            )
            return loaded

        snapshot_dir = self.registry.analytics_root / snapshot_id
        if not snapshot_dir.is_dir():
            loaded["snapshot"] = LoadedArtifact(
                "snapshot",
                "Snapshot operacional",
                snapshot_dir,
                ArtifactState.MISSING,
                error="diretório do snapshot apontado não foi encontrado",
            )
            return loaded

        loaded.update(self._load_analytics_snapshot(snapshot_dir))
        loaded["snapshot"] = LoadedArtifact(
            "snapshot",
            "Baseline operacional oficial",
            snapshot_dir,
            ArtifactState.FOUND,
            payload={"snapshot_id": snapshot_id},
        )
        loaded["operational_manifest"] = self.load(
            "operational_baseline_manifest", snapshot_dir=snapshot_dir
        )
        return loaded

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
            "operational_baseline_latest": self.load("operational_baseline_latest"),
            "ledger": self.load("ledger"),
            "ingestion_batches": self.load("ingestion_batches"),
            "indicator_history": self.load("indicator_history"),
        }
