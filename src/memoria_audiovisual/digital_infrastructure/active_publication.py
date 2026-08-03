"""Registro operacional da versão pública vigente de cada snapshot."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from .models import utc_now_iso

PublicationKind = Literal["initial", "revision"]


@dataclass(frozen=True, slots=True)
class ActivePublication:
    snapshot_id: str
    publication_kind: PublicationKind
    publication_revision: int
    publication_id: str
    events_path: str
    manifest_path: str
    event_count: int
    activated_by: str
    activation_reason: str
    activated_at: str = field(default_factory=utc_now_iso)
    supersedes_publication_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ActivePublicationRegistry:
    """Mantém estado atual reconstruível e histórico append-only de ativações."""

    def __init__(self, public_root: str | Path) -> None:
        self.root = Path(public_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.current_path = self.root / "active_publications.json"
        self.history_path = self.root / "publication_activation_history.jsonl"

    def read_current(self) -> dict[str, ActivePublication]:
        if not self.current_path.exists():
            return {}
        payload = json.loads(self.current_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("active_publications.json deve conter uma lista")
        result: dict[str, ActivePublication] = {}
        for item in payload:
            record = ActivePublication(**dict(item))
            if record.snapshot_id in result:
                raise ValueError(f"snapshot duplicado no registro vigente: {record.snapshot_id}")
            result[record.snapshot_id] = record
        return result

    def activate(
        self,
        *,
        snapshot_id: str,
        publication_kind: PublicationKind,
        activated_by: str,
        activation_reason: str,
        revision_number: int | None = None,
    ) -> ActivePublication:
        if not snapshot_id.strip() or not activated_by.strip() or not activation_reason.strip():
            raise ValueError("snapshot_id, activated_by e activation_reason são obrigatórios")
        snapshot_root = self.root / snapshot_id
        if publication_kind == "initial":
            revision = 0
            publication_id = f"{snapshot_id}:initial"
            version_root = snapshot_root
        elif publication_kind == "revision":
            if revision_number is None or revision_number < 1:
                raise ValueError("revision_number deve ser maior ou igual a 1")
            revision = revision_number
            publication_id = f"{snapshot_id}:publication_revision:{revision}"
            version_root = snapshot_root / "revisions" / f"revision_{revision:04d}"
        else:
            raise ValueError(f"publication_kind inválido: {publication_kind}")

        events_path = version_root / "events.json"
        manifest_path = version_root / "manifest.json"
        if not events_path.exists() or not manifest_path.exists():
            raise FileNotFoundError(f"versão pública incompleta: {version_root}")
        events = json.loads(events_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(events, list):
            raise ValueError("events.json deve conter uma lista")
        if str(manifest.get("snapshot_id") or "") != snapshot_id:
            raise ValueError("manifesto aponta para outro snapshot")
        if int(manifest.get("event_count", -1)) != len(events):
            raise ValueError("event_count do manifesto diverge de events.json")
        if publication_kind == "revision":
            if int(manifest.get("publication_revision", 0)) != revision:
                raise ValueError("manifesto aponta para outra revisão")
            if str(manifest.get("revision_id") or "") != publication_id:
                raise ValueError("revision_id incompatível")

        current = self.read_current()
        previous = current.get(snapshot_id)
        if previous is not None and previous.publication_id == publication_id:
            raise ValueError(f"publicação já está vigente: {publication_id}")
        record = ActivePublication(
            snapshot_id=snapshot_id,
            publication_kind=publication_kind,
            publication_revision=revision,
            publication_id=publication_id,
            events_path=str(events_path),
            manifest_path=str(manifest_path),
            event_count=len(events),
            activated_by=activated_by.strip(),
            activation_reason=activation_reason.strip(),
            supersedes_publication_id=previous.publication_id if previous else None,
        )
        current[snapshot_id] = record
        ordered = [current[key].to_dict() for key in sorted(current)]
        temporary = self.current_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.current_path)
        with self.history_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return record
