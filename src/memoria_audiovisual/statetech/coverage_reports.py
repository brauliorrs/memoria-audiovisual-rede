"""Persistência de relatórios de cobertura e comparação por snapshot.

Os relatórios são derivados das observações normalizadas. Cada snapshot é
armazenado em diretório próprio e um índice append-only permite localizar a
rodada anterior sem alterar relatórios já produzidos.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import utc_now_iso
from .parameter_coverage import ParameterCoverage, compare_coverage


@dataclass(frozen=True, slots=True)
class SnapshotCoverageManifest:
    snapshot_id: str
    coverage_path: str
    changes_path: str | None
    previous_snapshot_id: str | None
    corpus_count: int
    parameter_count: int
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CoverageReportStore:
    """Grava relatórios derivados sem substituir snapshots anteriores."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "snapshot_coverage_index.jsonl"

    def latest_manifest(self, *, exclude_snapshot_id: str | None = None) -> SnapshotCoverageManifest | None:
        latest: SnapshotCoverageManifest | None = None
        if not self.index_path.exists():
            return None
        with self.index_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"índice de cobertura inválido em {self.index_path}:{line_number}"
                    ) from exc
                if exclude_snapshot_id and payload.get("snapshot_id") == exclude_snapshot_id:
                    continue
                latest = SnapshotCoverageManifest(**payload)
        return latest

    def load_coverage(self, manifest: SnapshotCoverageManifest) -> tuple[ParameterCoverage, ...]:
        path = Path(manifest.coverage_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("relatório de cobertura deve conter uma lista")
        return tuple(
            ParameterCoverage(
                corpus_code=str(item["corpus_code"]),
                snapshot_id=str(item["snapshot_id"]),
                detector_group=str(item["detector_group"]),
                status=str(item["status"]),
                observation_count=int(item["observation_count"]),
                detected_values=tuple(item.get("detected_values", ())),
            )
            for item in payload
        )

    def write(
        self,
        *,
        snapshot_id: str,
        coverage: Iterable[ParameterCoverage],
        previous_manifest: SnapshotCoverageManifest | None = None,
    ) -> SnapshotCoverageManifest:
        if not snapshot_id.strip():
            raise ValueError("snapshot_id não pode ser vazio")
        coverage_items = tuple(coverage)
        snapshot_dir = self.root / snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        coverage_path = snapshot_dir / "parameter_coverage.json"
        changes_path = snapshot_dir / "parameter_changes.json"

        if coverage_path.exists():
            raise FileExistsError(f"relatório do snapshot já existe: {coverage_path}")

        coverage_path.write_text(
            json.dumps([item.to_dict() for item in coverage_items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        previous_snapshot_id: str | None = None
        written_changes_path: str | None = None
        if previous_manifest is not None:
            previous = self.load_coverage(previous_manifest)
            changes = compare_coverage(previous, coverage_items)
            changes_path.write_text(
                json.dumps([item.to_dict() for item in changes], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            previous_snapshot_id = previous_manifest.snapshot_id
            written_changes_path = str(changes_path)

        manifest = SnapshotCoverageManifest(
            snapshot_id=snapshot_id,
            coverage_path=str(coverage_path),
            changes_path=written_changes_path,
            previous_snapshot_id=previous_snapshot_id,
            corpus_count=len({item.corpus_code for item in coverage_items}),
            parameter_count=len(coverage_items),
        )
        with self.index_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
        return manifest


def observations_from_ingestion_payload(payload: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Extrai as observações normalizadas do resumo de preview ou ledger."""
    observations: list[dict[str, Any]] = []
    for batch in payload.get("batches", ()):
        for item in batch.get("items", ()):
            record = dict(item.get("payload", {}))
            if record.get("corpus_code") and record.get("detector_group"):
                observations.append(record)
    return tuple(observations)
