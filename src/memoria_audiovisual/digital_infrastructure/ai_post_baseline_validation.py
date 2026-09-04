"""Validação pós-baseline dos componentes experimentais de IA.

Este módulo calcula métricas apenas a partir de decisões humanas concluídas.
Nenhum resultado produzido aqui altera o baseline operacional oficial.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

VALID_HUMAN_LABELS = {"positive", "negative", "ambiguous", "not_assessable"}
POSITIVE_MODEL_STATUSES = {"detected_pending_review", "verified_public_evidence"}
REVIEWED_STATUSES = {"completed", "confirmed", "corrected", "rejected"}


@dataclass(frozen=True, slots=True)
class BinaryMetrics:
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int

    @property
    def precision(self) -> float | None:
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else None

    @property
    def recall(self) -> float | None:
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else None

    @property
    def f1(self) -> float | None:
        if self.precision is None or self.recall is None or self.precision + self.recall == 0:
            return None
        return 2 * self.precision * self.recall / (self.precision + self.recall)

    def to_dict(self) -> dict[str, Any]:
        return {
            "confusion_matrix": {
                "true_positive": self.true_positive,
                "false_positive": self.false_positive,
                "true_negative": self.true_negative,
                "false_negative": self.false_negative,
            },
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "evaluated": sum((self.true_positive, self.false_positive, self.true_negative, self.false_negative)),
        }


def _is_reviewed(row: Mapping[str, Any]) -> bool:
    return str(row.get("review_status") or "").strip().lower() in REVIEWED_STATUSES


def _model_positive(row: Mapping[str, Any]) -> bool:
    return str(row.get("model_status") or "") in POSITIVE_MODEL_STATUSES


def _human_positive(row: Mapping[str, Any]) -> bool:
    return str(row.get("human_label") or "").strip().lower() == "positive"


def validate_review_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, source in enumerate(rows, start=1):
        row = {str(key): value for key, value in source.items()}
        unit_id = str(row.get("review_unit_id") or "").strip()
        if not unit_id:
            raise ValueError(f"review_unit_id ausente na linha {position}")
        if unit_id in seen:
            raise ValueError(f"review_unit_id duplicado: {unit_id}")
        seen.add(unit_id)
        if _is_reviewed(row):
            label = str(row.get("human_label") or "").strip().lower()
            if label not in VALID_HUMAN_LABELS:
                raise ValueError(f"human_label inválido para {unit_id}: {label}")
            if not str(row.get("reviewer_id") or "").strip():
                raise ValueError(f"reviewer_id obrigatório para {unit_id}")
            if not str(row.get("reviewed_at") or "").strip():
                raise ValueError(f"reviewed_at obrigatório para {unit_id}")
        normalized.append(row)
    return normalized


def apply_review_amendments(
    rows: Iterable[Mapping[str, Any]],
    amendments: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Aplica emendas sem apagar a revisão original.

    A fila original permanece preservada. A projeção usada para métricas recebe a
    decisão mais recente de cada emenda válida e registra no próprio row quais
    campos foram substituídos.
    """
    data = validate_review_rows(rows)
    by_id = {str(row["review_unit_id"]): row for row in data}
    seen_amendments: set[str] = set()

    for position, source in enumerate(amendments, start=1):
        amendment = {str(key): value for key, value in source.items()}
        amendment_id = str(amendment.get("amendment_id") or "").strip()
        unit_id = str(amendment.get("review_unit_id") or "").strip()
        if not amendment_id:
            raise ValueError(f"amendment_id ausente na emenda {position}")
        if amendment_id in seen_amendments:
            raise ValueError(f"amendment_id duplicado: {amendment_id}")
        seen_amendments.add(amendment_id)
        if unit_id not in by_id:
            raise ValueError(f"emenda referencia review_unit_id inexistente: {unit_id}")

        label = str(amendment.get("human_label") or "").strip().lower()
        if label not in VALID_HUMAN_LABELS:
            raise ValueError(f"human_label inválido na emenda {amendment_id}: {label}")
        reviewer_id = str(amendment.get("reviewer_id") or "").strip()
        reviewed_at = str(amendment.get("reviewed_at") or "").strip()
        if not reviewer_id or not reviewed_at:
            raise ValueError(f"emenda {amendment_id} exige reviewer_id e reviewed_at")

        row = by_id[unit_id]
        prior_label = str(row.get("human_label") or "").strip().lower()
        declared_prior = str(amendment.get("previous_human_label") or "").strip().lower()
        if declared_prior and declared_prior != prior_label:
            raise ValueError(
                f"emenda {amendment_id} esperava label anterior {declared_prior}, encontrado {prior_label}"
            )

        row["human_label_original"] = row.get("human_label")
        row["human_decision_original"] = row.get("human_decision")
        row["reviewed_at_original"] = row.get("reviewed_at")
        row["human_label"] = label
        row["human_decision"] = amendment.get("human_decision")
        row["reviewer_id"] = reviewer_id
        row["reviewed_at"] = reviewed_at
        if amendment.get("validation_url"):
            row["validation_url"] = amendment.get("validation_url")
        row["applied_amendment_id"] = amendment_id
        row["amendment_reason"] = amendment.get("amendment_reason")
        row["temporal_relation"] = amendment.get("temporal_relation")
        row["review_status"] = "corrected"

    return data


def _binary_metrics(rows: Iterable[Mapping[str, Any]]) -> BinaryMetrics:
    tp = fp = tn = fn = 0
    for row in rows:
        if not _is_reviewed(row):
            continue
        label = str(row.get("human_label") or "").strip().lower()
        if label not in {"positive", "negative"}:
            continue
        model_positive = _model_positive(row)
        human_positive = _human_positive(row)
        if model_positive and human_positive:
            tp += 1
        elif model_positive and not human_positive:
            fp += 1
        elif not model_positive and human_positive:
            fn += 1
        else:
            tn += 1
    return BinaryMetrics(tp, fp, tn, fn)


def _group_metrics(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key) or "unknown")].append(row)
    return {name: _binary_metrics(group).to_dict() for name, group in sorted(groups.items())}


def evaluate_human_reviews(
    rows: Iterable[Mapping[str, Any]],
    *,
    amendments: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    amendment_list = list(amendments)
    data = (
        apply_review_amendments(rows, amendment_list)
        if amendment_list
        else validate_review_rows(rows)
    )
    reviewed = [row for row in data if _is_reviewed(row)]
    pending = [row for row in data if not _is_reviewed(row)]
    tasks = sorted({str(row.get("task") or "unknown") for row in data})
    task_metrics = {
        task: _binary_metrics([row for row in data if str(row.get("task")) == task]).to_dict()
        for task in tasks
    }
    return {
        "schema_version": "1.1.0",
        "stage": "t2a_post_baseline_validation",
        "official_baseline_dependency": False,
        "does_not_modify_official_baseline": True,
        "review_units_total": len(data),
        "reviewed_units": len(reviewed),
        "pending_units": len(pending),
        "amendments_applied": len(amendment_list),
        "ambiguous_or_not_assessable": sum(
            str(row.get("human_label") or "").lower() in {"ambiguous", "not_assessable"}
            for row in reviewed
        ),
        "overall": _binary_metrics(data).to_dict(),
        "by_task": task_metrics,
        "by_language": _group_metrics(data, "language_group"),
        "by_geography": _group_metrics(data, "geographic_group"),
        "by_institution_type": _group_metrics(data, "analytical_stratum"),
        "activation_decision": {
            task: "insufficient_human_review" if metrics["evaluated"] == 0 else "requires_scientific_review"
            for task, metrics in task_metrics.items()
        },
    }
