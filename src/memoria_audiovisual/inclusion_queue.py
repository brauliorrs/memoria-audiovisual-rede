"""Deterministic selector for the next MAR corpus-inclusion candidates.

The selector consumes the already-versioned European research queue. It never
visits a website, never uses model predictions and never changes inclusion
criteria. It only exposes the next human/engineering work items in queue order.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import OUTPUT_DIR

EUROPE_RESEARCH_QUEUE_FILENAME = "observatorio_fila_pesquisa_europa.csv"
NEXT_INCLUSION_FILENAME = "observatorio_proximos_candidatos_inclusao.json"

_ELIGIBLE_QUEUE_LAYER = "fila_definitiva_um_por_um"
_ELIGIBLE_DECISION = "avaliar_arquivo_individual_um_por_um"
_ELIGIBLE_STATUS = "candidato_individual"


class InclusionQueueError(RuntimeError):
    """Raised when the inclusion queue is malformed or ambiguous."""


@dataclass(frozen=True)
class InclusionCandidate:
    rank: int
    unit_code: str
    unit_label: str
    country_or_scope: str
    source_family: str
    source_url: str
    next_action: str
    inclusion_gate: str
    video_location_status: str
    video_location_candidate_url: str
    evidence_reference: str
    rule_version: str

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "unit_code": self.unit_code,
            "unit_label": self.unit_label,
            "country_or_scope": self.country_or_scope,
            "source_family": self.source_family,
            "source_url": self.source_url,
            "next_action": self.next_action,
            "inclusion_gate": self.inclusion_gate,
            "video_location_status": self.video_location_status,
            "video_location_candidate_url": self.video_location_candidate_url,
            "evidence_reference": self.evidence_reference,
            "rule_version": self.rule_version,
        }


def _falsey(value: str) -> bool:
    return str(value or "").strip().lower() in {"", "false", "0", "no", "nao", "não"}


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise InclusionQueueError(f"Inclusion queue not found: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise InclusionQueueError("Could not read inclusion queue") from exc
    if not rows:
        raise InclusionQueueError("Inclusion queue is empty")
    required = {
        "unit_code", "unit_label", "source_family", "country_or_scope",
        "source_url", "organism_status", "queue_layer", "queue_decision",
        "definitive_queue_rank", "next_action", "inclusion_gate",
        "video_location_status", "video_location_candidate_url",
        "blocks_expansion", "evidence_reference", "rule_version",
    }
    missing = required.difference(rows[0])
    if missing:
        raise InclusionQueueError(
            "Inclusion queue lacks required column(s): " + ", ".join(sorted(missing))
        )
    return rows


def _candidate_from_row(row: dict[str, str]) -> InclusionCandidate:
    try:
        rank = int(str(row["definitive_queue_rank"]).strip())
    except (TypeError, ValueError) as exc:
        raise InclusionQueueError(
            f"Invalid definitive queue rank for {row.get('unit_code', '')}"
        ) from exc
    if rank <= 0:
        raise InclusionQueueError("Queue rank must be positive")
    fields = {
        key: str(row.get(key, "") or "").strip()
        for key in (
            "unit_code", "unit_label", "country_or_scope", "source_family",
            "source_url", "next_action", "inclusion_gate",
            "video_location_status", "video_location_candidate_url",
            "evidence_reference", "rule_version",
        )
    }
    if not all(fields[key] for key in ("unit_code", "unit_label", "source_url", "inclusion_gate")):
        raise InclusionQueueError(f"Incomplete inclusion candidate at rank {rank}")
    return InclusionCandidate(rank=rank, **fields)


def select_inclusion_candidates(
    rows: Iterable[dict[str, str]],
    *,
    limit: int = 1,
) -> list[InclusionCandidate]:
    if type(limit) is not int or limit <= 0:
        raise InclusionQueueError("Candidate limit must be a positive integer")
    candidates = []
    seen_codes: set[str] = set()
    seen_ranks: set[int] = set()
    for row in rows:
        if (
            str(row.get("queue_layer", "")).strip() != _ELIGIBLE_QUEUE_LAYER
            or str(row.get("queue_decision", "")).strip() != _ELIGIBLE_DECISION
            or str(row.get("organism_status", "")).strip() != _ELIGIBLE_STATUS
            or not _falsey(row.get("blocks_expansion", ""))
        ):
            continue
        candidate = _candidate_from_row(row)
        if candidate.unit_code in seen_codes:
            raise InclusionQueueError(f"Duplicate candidate code: {candidate.unit_code}")
        if candidate.rank in seen_ranks:
            raise InclusionQueueError(f"Duplicate definitive queue rank: {candidate.rank}")
        seen_codes.add(candidate.unit_code)
        seen_ranks.add(candidate.rank)
        candidates.append(candidate)
    candidates.sort(key=lambda item: (item.rank, item.unit_code))
    return candidates[:limit]


def next_inclusion_candidates(
    *,
    output_dir: Path = OUTPUT_DIR,
    limit: int = 3,
) -> list[InclusionCandidate]:
    rows = _read_rows(Path(output_dir) / EUROPE_RESEARCH_QUEUE_FILENAME)
    return select_inclusion_candidates(rows, limit=limit)


def write_next_inclusion_candidates(
    *,
    output_dir: Path = OUTPUT_DIR,
    limit: int = 3,
) -> dict:
    output_dir = Path(output_dir)
    candidates = next_inclusion_candidates(output_dir=output_dir, limit=limit)
    payload = {
        "schema_version": "1.0.0",
        "source_queue": EUROPE_RESEARCH_QUEUE_FILENAME,
        "selection_rule": (
            "queue_layer=fila_definitiva_um_por_um; "
            "queue_decision=avaliar_arquivo_individual_um_por_um; "
            "organism_status=candidato_individual; blocks_expansion=false; "
            "ascending definitive_queue_rank"
        ),
        "automatic_incorporation_authorized": False,
        "candidate_count": len(candidates),
        "candidates": [candidate.to_dict() for candidate in candidates],
        "note": (
            "This file schedules engineering/research work only. A candidate enters "
            "the active corpus only after its existing inclusion_gate is satisfied "
            "and its dedicated pipeline/checks are reviewed."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / NEXT_INCLUSION_FILENAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload
