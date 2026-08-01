"""Entrada e saída de filas e decisões curatoriais em CSV ou JSON."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from .curatorial_review import CuratorialReview, CuratorialReviewService

REVIEW_FIELDS = (
    "observation_id", "reviewer_id", "reviewer_role", "decision", "justification",
    "evidence_ids", "conflict_of_interest_status", "reviewed_at", "supersedes_review_id",
)


def export_review_queue(
    service: CuratorialReviewService,
    observations: Iterable[Mapping[str, Any]],
    destination: str | Path,
    *,
    include_reviewed: bool = False,
) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(item) for item in service.export_queue(observations, include_reviewed=include_reviewed)]
    if path.suffix.casefold() == ".json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
    if path.suffix.casefold() != ".csv":
        raise ValueError("a fila deve ser exportada como .csv ou .json")
    fieldnames = list(rows[0].keys()) if rows else [
        "observation_id", "corpus_code", "institution_name", "detector_group",
        "detected_value", "automatic_confidence", "evidence_url", "current_status",
        "sensitive", "required_confirmations",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def import_review_decisions(
    service: CuratorialReviewService,
    source: str | Path,
) -> tuple[CuratorialReview, ...]:
    path = Path(source)
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("o JSON de decisões deve conter uma lista")
        rows = [dict(item) for item in payload]
    elif path.suffix.casefold() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [dict(item) for item in csv.DictReader(handle)]
    else:
        raise ValueError("as decisões devem ser importadas de .csv ou .json")

    reviews: list[CuratorialReview] = []
    for position, row in enumerate(rows, start=1):
        missing = [name for name in ("observation_id", "reviewer_id", "reviewer_role", "decision", "justification") if not str(row.get(name) or "").strip()]
        if missing:
            raise ValueError(f"linha {position}: campos obrigatórios ausentes: {', '.join(missing)}")
        raw_evidence = row.get("evidence_ids", ())
        if isinstance(raw_evidence, str):
            evidence_ids = tuple(item.strip() for item in raw_evidence.replace(";", "|").split("|") if item.strip())
        else:
            evidence_ids = tuple(str(item).strip() for item in raw_evidence if str(item).strip())
        review = CuratorialReview(
            observation_id=str(row["observation_id"]).strip(),
            reviewer_id=str(row["reviewer_id"]).strip(),
            reviewer_role=str(row["reviewer_role"]).strip(),
            decision=str(row["decision"]).strip(),  # type: ignore[arg-type]
            justification=str(row["justification"]).strip(),
            evidence_ids=evidence_ids,
            conflict_of_interest_status=str(row.get("conflict_of_interest_status") or "none_declared").strip(),
            reviewed_at=str(row.get("reviewed_at") or "").strip() or None,  # type: ignore[arg-type]
            supersedes_review_id=str(row.get("supersedes_review_id") or "").strip() or None,
        )
        service.register(review)
        reviews.append(review)
    return tuple(reviews)
