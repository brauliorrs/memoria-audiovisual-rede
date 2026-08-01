"""Cobertura explícita dos parâmetros Estado–tecnologia por corpus e snapshot.

A matriz distingue parâmetro não detectado, não avaliável, erro e detecção
positiva. Isso evita interpretar ausência de registro como ausência da variável.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

EXPECTED_DETECTOR_GROUPS = (
    "technology",
    "api_service",
    "metadata_format",
    "interoperability",
    "search",
    "restriction",
    "ai_evidence",
)


@dataclass(frozen=True, slots=True)
class ParameterCoverage:
    corpus_code: str
    snapshot_id: str
    detector_group: str
    status: str
    observation_count: int
    detected_values: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["detected_values"] = list(self.detected_values)
        return data


@dataclass(frozen=True, slots=True)
class CoverageComparison:
    corpus_code: str
    detector_group: str
    previous_snapshot_id: str | None
    current_snapshot_id: str
    change_type: str
    previous_values: tuple[str, ...]
    current_values: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["previous_values"] = list(self.previous_values)
        data["current_values"] = list(self.current_values)
        return data


def build_coverage_matrix(
    observations: Iterable[Mapping[str, Any]],
    *,
    corpus_code: str,
    snapshot_id: str,
) -> tuple[ParameterCoverage, ...]:
    grouped: dict[str, list[Mapping[str, Any]]] = {name: [] for name in EXPECTED_DETECTOR_GROUPS}
    for observation in observations:
        if str(observation.get("corpus_code") or "") != corpus_code:
            continue
        if str(observation.get("snapshot_id") or "") != snapshot_id:
            continue
        group = str(observation.get("detector_group") or "")
        if group in grouped:
            grouped[group].append(observation)

    result: list[ParameterCoverage] = []
    for group in EXPECTED_DETECTOR_GROUPS:
        items = grouped[group]
        statuses = {str(item.get("detection_status") or "unknown") for item in items}
        values = tuple(sorted({
            str(item.get("detected_value") or "").strip()
            for item in items
            if str(item.get("detection_status") or "") == "detected"
            and str(item.get("detected_value") or "").strip()
        }))
        if not items:
            status = "missing_observation"
        elif "detected" in statuses:
            status = "detected"
        elif "error" in statuses:
            status = "error"
        elif "not_assessable" in statuses:
            status = "not_assessable"
        elif "not_detected" in statuses:
            status = "not_detected"
        else:
            status = "unknown"
        result.append(ParameterCoverage(
            corpus_code=corpus_code,
            snapshot_id=snapshot_id,
            detector_group=group,
            status=status,
            observation_count=len(items),
            detected_values=values,
        ))
    return tuple(result)


def compare_coverage(
    previous: Iterable[ParameterCoverage],
    current: Iterable[ParameterCoverage],
) -> tuple[CoverageComparison, ...]:
    previous_map = {(item.corpus_code, item.detector_group): item for item in previous}
    comparisons: list[CoverageComparison] = []
    for item in current:
        old = previous_map.get((item.corpus_code, item.detector_group))
        old_values = old.detected_values if old else ()
        new_values = item.detected_values
        if old is None or old.status == "missing_observation":
            change = "baseline_created" if item.status != "missing_observation" else "still_missing"
        elif item.status in {"error", "not_assessable", "missing_observation"}:
            change = item.status
        elif old_values == new_values:
            change = "unchanged"
        elif old_values and not new_values:
            change = "disappeared"
        elif not old_values and new_values:
            change = "appeared"
        else:
            change = "changed"
        comparisons.append(CoverageComparison(
            corpus_code=item.corpus_code,
            detector_group=item.detector_group,
            previous_snapshot_id=old.snapshot_id if old else None,
            current_snapshot_id=item.snapshot_id,
            change_type=change,
            previous_values=old_values,
            current_values=new_values,
        ))
    return tuple(comparisons)
