"""Política de triagem e publicação de eventos longitudinais Estado–tecnologia."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

SENSITIVE_GROUPS = {"restriction", "ai_evidence"}
DATA_QUALITY_CHANGES = {"error", "not_assessable", "still_missing", "missing_observation"}


@dataclass(frozen=True, slots=True)
class TriagedEvent:
    event_id: str
    snapshot_id: str
    corpus_code: str
    detector_group: str
    change_type: str
    triage_class: str
    severity: str
    review_required: bool
    publication_status: str
    reason_code: str
    previous_values: tuple[str, ...] = ()
    current_values: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["previous_values"] = list(self.previous_values)
        data["current_values"] = list(self.current_values)
        return data


def _event_id(item: Mapping[str, Any]) -> str:
    basis = "|".join(
        [
            str(item.get("current_snapshot_id") or item.get("snapshot_id") or ""),
            str(item.get("corpus_code") or ""),
            str(item.get("detector_group") or ""),
            str(item.get("change_type") or ""),
            json.dumps(item.get("previous_values", []), ensure_ascii=False, sort_keys=True),
            json.dumps(item.get("current_values", []), ensure_ascii=False, sort_keys=True),
        ]
    )
    return "event_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]


def triage_event(item: Mapping[str, Any]) -> TriagedEvent:
    snapshot_id = str(item.get("current_snapshot_id") or item.get("snapshot_id") or "").strip()
    corpus_code = str(item.get("corpus_code") or "").strip()
    detector_group = str(item.get("detector_group") or "").strip()
    change_type = str(item.get("change_type") or "").strip()
    if not all((snapshot_id, corpus_code, detector_group, change_type)):
        raise ValueError("evento longitudinal sem identificação completa")

    sensitive = detector_group in SENSITIVE_GROUPS
    if change_type in DATA_QUALITY_CHANGES:
        triage_class, severity, review, publication, reason = (
            "data_quality", "warning", True, "blocked", "TRIAGE-DATA-QUALITY"
        )
    elif sensitive and change_type not in {"unchanged", "baseline_created"}:
        triage_class, severity, review, publication, reason = (
            "sensitive", "high", True, "pending_review", "TRIAGE-SENSITIVE"
        )
    elif change_type == "disappeared":
        triage_class, severity, review, publication, reason = (
            "disappearance_alert", "high", True, "pending_review", "TRIAGE-DISAPPEARED"
        )
    elif change_type in {"appeared", "changed"}:
        triage_class, severity, review, publication, reason = (
            "material_change", "medium", True, "pending_review", "TRIAGE-MATERIAL-CHANGE"
        )
    elif change_type in {"unchanged", "baseline_created"}:
        triage_class, severity, review, publication, reason = (
            "routine", "info", False, "publishable", "TRIAGE-ROUTINE"
        )
    else:
        triage_class, severity, review, publication, reason = (
            "unclassified", "warning", True, "blocked", "TRIAGE-UNKNOWN"
        )

    return TriagedEvent(
        event_id=_event_id(item),
        snapshot_id=snapshot_id,
        corpus_code=corpus_code,
        detector_group=detector_group,
        change_type=change_type,
        triage_class=triage_class,
        severity=severity,
        review_required=review,
        publication_status=publication,
        reason_code=reason,
        previous_values=tuple(str(value) for value in item.get("previous_values", ())),
        current_values=tuple(str(value) for value in item.get("current_values", ())),
    )


def triage_events(items: Iterable[Mapping[str, Any]]) -> tuple[TriagedEvent, ...]:
    events = tuple(triage_event(item) for item in items)
    identifiers = [item.event_id for item in events]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("eventos longitudinais duplicados")
    return events
