"""Regeneração controlada da visão pública após revisões humanas tardias.

A coleta e a primeira visão pública de um snapshot permanecem imutáveis. Cada
regeneração cria uma revisão derivada numerada, vinculada ao snapshot e à versão
pública anterior, com justificativa e rastreabilidade das decisões utilizadas.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .event_review import LongitudinalEventReviewService
from .models import utc_now_iso
from .public_view import PublicEvent, build_public_view


@dataclass(frozen=True, slots=True)
class PublicationRevisionManifest:
    snapshot_id: str
    publication_revision: int
    revision_id: str
    supersedes_revision_id: str | None
    reason: str
    requested_by: str
    events_path: str
    event_count: int
    added_event_ids: tuple[str, ...]
    removed_event_ids: tuple[str, ...]
    changed_event_ids: tuple[str, ...]
    review_ids: tuple[str, ...]
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for name in (
            "added_event_ids",
            "removed_event_ids",
            "changed_event_ids",
            "review_ids",
        ):
            payload[name] = list(payload[name])
        return payload


def _event_map(events: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for event in events:
        payload = dict(event)
        event_id = str(payload.get("event_id") or "").strip()
        if not event_id:
            raise ValueError("evento público sem event_id")
        if event_id in result:
            raise ValueError(f"evento público duplicado: {event_id}")
        result[event_id] = payload
    return result


def compare_publications(
    previous: Iterable[Mapping[str, Any]],
    current: Iterable[PublicEvent],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Retorna eventos adicionados, removidos e alterados entre duas versões."""
    before = _event_map(previous)
    after = _event_map(item.to_dict() for item in current)
    added = tuple(sorted(set(after) - set(before)))
    removed = tuple(sorted(set(before) - set(after)))
    changed = tuple(
        sorted(event_id for event_id in set(before) & set(after) if before[event_id] != after[event_id])
    )
    return added, removed, changed


class PublicationRevisionStore:
    """Persiste revisões públicas sem alterar a versão inicial do snapshot."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "publication_revision_index.jsonl"

    def _snapshot_root(self, snapshot_id: str) -> Path:
        return self.root / snapshot_id

    def _revision_root(self, snapshot_id: str) -> Path:
        return self._snapshot_root(snapshot_id) / "revisions"

    def list_manifests(self, snapshot_id: str) -> tuple[dict[str, Any], ...]:
        revisions = self._revision_root(snapshot_id)
        if not revisions.exists():
            return ()
        manifests: list[dict[str, Any]] = []
        for path in sorted(revisions.glob("revision_*/manifest.json")):
            manifests.append(json.loads(path.read_text(encoding="utf-8")))
        return tuple(manifests)

    def latest_manifest(self, snapshot_id: str) -> dict[str, Any] | None:
        manifests = self.list_manifests(snapshot_id)
        return manifests[-1] if manifests else None

    def latest_events(self, snapshot_id: str) -> tuple[dict[str, Any], ...]:
        latest = self.latest_manifest(snapshot_id)
        if latest is not None:
            path = Path(str(latest["events_path"]))
        else:
            path = self._snapshot_root(snapshot_id) / "events.json"
        if not path.exists():
            raise FileNotFoundError(f"visão pública de origem inexistente: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("arquivo público deve conter uma lista de eventos")
        return tuple(dict(item) for item in payload)

    def write_revision(
        self,
        *,
        snapshot_id: str,
        events: Iterable[PublicEvent],
        reason: str,
        requested_by: str,
    ) -> PublicationRevisionManifest:
        if not snapshot_id.strip():
            raise ValueError("snapshot_id não pode ser vazio")
        if not reason.strip() or not requested_by.strip():
            raise ValueError("reason e requested_by são obrigatórios")
        items = tuple(events)
        if any(item.snapshot_id != snapshot_id for item in items):
            raise ValueError("a revisão contém evento de outro snapshot")

        previous = self.latest_events(snapshot_id)
        latest = self.latest_manifest(snapshot_id)
        revision_number = int(latest["publication_revision"]) + 1 if latest else 1
        revision_id = f"{snapshot_id}:publication_revision:{revision_number}"
        supersedes = str(latest["revision_id"]) if latest else None
        revision_dir = self._revision_root(snapshot_id) / f"revision_{revision_number:04d}"
        if revision_dir.exists():
            raise FileExistsError(f"revisão pública já existe: {revision_id}")
        revision_dir.mkdir(parents=True, exist_ok=False)

        events_path = revision_dir / "events.json"
        events_path.write_text(
            json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        added, removed, changed = compare_publications(previous, items)
        review_ids = tuple(
            dict.fromkeys(review_id for item in items for review_id in item.review_ids)
        )
        manifest = PublicationRevisionManifest(
            snapshot_id=snapshot_id,
            publication_revision=revision_number,
            revision_id=revision_id,
            supersedes_revision_id=supersedes,
            reason=reason.strip(),
            requested_by=requested_by.strip(),
            events_path=str(events_path),
            event_count=len(items),
            added_event_ids=added,
            removed_event_ids=removed,
            changed_event_ids=changed,
            review_ids=review_ids,
        )
        manifest_path = revision_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        with self.index_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return manifest


def regenerate_publication(
    *,
    snapshot_id: str,
    events: Iterable[Mapping[str, Any]],
    review_service: LongitudinalEventReviewService,
    store: PublicationRevisionStore,
    reason: str,
    requested_by: str,
) -> PublicationRevisionManifest:
    """Reconstrói a visão a partir dos eventos originais e do ledger atual."""
    public = build_public_view(events, review_service)
    return store.write_revision(
        snapshot_id=snapshot_id,
        events=public,
        reason=reason,
        requested_by=requested_by,
    )
