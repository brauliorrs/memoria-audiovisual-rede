#!/usr/bin/env python3
"""Validate the MAR scientific experiment registry and its durable artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

DEFAULT_REGISTRY = Path("data/digital_infrastructure/ai_experiments/experiment_registry_v1.json")
DEFAULT_SCHEMA = Path("schemas/digital_infrastructure/experiment_registry.schema.json")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode("utf-8")
    return hashlib.sha1(header + payload).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_has_hash(artifact: dict[str, Any]) -> bool:
    return any(artifact.get(key) for key in ("content_sha", "current_blob_sha", "sha256"))


def _role_matches(artifact: dict[str, Any], *tokens: str) -> bool:
    role = str(artifact.get("role") or "").lower()
    return any(token in role for token in tokens)


def validate_registry(
    registry_path: Path = DEFAULT_REGISTRY,
    schema_path: Path = DEFAULT_SCHEMA,
    repo_root: Path = Path("."),
) -> list[str]:
    errors: list[str] = []

    if not schema_path.is_file():
        return [f"schema not found: {schema_path}"]
    if not registry_path.is_file():
        return [f"registry not found: {registry_path}"]

    schema = _load_json(schema_path)
    registry = _load_json(registry_path)

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:  # pragma: no cover - defensive schema bootstrap
        return [f"invalid JSON Schema: {exc}"]

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(registry), key=lambda item: list(item.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"schema:{location}: {error.message}")

    if errors:
        return errors

    governance_document = repo_root / registry["governance_document"]
    if not governance_document.is_file():
        errors.append(f"governance document not found: {registry['governance_document']}")

    experiments: list[dict[str, Any]] = registry["experiments"]
    ids = [experiment["experiment_id"] for experiment in experiments]
    duplicate_ids = sorted({experiment_id for experiment_id in ids if ids.count(experiment_id) > 1})
    for experiment_id in duplicate_ids:
        errors.append(f"duplicate experiment_id: {experiment_id}")

    known_ids = set(ids)

    for experiment in experiments:
        experiment_id = experiment["experiment_id"]
        claim_level = experiment["claim_level"]
        experiment_types = set(experiment["experiment_types"])
        artifacts: list[dict[str, Any]] = experiment["artifacts"]

        if experiment.get("does_not_modify_official_baseline") is not True:
            errors.append(f"{experiment_id}: T2A experiment must not modify the official baseline")

        if claim_level == "official_baseline":
            errors.append(
                f"{experiment_id}: official_baseline claim is incompatible with this T2A registry; "
                "use a separately authorised baseline transition record"
            )

        source_id = experiment.get("source_experiment_id")
        if source_id and source_id not in known_ids:
            errors.append(f"{experiment_id}: unknown source_experiment_id {source_id}")

        for artifact in artifacts:
            relative_path = artifact["path"]
            path = repo_root / relative_path
            if not path.is_file():
                errors.append(f"{experiment_id}: artifact not found: {relative_path}")
                continue

            content_sha = artifact.get("content_sha")
            if content_sha:
                actual = _git_blob_sha(path) if len(content_sha) == 40 else _sha256(path)
                if actual != content_sha:
                    errors.append(
                        f"{experiment_id}: content_sha mismatch for {relative_path}: "
                        f"registered={content_sha} actual={actual}"
                    )

            current_blob_sha = artifact.get("current_blob_sha")
            if current_blob_sha:
                actual = _git_blob_sha(path)
                if actual != current_blob_sha:
                    errors.append(
                        f"{experiment_id}: current_blob_sha mismatch for {relative_path}: "
                        f"registered={current_blob_sha} actual={actual}"
                    )

            sha256 = artifact.get("sha256")
            if sha256:
                actual = _sha256(path)
                if actual != sha256:
                    errors.append(
                        f"{experiment_id}: sha256 mismatch for {relative_path}: "
                        f"registered={sha256} actual={actual}"
                    )

        if "blind_human_validation" in experiment_types:
            blinding = experiment.get("blinding")
            if not isinstance(blinding, dict):
                errors.append(f"{experiment_id}: blind human validation requires a blinding object")
            elif blinding.get("human_reviewer_saw_model_predictions") is not False:
                errors.append(f"{experiment_id}: blind review must state that model predictions were not seen")

            has_human_artifact = any(
                _role_matches(artifact, "human_review", "review_queue", "review_amendment")
                for artifact in artifacts
            )
            if not has_human_artifact:
                errors.append(f"{experiment_id}: blind human validation requires a durable human-review artifact")

        if claim_level == "empirical_validation":
            has_frozen_prediction = any(
                _role_matches(artifact, "prediction")
                and artifact.get("frozen_before_human_review") is True
                and _artifact_has_hash(artifact)
                for artifact in artifacts
            )
            has_evaluation = any(_role_matches(artifact, "comparison", "evaluation", "performance") for artifact in artifacts)
            has_human_artifact = any(
                _role_matches(artifact, "human_review", "review_queue", "review_amendment")
                for artifact in artifacts
            )
            if "blind_human_validation" in experiment_types and not has_frozen_prediction:
                errors.append(
                    f"{experiment_id}: empirical blind validation requires a prediction artifact "
                    "frozen before human review and protected by an integrity hash"
                )
            if "blind_human_validation" in experiment_types and not has_human_artifact:
                errors.append(f"{experiment_id}: empirical blind validation requires a human-review artifact")
            if not has_evaluation:
                errors.append(f"{experiment_id}: empirical validation requires an evaluation/comparison artifact")

        if claim_level == "diagnostic_only":
            if "diagnostic_replay" not in experiment_types:
                errors.append(f"{experiment_id}: diagnostic_only claim requires diagnostic_replay experiment type")
            if experiment.get("is_scientific_performance_result") is not False:
                errors.append(f"{experiment_id}: diagnostic replay must set is_scientific_performance_result=false")
            if experiment.get("is_original_run_prediction") is not False:
                errors.append(f"{experiment_id}: diagnostic replay must set is_original_run_prediction=false")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()

    errors = validate_registry(args.registry, args.schema)
    if errors:
        print("Experiment registry validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    registry = _load_json(args.registry)
    print(
        "Experiment registry valid: "
        f"{len(registry['experiments'])} experiments; schema={registry['schema_version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
