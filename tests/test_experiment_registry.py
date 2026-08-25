from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_experiment_registry import DEFAULT_REGISTRY, DEFAULT_SCHEMA, validate_registry


def test_current_experiment_registry_is_valid() -> None:
    assert validate_registry(DEFAULT_REGISTRY, DEFAULT_SCHEMA) == []


def test_empirical_blind_validation_requires_frozen_prediction(tmp_path: Path) -> None:
    governance = tmp_path / "docs" / "governance.md"
    governance.parent.mkdir(parents=True)
    governance.write_text("# Governance\n", encoding="utf-8")

    review = tmp_path / "data" / "human_review.json"
    review.parent.mkdir(parents=True)
    review.write_text("{}\n", encoding="utf-8")

    comparison = tmp_path / "data" / "comparison.json"
    comparison.write_text("{}\n", encoding="utf-8")

    registry = {
        "schema_version": "1.0.0",
        "registry_id": "mar-experiment-registry-v1",
        "project": "Memória Audiovisual em Rede",
        "scope": "controlled test registry for semantic validation behaviour",
        "does_not_modify_official_baseline": True,
        "governance_document": "docs/governance.md",
        "experiments": [
            {
                "experiment_id": "MAR-T2A-TEST-001",
                "version": "1",
                "stage": "test_stage",
                "scientific_layer": "mar_intelligence_automation",
                "experiment_types": ["blind_human_validation", "ecological_validation"],
                "status": "completed",
                "claim_level": "empirical_validation",
                "is_prevalence_sample": False,
                "does_not_modify_official_baseline": True,
                "question": "Does a frozen mechanism generalise to an independent blind sample?",
                "blinding": {"human_reviewer_saw_model_predictions": False},
                "scientific_decision": "Do not accept without a frozen prediction artifact.",
                "limitations": ["Synthetic validator test only."],
                "prohibited_interpretations": ["Not a real scientific result."],
                "artifacts": [
                    {"path": "data/human_review.json", "role": "human_review"},
                    {"path": "data/comparison.json", "role": "performance_comparison"}
                ]
            }
        ]
    }

    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    errors = validate_registry(registry_path, DEFAULT_SCHEMA, repo_root=tmp_path)
    assert any("frozen before human review" in error for error in errors)
