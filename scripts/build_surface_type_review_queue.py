#!/usr/bin/env python3
"""Gera previsões e fila cega para validar a tipagem de superfícies do MAR."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from memoria_audiovisual.digital_infrastructure.surface_typing import (
    SURFACE_TYPES,
    SURFACE_TYPING_PROTOCOL_VERSION,
    classify_surface_mapping,
)

DEFAULT_ARTIFACT_ID = "mar-surface-type-predictions-v2"
DEFAULT_QUEUE_ID = "mar-surface-type-review-v2"
DEFAULT_STAGE = "t2a_mar_surface_typing_validation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/output/_ai_surface_discovery"),
    )
    parser.add_argument(
        "--predictions-output",
        type=Path,
        default=Path(
            "data/digital_infrastructure/ai_experiments/mar_surface_type_predictions_v2.json"
        ),
    )
    parser.add_argument(
        "--review-output",
        type=Path,
        default=Path(
            "data/digital_infrastructure/ai_experiments/mar_surface_type_review_queue_v2.json"
        ),
    )
    parser.add_argument("--max-units", type=int, default=60)
    parser.add_argument(
        "--max-units-per-entity",
        type=int,
        default=None,
        help=(
            "optional cap per entity; useful for balanced independent samples so "
            "a global cap cannot be exhausted by early entities"
        ),
    )
    parser.add_argument("--exclude-urls-file", type=Path)
    parser.add_argument("--artifact-id", default=DEFAULT_ARTIFACT_ID)
    parser.add_argument("--queue-id", default=DEFAULT_QUEUE_ID)
    parser.add_argument("--stage", default=DEFAULT_STAGE)
    parser.add_argument("--sample-role", default="unspecified")
    parser.add_argument("--independent-validation-sample", action="store_true")
    return parser.parse_args()


def _stable_review_id(entity_id: str, root_url: str, page_url: str) -> str:
    digest = hashlib.sha256(
        f"{entity_id}\n{root_url}\n{page_url}".encode("utf-8")
    ).hexdigest()[:16]
    return f"{entity_id}-surface-{digest}"


def _iter_reports(input_root: Path) -> Iterable[tuple[Path, dict[str, object]]]:
    if not input_root.exists():
        return
    for path in sorted(input_root.rglob("surface_discovery_report.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            yield path, payload


def _load_excluded_urls(path: Path | None) -> set[str]:
    if path is None:
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return {str(value).strip() for value in payload if str(value).strip()}
    if not isinstance(payload, dict):
        raise ValueError("exclude URL file must contain a JSON object or list")

    values = payload.get("urls")
    if isinstance(values, list):
        return {str(value).strip() for value in values if str(value).strip()}

    units = payload.get("units")
    if isinstance(units, list):
        excluded: set[str] = set()
        for unit in units:
            if not isinstance(unit, dict):
                continue
            value = str(unit.get("url") or unit.get("page_url") or "").strip()
            if value:
                excluded.add(value)
        return excluded

    raise ValueError("exclude URL object must provide urls[] or units[]")


def build_surface_type_artifacts(
    input_root: Path,
    *,
    max_units: int = 60,
    max_units_per_entity: int | None = None,
    exclude_page_urls: set[str] | None = None,
    artifact_id: str = DEFAULT_ARTIFACT_ID,
    queue_id: str = DEFAULT_QUEUE_ID,
    stage: str = DEFAULT_STAGE,
    sample_role: str = "unspecified",
    is_independent_validation_sample: bool = False,
) -> tuple[dict[str, object], dict[str, object]]:
    predictions: list[dict[str, object]] = []
    review_units: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    excluded_urls = exclude_page_urls or set()
    excluded_matches = 0
    selected_by_entity: dict[str, int] = {}

    for path, report in _iter_reports(input_root):
        root_url = str(report.get("root_url") or "")
        if not root_url:
            continue
        try:
            relative = path.relative_to(input_root)
            entity_id = relative.parts[-2] if len(relative.parts) >= 2 else "unknown"
        except ValueError:
            entity_id = "unknown"
        pages = report.get("pages")
        if not isinstance(pages, list):
            continue

        for page in pages:
            if (
                max_units_per_entity is not None
                and selected_by_entity.get(entity_id, 0) >= max_units_per_entity
            ):
                break
            if not isinstance(page, dict):
                continue
            page_url = str(page.get("url") or "")
            if not page_url:
                continue
            if page_url in excluded_urls:
                excluded_matches += 1
                continue
            dedupe = (entity_id, page_url)
            if dedupe in seen:
                continue
            seen.add(dedupe)

            review_unit_id = _stable_review_id(entity_id, root_url, page_url)
            decision = classify_surface_mapping(page, root_url=root_url)
            predictions.append(
                {
                    "review_unit_id": review_unit_id,
                    "entity_id": entity_id,
                    "root_url": root_url,
                    "page_url": page_url,
                    "predicted_surface_type": decision.surface_type,
                    "prediction_confidence": decision.confidence,
                    "prediction_evidence": list(decision.evidence),
                    "predicted_item_level": decision.is_item_level,
                    "predicted_access_state": decision.access_state,
                    "predicted_access_evidence": list(decision.access_evidence),
                }
            )
            review_units.append(
                {
                    "review_unit_id": review_unit_id,
                    "entity_id": entity_id,
                    "root_url": root_url,
                    "page_url": page_url,
                    "parent_url": page.get("parent_url"),
                    "depth": page.get("depth"),
                    "title": page.get("title"),
                    "fetch_status": page.get("fetch_status"),
                    "content_type": page.get("content_type"),
                    "media_urls": page.get("media_urls") or [],
                    "collector_access_state": decision.access_state,
                    "model_prediction_blinded": True,
                    "human_surface_type": None,
                    "human_is_item_level": None,
                    "human_access_state": None,
                    "human_review_note": None,
                    "review_status": "pending",
                }
            )
            selected_by_entity[entity_id] = selected_by_entity.get(entity_id, 0) + 1
            if len(review_units) >= max_units:
                break
        if len(review_units) >= max_units:
            break

    shared_metadata = {
        "protocol_version": SURFACE_TYPING_PROTOCOL_VERSION,
        "sample_role": sample_role,
        "is_independent_validation_sample": is_independent_validation_sample,
        "excluded_reference_urls_total": len(excluded_urls),
        "excluded_observed_matches": excluded_matches,
        "max_units_per_entity": max_units_per_entity,
        "selected_units_by_entity": dict(sorted(selected_by_entity.items())),
        "does_not_modify_official_baseline": True,
    }
    predictions_payload: dict[str, object] = {
        "schema_version": "2.0.0",
        "artifact_id": artifact_id,
        "task": "mar_surface_type_classification",
        "status": "ready" if predictions else "no_inputs_found",
        "is_scientific_result": False,
        "classes": list(SURFACE_TYPES),
        "units_total": len(predictions),
        "units": predictions,
        **shared_metadata,
    }
    review_payload: dict[str, object] = {
        "schema_version": "2.0.0",
        "queue_id": queue_id,
        "stage": stage,
        "status": "pending_human_review" if review_units else "no_inputs_found",
        "model_prediction_blinded": True,
        "is_prevalence_sample": False,
        "classes": list(SURFACE_TYPES),
        "decision_rule": (
            "human reviewer classifies the observable page type without seeing the "
            "automatic prediction; item-level means only item_record or audiovisual_item; "
            "surface role and access state are independent dimensions"
        ),
        "units_total": len(review_units),
        "units": review_units,
        **shared_metadata,
    }
    return predictions_payload, review_payload


def main() -> int:
    args = parse_args()
    excluded_urls = _load_excluded_urls(args.exclude_urls_file)
    predictions, review = build_surface_type_artifacts(
        args.input_root,
        max_units=args.max_units,
        max_units_per_entity=args.max_units_per_entity,
        exclude_page_urls=excluded_urls,
        artifact_id=args.artifact_id,
        queue_id=args.queue_id,
        stage=args.stage,
        sample_role=args.sample_role,
        is_independent_validation_sample=args.independent_validation_sample,
    )
    args.predictions_output.parent.mkdir(parents=True, exist_ok=True)
    args.review_output.parent.mkdir(parents=True, exist_ok=True)
    args.predictions_output.write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.review_output.write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "protocol_version": SURFACE_TYPING_PROTOCOL_VERSION,
                "sample_role": args.sample_role,
                "is_independent_validation_sample": args.independent_validation_sample,
                "predictions_status": predictions["status"],
                "review_status": review["status"],
                "units_total": review["units_total"],
                "excluded_reference_urls_total": review["excluded_reference_urls_total"],
                "excluded_observed_matches": review["excluded_observed_matches"],
                "max_units_per_entity": review["max_units_per_entity"],
                "selected_units_by_entity": review["selected_units_by_entity"],
                "predictions_output": str(args.predictions_output),
                "review_output": str(args.review_output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
