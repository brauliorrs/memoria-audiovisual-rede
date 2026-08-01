"""Projeção de entrega das publicações vigentes de infraestrutura digital.

A projeção resolve o registro operacional de ativações e produz arquivos estáveis
para consumo futuro por dashboard, API ou exportadores, sem alterar as versões
históricas que lhe deram origem.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .models import utc_now_iso


@dataclass(frozen=True, slots=True)
class DeliveryItem:
    snapshot_id: str
    publication_id: str
    publication_kind: str
    publication_revision: int | None
    source_events_path: str
    event_count: int
    content_sha256: str
    activated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DeliveryManifest:
    item_count: int
    total_event_count: int
    events_path: str
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_json_write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, newline="\n"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def build_public_delivery(
    public_root: str | Path,
    *,
    output_root: str | Path | None = None,
) -> DeliveryManifest:
    """Materializa uma projeção estável a partir de ``active_publications.json``."""
    root = Path(public_root)
    registry_path = root / "active_publications.json"
    if not registry_path.exists():
        raise FileNotFoundError(f"registro de publicações vigentes inexistente: {registry_path}")
    registry = _read_json(registry_path)
    if not isinstance(registry, Mapping):
        raise ValueError("active_publications.json deve conter um objeto por snapshot")

    destination = Path(output_root) if output_root is not None else root / "delivery"
    combined_events: list[dict[str, Any]] = []
    items: list[DeliveryItem] = []

    for snapshot_id in sorted(str(key) for key in registry):
        activation = dict(registry[snapshot_id])
        if str(activation.get("snapshot_id") or "") != snapshot_id:
            raise ValueError(f"registro vigente inconsistente para {snapshot_id}")
        source_path = Path(str(activation.get("events_path") or ""))
        if not source_path.exists():
            raise FileNotFoundError(f"eventos vigentes inexistentes: {source_path}")
        events = _read_json(source_path)
        if not isinstance(events, list):
            raise ValueError(f"eventos de {snapshot_id} devem formar uma lista")
        expected_count = int(activation.get("event_count", -1))
        if expected_count != len(events):
            raise ValueError(f"contagem divergente na publicação vigente de {snapshot_id}")

        canonical = json.dumps(events, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        publication_id = str(activation.get("publication_id") or "").strip()
        if not publication_id:
            raise ValueError(f"publication_id ausente para {snapshot_id}")

        for event in events:
            payload = dict(event)
            if str(payload.get("snapshot_id") or "") != snapshot_id:
                raise ValueError(f"evento de outro snapshot em {publication_id}")
            payload["active_publication_id"] = publication_id
            combined_events.append(payload)

        revision = activation.get("publication_revision")
        items.append(
            DeliveryItem(
                snapshot_id=snapshot_id,
                publication_id=publication_id,
                publication_kind=str(activation.get("publication_kind") or ""),
                publication_revision=int(revision) if revision is not None else None,
                source_events_path=str(source_path),
                event_count=len(events),
                content_sha256=digest,
                activated_at=str(activation.get("activated_at") or ""),
            )
        )

    events_path = destination / "events.json"
    manifest_path = destination / "manifest.json"
    _atomic_json_write(events_path, combined_events)
    manifest = DeliveryManifest(
        item_count=len(items),
        total_event_count=len(combined_events),
        events_path=str(events_path),
    )
    _atomic_json_write(
        manifest_path,
        {**manifest.to_dict(), "publications": [item.to_dict() for item in items]},
    )
    return manifest
