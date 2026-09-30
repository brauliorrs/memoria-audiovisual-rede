"""Fail-closed production registry for MAR analysis instruments.

Corpus ingestion is intentionally independent from this module. Only instruments
admitted as production in the versioned registry can run through this executor.
Experimental classifiers must use their own development/validation workflows.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Iterable

from .config import OUTPUT_DIR

ROOT_DIR = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT_DIR / "docs" / "methodology" / "analysis-instrument-registry.json"
RUN_MANIFEST_FILENAME = "observatorio_execucao_instrumentos_analise.json"
_ALLOWED_LIFECYCLES = {"production", "evidence_capture_only", "experimental"}


class InstrumentRegistryError(RuntimeError):
    """Raised when production analysis admission cannot be proved."""


@dataclass(frozen=True)
class InstrumentSpec:
    instrument_id: str
    label: str
    kind: str
    lifecycle: str
    version: str
    default_cycle: bool
    runner: str
    depends_on: tuple[str, ...]
    validation_status: str
    efficacy_document: str
    tests: tuple[str, ...]
    outputs: tuple[str, ...]
    may_infer: str
    must_not_infer: str


def _utcnow() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_raw_registry(path: Path = REGISTRY_PATH) -> dict:
    if not path.is_file():
        raise InstrumentRegistryError(f"Instrument registry not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstrumentRegistryError("Instrument registry is unreadable") from exc
    if not isinstance(payload, dict):
        raise InstrumentRegistryError("Instrument registry must be a JSON object")
    return payload


def _as_spec(row: dict) -> InstrumentSpec:
    required = {
        "id", "label", "kind", "lifecycle", "version", "default_cycle",
        "runner", "depends_on", "validation_status", "efficacy_document",
        "tests", "outputs", "may_infer", "must_not_infer",
    }
    if not isinstance(row, dict) or set(row) != required:
        raise InstrumentRegistryError("Instrument registry row has unexpected fields")
    if (
        not all(isinstance(row[key], str) and row[key].strip() for key in (
            "id", "label", "kind", "lifecycle", "version", "runner",
            "validation_status", "efficacy_document", "may_infer",
            "must_not_infer",
        ))
        or type(row["default_cycle"]) is not bool
        or not isinstance(row["depends_on"], list)
        or not all(isinstance(value, str) and value for value in row["depends_on"])
        or not isinstance(row["tests"], list)
        or not all(isinstance(value, str) and value for value in row["tests"])
        or not isinstance(row["outputs"], list)
        or not all(isinstance(value, str) and value for value in row["outputs"])
    ):
        raise InstrumentRegistryError("Instrument registry row contains invalid values")
    if row["lifecycle"] not in _ALLOWED_LIFECYCLES:
        raise InstrumentRegistryError(f"Unknown lifecycle: {row['lifecycle']}")
    return InstrumentSpec(
        instrument_id=row["id"],
        label=row["label"],
        kind=row["kind"],
        lifecycle=row["lifecycle"],
        version=row["version"],
        default_cycle=row["default_cycle"],
        runner=row["runner"],
        depends_on=tuple(row["depends_on"]),
        validation_status=row["validation_status"],
        efficacy_document=row["efficacy_document"],
        tests=tuple(row["tests"]),
        outputs=tuple(row["outputs"]),
        may_infer=row["may_infer"],
        must_not_infer=row["must_not_infer"],
    )


def load_instrument_registry(path: Path = REGISTRY_PATH) -> dict[str, InstrumentSpec]:
    payload = _load_raw_registry(path)
    if payload.get("status") != "active_engineering_policy":
        raise InstrumentRegistryError("Instrument registry policy is not active")
    policy = payload.get("production_policy")
    if not isinstance(policy, dict) or not all(
        policy.get(key) is True
        for key in (
            "standard_cycle_runs_only_default_cycle_production_instruments",
            "experimental_instruments_rejected_even_when_requested",
            "evidence_capture_only_instruments_not_run_by_standard_cycle",
            "analysis_runs_after_successful_full_corpus_refresh",
            "partial_or_failed_corpus_refresh_does_not_recompute_global_analysis",
            "unregistered_instruments_rejected",
        )
    ):
        raise InstrumentRegistryError("Production policy lost a mandatory fail-closed rule")
    rows = payload.get("instruments")
    if not isinstance(rows, list) or not rows:
        raise InstrumentRegistryError("Instrument registry has no instruments")
    specs = [_as_spec(row) for row in rows]
    by_id = {spec.instrument_id: spec for spec in specs}
    if len(by_id) != len(specs):
        raise InstrumentRegistryError("Duplicate instrument id")
    for spec in specs:
        if spec.default_cycle and spec.lifecycle != "production":
            raise InstrumentRegistryError(
                f"{spec.instrument_id}: only production instruments can run by default"
            )
        if spec.lifecycle == "production":
            if not spec.validation_status.startswith("validated_for_"):
                raise InstrumentRegistryError(
                    f"{spec.instrument_id}: production instrument lacks scoped validation"
                )
            doc_path = ROOT_DIR / spec.efficacy_document.split("#", 1)[0]
            if not doc_path.is_file():
                raise InstrumentRegistryError(
                    f"{spec.instrument_id}: efficacy document not found"
                )
            if not spec.tests:
                raise InstrumentRegistryError(
                    f"{spec.instrument_id}: production instrument has no contract tests"
                )
            for test_path in spec.tests:
                if not (ROOT_DIR / test_path).is_file():
                    raise InstrumentRegistryError(
                        f"{spec.instrument_id}: missing declared test {test_path}"
                    )
            if spec.runner not in _RUNNERS:
                raise InstrumentRegistryError(
                    f"{spec.instrument_id}: production runner is not implemented"
                )
        for dependency in spec.depends_on:
            if dependency not in by_id:
                raise InstrumentRegistryError(
                    f"{spec.instrument_id}: unknown dependency {dependency}"
                )
            if spec.lifecycle == "production" and by_id[dependency].lifecycle != "production":
                raise InstrumentRegistryError(
                    f"{spec.instrument_id}: production depends on non-production {dependency}"
                )
    return by_id


def _restricted_access_runner(output_dir: Path) -> None:
    from .restricted_access_audit import write_restricted_access_audit

    write_restricted_access_audit(output_dir)


def _public_access_runner(output_dir: Path) -> None:
    from .public_access_index import write_public_access_index

    write_public_access_index(output_dir)


_RUNNERS: dict[str, Callable[[Path], None]] = {
    "restricted_access_audit": _restricted_access_runner,
    "public_access_index": _public_access_runner,
}


def _ordered_requested(
    registry: dict[str, InstrumentSpec],
    requested: Iterable[str] | None,
) -> list[InstrumentSpec]:
    if requested is None:
        target_ids = {
            spec.instrument_id
            for spec in registry.values()
            if spec.lifecycle == "production" and spec.default_cycle
        }
    else:
        target_ids = {value.strip() for value in requested if value and value.strip()}
        unknown = sorted(target_ids.difference(registry))
        if unknown:
            raise InstrumentRegistryError(
                f"Unregistered production instrument(s): {', '.join(unknown)}"
            )
        disallowed = sorted(
            instrument_id
            for instrument_id in target_ids
            if registry[instrument_id].lifecycle != "production"
        )
        if disallowed:
            raise InstrumentRegistryError(
                "Production executor rejected non-production instrument(s): "
                + ", ".join(disallowed)
            )
    expanded = set(target_ids)
    changed = True
    while changed:
        changed = False
        for instrument_id in list(expanded):
            for dependency in registry[instrument_id].depends_on:
                if dependency not in expanded:
                    expanded.add(dependency)
                    changed = True

    ordered: list[InstrumentSpec] = []
    pending = set(expanded)
    while pending:
        ready = sorted(
            instrument_id
            for instrument_id in pending
            if set(registry[instrument_id].depends_on).isdisjoint(pending)
        )
        if not ready:
            raise InstrumentRegistryError("Instrument dependency cycle detected")
        for instrument_id in ready:
            ordered.append(registry[instrument_id])
            pending.remove(instrument_id)
    return ordered


def run_production_analysis(
    *,
    output_dir: Path = OUTPUT_DIR,
    requested: Iterable[str] | None = None,
    source_cycle_status: str = "successful_full_refresh",
) -> dict:
    """Run only admitted instruments and persist a provenance/status manifest."""
    if source_cycle_status != "successful_full_refresh":
        raise InstrumentRegistryError(
            "Global production analysis requires a successful full corpus refresh"
        )
    registry = load_instrument_registry()
    selected = _ordered_requested(registry, requested)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = _utcnow()
    rows = []
    try:
        for spec in selected:
            runner = _RUNNERS[spec.runner]
            runner(output_dir)
            missing = [
                filename for filename in spec.outputs
                if not (output_dir / filename).is_file()
            ]
            if missing:
                raise InstrumentRegistryError(
                    f"{spec.instrument_id}: expected output(s) missing: "
                    + ", ".join(missing)
                )
            rows.append(
                {
                    "instrument_id": spec.instrument_id,
                    "version": spec.version,
                    "status": "success",
                    "outputs": list(spec.outputs),
                    "validation_status": spec.validation_status,
                    "efficacy_document": spec.efficacy_document,
                }
            )
    except Exception as exc:
        manifest = {
            "schema_version": "1.0.0",
            "policy": "2026-09-30-production-instrument-gate-v1",
            "started_at": started_at,
            "finished_at": _utcnow(),
            "source_cycle_status": source_cycle_status,
            "status": "failed",
            "instruments": rows,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        (output_dir / RUN_MANIFEST_FILENAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise
    manifest = {
        "schema_version": "1.0.0",
        "policy": "2026-09-30-production-instrument-gate-v1",
        "started_at": started_at,
        "finished_at": _utcnow(),
        "source_cycle_status": source_cycle_status,
        "status": "success",
        "instruments": rows,
        "error_type": None,
        "error": None,
    }
    (output_dir / RUN_MANIFEST_FILENAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def write_analysis_skipped_manifest(
    reason: str,
    *,
    output_dir: Path = OUTPUT_DIR,
    source_cycle_status: str,
) -> dict:
    if not isinstance(reason, str) or not reason.strip():
        raise InstrumentRegistryError("Skipped-analysis reason is required")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    now = _utcnow()
    manifest = {
        "schema_version": "1.0.0",
        "policy": "2026-09-30-production-instrument-gate-v1",
        "started_at": now,
        "finished_at": now,
        "source_cycle_status": source_cycle_status,
        "status": "skipped",
        "instruments": [],
        "error_type": None,
        "error": None,
        "reason": reason.strip(),
    }
    (output_dir / RUN_MANIFEST_FILENAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
