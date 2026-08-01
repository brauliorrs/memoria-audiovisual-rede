"""Geração conservadora da visão pública derivada dos eventos longitudinais.

A visão pública não publica páginas nem envia alertas. Ela produz um conjunto
derivado, versionado e rastreável contendo somente eventos rotineiros elegíveis
ou eventos que alcançaram o quórum humano exigido.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .event_review import LongitudinalEventReviewService
from .models import utc_now_iso


@dataclass(frozen=True, slots=True)
class PublicEvent:
    event_id: str
    snapshot_id: str
    corpus_code: str
    detector_group: str
    change_type: str
    effective_class: str
    statement: str
    publication_basis: str
    previous_values: tuple[str, ...]
    current_values: tuple[str, ...]
    review_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for name in ("previous_values", "current_values", "review_ids", "evidence_ids"):
            payload[name] = list(payload[name])
        return payload


@dataclass(frozen=True, slots=True)
class PublicViewManifest:
    snapshot_id: str
    events_path: str
    event_count: int
    routine_count: int
    reviewed_count: int
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _values_text(values: tuple[str, ...]) -> str:
    cleaned = tuple(item for item in values if item.strip())
    return ", ".join(cleaned) if cleaned else "nenhum valor específico"


def _statement(event: Mapping[str, Any], effective_class: str) -> str:
    corpus = str(event.get("corpus_code") or "corpus")
    group = str(event.get("detector_group") or "parâmetro")
    change = str(event.get("change_type") or "")
    previous = tuple(str(item) for item in event.get("previous_values", ()))
    current = tuple(str(item) for item in event.get("current_values", ()))

    if change == "baseline_created":
        return f"Foi estabelecida uma linha de base para {group} no corpus {corpus}."
    if change == "unchanged":
        return f"Não foi identificada mudança em {group} no corpus {corpus} nesta rodada."
    if change == "appeared":
        return (
            f"A rodada identificou novo sinal de {group} no corpus {corpus}: "
            f"{_values_text(current)}."
        )
    if change == "changed":
        return (
            f"A rodada identificou alteração em {group} no corpus {corpus}, de "
            f"{_values_text(previous)} para {_values_text(current)}."
        )
    if change == "disappeared":
        return (
            f"Após revisão humana, o sinal anteriormente observado para {group} no corpus "
            f"{corpus} não foi identificado nesta rodada. Isso não comprova eliminação "
            "definitiva do recurso ou da informação."
        )
    return (
        f"Foi registrada uma mudança revisada em {group} no corpus {corpus}, "
        f"classificada como {effective_class}."
    )


def build_public_view(
    events: Iterable[Mapping[str, Any]],
    review_service: LongitudinalEventReviewService,
) -> tuple[PublicEvent, ...]:
    """Seleciona somente eventos elegíveis e acrescenta rastreabilidade humana."""
    public: list[PublicEvent] = []
    seen: set[str] = set()
    for raw_event in events:
        event = dict(raw_event)
        event_id = str(event.get("event_id") or "").strip()
        if not event_id:
            raise ValueError("evento sem event_id")
        if event_id in seen:
            raise ValueError(f"evento duplicado na visão pública: {event_id}")
        seen.add(event_id)

        routine = (
            event.get("triage_class") == "routine"
            and event.get("publication_status") == "publishable"
            and not bool(event.get("review_required"))
        )
        approved = None if routine else review_service.approved_for_public_view(event)
        if not routine and approved is None:
            continue

        source = event if routine else approved
        assert source is not None
        effective_class = str(source.get("triage_class") or "unclassified")
        reviews = review_service.reviews_for(event_id) if not routine else ()
        active_review_ids = tuple(item.review_id for item in reviews)
        evidence_ids = tuple(
            dict.fromkeys(
                evidence_id
                for review in reviews
                if review.decision == "confirmed"
                for evidence_id in review.evidence_ids
            )
        )
        public.append(
            PublicEvent(
                event_id=event_id,
                snapshot_id=str(source.get("snapshot_id") or ""),
                corpus_code=str(source.get("corpus_code") or ""),
                detector_group=str(source.get("detector_group") or ""),
                change_type=str(source.get("change_type") or ""),
                effective_class=effective_class,
                statement=_statement(source, effective_class),
                publication_basis="automatic_routine" if routine else "human_review_quorum",
                previous_values=tuple(str(item) for item in source.get("previous_values", ())),
                current_values=tuple(str(item) for item in source.get("current_values", ())),
                review_ids=active_review_ids,
                evidence_ids=evidence_ids,
            )
        )
    return tuple(public)


class PublicViewStore:
    """Persiste visões derivadas sem sobrescrever versões anteriores."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "public_view_index.jsonl"

    def write(self, snapshot_id: str, events: Iterable[PublicEvent]) -> PublicViewManifest:
        if not snapshot_id.strip():
            raise ValueError("snapshot_id não pode ser vazio")
        items = tuple(events)
        if any(item.snapshot_id != snapshot_id for item in items):
            raise ValueError("a visão contém evento de outro snapshot")
        snapshot_dir = self.root / snapshot_id
        events_path = snapshot_dir / "events.json"
        manifest_path = snapshot_dir / "manifest.json"
        if events_path.exists() or manifest_path.exists():
            raise FileExistsError(f"visão pública já existe para {snapshot_id}")
        snapshot_dir.mkdir(parents=True, exist_ok=False)
        events_path.write_text(
            json.dumps([item.to_dict() for item in items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        manifest = PublicViewManifest(
            snapshot_id=snapshot_id,
            events_path=str(events_path),
            event_count=len(items),
            routine_count=sum(item.publication_basis == "automatic_routine" for item in items),
            reviewed_count=sum(item.publication_basis == "human_review_quorum" for item in items),
        )
        manifest_path.write_text(
            json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        with self.index_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
        return manifest
