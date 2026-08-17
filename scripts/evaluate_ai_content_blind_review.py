#!/usr/bin/env python3
"""Compara previsões cegas de IA no conteúdo com a revisão humana independente."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

POSITIVE_CLASSES = {
    "ai_assisted_production",
    "materially_ai_modified",
    "partially_synthetic",
    "fully_synthetic",
}
EVALUABLE_NEGATIVE = "no_verified_ai_evidence"
NOT_ASSESSABLE = "not_assessable"


def _load_jsonl_latest(path: Path) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    records: list[dict[str, object]] = []
    latest: dict[str, dict[str, object]] = {}
    if not path.exists():
        return records, latest
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        unit_id = str(row.get("review_unit_id") or "").strip()
        if not unit_id:
            raise ValueError("registro humano sem review_unit_id")
        records.append(row)
        latest[unit_id] = row
    return records, latest


def evaluate_blind_review(
    *,
    queue: dict[str, object],
    human_records: list[dict[str, object]],
    human_latest: dict[str, dict[str, object]],
    predictions: dict[str, object],
) -> dict[str, object]:
    units = queue.get("units")
    predicted_rows = predictions.get("predictions")
    if not isinstance(units, list) or not isinstance(predicted_rows, list):
        raise ValueError("fila ou previsões sem units válidas")

    prediction_by_id = {
        str(row["review_unit_id"]): row
        for row in predicted_rows
        if isinstance(row, dict) and row.get("review_unit_id")
    }

    confusion = {
        "true_positive": 0,
        "false_positive": 0,
        "true_negative": 0,
        "false_negative": 0,
    }
    exact_matches = 0
    evaluated = 0
    not_assessable = 0
    human_positive = 0
    human_negative = 0
    comparison_rows: list[dict[str, object]] = []
    pending: list[str] = []

    for unit in units:
        if not isinstance(unit, dict):
            continue
        unit_id = str(unit.get("review_unit_id") or "")
        human = human_latest.get(unit_id)
        prediction = prediction_by_id.get(unit_id)
        if human is None or prediction is None:
            pending.append(unit_id)
            continue

        human_label = str(human.get("human_label") or "")
        predicted_class = str(prediction.get("predicted_usage_class") or "")
        predicted_positive = bool(prediction.get("predicted_positive"))
        exact_match = human_label == predicted_class
        exact_matches += int(exact_match)

        row: dict[str, object] = {
            "review_unit_id": unit_id,
            "human_label": human_label,
            "predicted_usage_class": predicted_class,
            "predicted_positive": predicted_positive,
            "exact_class_match": exact_match,
        }

        if human_label == NOT_ASSESSABLE:
            not_assessable += 1
            row["binary_comparison"] = "excluded_not_assessable"
            comparison_rows.append(row)
            continue
        if human_label not in POSITIVE_CLASSES | {EVALUABLE_NEGATIVE}:
            raise ValueError(f"rótulo humano desconhecido: {human_label}")

        actual_positive = human_label in POSITIVE_CLASSES
        human_positive += int(actual_positive)
        human_negative += int(not actual_positive)
        evaluated += 1
        if actual_positive and predicted_positive:
            confusion["true_positive"] += 1
            row["binary_comparison"] = "true_positive"
        elif actual_positive and not predicted_positive:
            confusion["false_negative"] += 1
            row["binary_comparison"] = "false_negative"
        elif not actual_positive and predicted_positive:
            confusion["false_positive"] += 1
            row["binary_comparison"] = "false_positive"
        else:
            confusion["true_negative"] += 1
            row["binary_comparison"] = "true_negative"
        comparison_rows.append(row)

    tp = confusion["true_positive"]
    fp = confusion["false_positive"]
    tn = confusion["true_negative"]
    fn = confusion["false_negative"]
    accuracy = (tp + tn) / evaluated if evaluated else None
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall)
        else None
    )
    exact_class_accuracy = exact_matches / len(comparison_rows) if comparison_rows else None

    negative_only = evaluated > 0 and human_positive == 0
    status = "incomplete" if pending else (
        "completed_negative_only_challenge_sample" if negative_only else "completed"
    )

    return {
        "schema_version": "1.0.0",
        "report_id": "ai-content-blind-comparison-v1",
        "queue_id": queue.get("queue_id"),
        "prediction_set_id": predictions.get("prediction_set_id"),
        "assessment_stage": predictions.get("assessment_stage"),
        "status": status,
        "is_prevalence_sample": bool(queue.get("is_prevalence_sample", False)),
        "review_records_total": len(human_records),
        "latest_human_reviews": len(human_latest),
        "queue_units_total": len(units),
        "compared_units": len(comparison_rows),
        "pending_units": len(pending),
        "pending_review_unit_ids": pending,
        "human_positive": human_positive,
        "human_negative": human_negative,
        "not_assessable": not_assessable,
        "binary": {
            "evaluated": evaluated,
            "confusion_matrix": confusion,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        },
        "exact_class_accuracy": exact_class_accuracy,
        "scientific_interpretation": {
            "zero_divergences": fp == 0 and fn == 0,
            "negative_only_real_corpus_sample": negative_only,
            "supports_specificity_on_observed_negatives": negative_only and fp == 0,
            "positive_recall_estimable_from_this_sample": human_positive > 0,
            "prevalence_estimable_from_this_sample": bool(queue.get("is_prevalence_sample", False)),
            "next_requirement": (
                "blind_positive_challenge_extension"
                if negative_only
                else "scientific_review_of_error_profile"
            ),
        },
        "comparisons": comparison_rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--human-reviews", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-complete", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    predictions = json.loads(args.predictions.read_text(encoding="utf-8"))
    human_records, human_latest = _load_jsonl_latest(args.human_reviews)
    report = evaluate_blind_review(
        queue=queue,
        human_records=human_records,
        human_latest=human_latest,
        predictions=predictions,
    )
    if args.require_complete and report["pending_units"]:
        raise SystemExit("revisão cega de conteúdo ainda possui unidades pendentes")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
