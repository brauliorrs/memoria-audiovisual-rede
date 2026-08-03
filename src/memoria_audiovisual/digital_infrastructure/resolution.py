"""Resolução conservadora de entidades, aliases e possíveis duplicidades."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from .ledger import AtomicLedger


def normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_marks).strip()


@dataclass(frozen=True, slots=True)
class DuplicateCandidate:
    entity_id: str
    candidate_entity_id: str
    similarity: float
    reason: str


class EntityResolver:
    """Resolve aliases explícitos e sugere duplicidades sem fundir registros automaticamente."""

    def __init__(self, ledger: AtomicLedger) -> None:
        self.ledger = ledger

    def alias_map(self) -> dict[tuple[str, str], str]:
        aliases: dict[tuple[str, str], str] = {}
        for entry in self.ledger.read_all():
            for envelope in entry.records:
                if envelope.get("record_type") != "entity_alias":
                    continue
                payload = envelope.get("payload", {})
                key = (str(payload["entity_type"]), normalize_label(str(payload["alias"])))
                aliases[key] = str(payload["entity_id"])
        return aliases

    def register_alias(
        self,
        *,
        entity_type: str,
        entity_id: str,
        alias: str,
        source: str,
        reviewed_by: str,
    ) -> str:
        normalized = normalize_label(alias)
        if not normalized:
            raise ValueError("alias vazio após normalização")
        current = self.alias_map().get((entity_type, normalized))
        if current is not None and current != entity_id:
            raise ValueError(f"alias já associado a outra entidade: {current}")
        entry = self.ledger.append(
            [
                {
                    "record_type": "entity_alias",
                    "payload": {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "alias": alias,
                        "normalized_alias": normalized,
                        "source": source,
                        "reviewed_by": reviewed_by,
                    },
                }
            ]
        )
        return entry.transaction_id

    def resolve(self, entity_type: str, label: str) -> str | None:
        return self.alias_map().get((entity_type, normalize_label(label)))

    def duplicate_candidates(
        self,
        *,
        entity_type: str,
        entity_id: str,
        label: str,
        threshold: float = 0.88,
    ) -> tuple[DuplicateCandidate, ...]:
        target = normalize_label(label)
        if not target:
            return ()
        candidates: list[DuplicateCandidate] = []
        seen: set[str] = set()
        for entry in self.ledger.read_all():
            for envelope in entry.records:
                if envelope.get("record_type") != "entity_alias":
                    continue
                payload: dict[str, Any] = envelope.get("payload", {})
                if payload.get("entity_type") != entity_type:
                    continue
                candidate_id = str(payload.get("entity_id"))
                if candidate_id == entity_id or candidate_id in seen:
                    continue
                candidate_label = str(payload.get("normalized_alias") or normalize_label(str(payload.get("alias", ""))))
                score = SequenceMatcher(None, target, candidate_label).ratio()
                if score >= threshold:
                    candidates.append(
                        DuplicateCandidate(
                            entity_id=entity_id,
                            candidate_entity_id=candidate_id,
                            similarity=round(score, 4),
                            reason="similaridade lexical entre aliases curados",
                        )
                    )
                    seen.add(candidate_id)
        return tuple(sorted(candidates, key=lambda item: item.similarity, reverse=True))
