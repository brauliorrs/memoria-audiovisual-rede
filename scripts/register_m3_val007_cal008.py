from __future__ import annotations

import json
from pathlib import Path


REGISTRY_PATH = Path("data/digital_infrastructure/ai_experiments/experiment_registry_v1.json")

VAL007 = {
    "experiment_id": "MAR-T2A-M3-VAL-007",
    "hypothesis_version": "h_m3_surface_type_v2_2",
    "feature_version": "surface_features_v2_2",
    "algorithm_version": "deterministic_surface_typing_rules_v2_2",
    "threshold_version": "not_applicable",
    "sample_version": "independent_corpus_sample_v2_2",
    "evaluation_split": "independent_validation",
    "git_commit": "598be11c93df2e613616c27447775c777e63ba18",
    "status": "failed",
    "promoted": False,
    "source_snapshots": [
        {
            "snapshot_id": "MAR-T2A-M3-VAL-007-PROTOCOL",
            "path": "data/digital_infrastructure/ai_experiments/m3_surface_type_independent_validation_protocol_v2_2.json",
            "git_blob_sha": "6f4f965556200653976a2b0cd3671a4afd200c82",
        },
        {
            "snapshot_id": "MAR-T2A-M3-VAL-007-PREDICTION-FREEZE",
            "path": "data/digital_infrastructure/ai_experiments/m3_surface_type_independent_prediction_freeze_v2_2.json",
            "git_blob_sha": "c12368dd765f84d411b7b667da7209509c8849cb",
        },
        {
            "snapshot_id": "MAR-T2A-M3-VAL-007-HUMAN-REVIEW-FREEZE",
            "path": "data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_freeze_v2_2.json",
            "git_blob_sha": "4000544c32fec0b2f4d6756a7cacc8c4642354c0",
        },
    ],
    "output_artifacts": [
        {
            "artifact_id": "MAR-T2A-M3-VAL-007-EVALUATION",
            "path": "data/digital_infrastructure/ai_experiments/m3_surface_type_independent_evaluation_v2_2.json",
            "git_blob_sha": "b63fc74fb4b69b40e5cd41dbfee1fc1084d67a32",
        }
    ],
    "report_path": "docs/research/experiments/2026-09_m3_surface_typing_independent_validation_v2_2.md",
    "metrics_summary": {
        "fine_exact_accuracy": 0.22580645161290322,
        "fine_macro_f1_supported": 0.2835064935064935,
        "fine_weighted_f1": 0.2828236279849183,
        "item_level_precision": 1.0,
        "item_level_recall": 0.14285714285714285,
        "item_level_f1": 0.25,
        "item_level_specificity": 1.0,
        "item_level_accuracy": 0.6,
        "access_state_agreement": 1.0,
    },
    "reviewer_notes": [
        "Blind human review completed and frozen at 31/31 units before model predictions were opened.",
        "Authoritative source execution: workflow run 33673923717, job 100393939906, artifact 9863619119.",
        "Six preregistered entities contributed review units; FINA/Ninateka contributed one eligible observed surface and was not replaced post hoc.",
        "No classifier tuning or entity substitution was performed after the independent sample was frozen.",
        "Protocol 2.2.0 failed the preregistered semantic and item-level recall gates; M4 scale remains blocked.",
    ],
    "known_limitations": [
        "The independent ecological sample is not a prevalence sample and contains sparse support for some fine-grained classes.",
        "Three entity families with at least two human item-level positives suffered total item-level miss: Cinemateca Portuguesa, Cinematheque francaise/HENRI, and Home Movies/Memoryscapes.",
        "Fine-grained recall failed for archive_landing_page, search_or_index, and audiovisual_item among classes with support >= 5.",
    ],
    "valid_reuse": [
        "historical reference",
        "protocol 2.3 development diagnosis",
    ],
    "invalid_reuse": [
        "official T2 baseline",
        "production automation",
        "population-prevalence inference",
        "protocol 2.2 promotion",
        "M4 scale",
    ],
}

CAL008 = {
    "experiment_id": "MAR-T2A-M3-CAL-008",
    "hypothesis_version": "h_m3_surface_type_v2_3",
    "feature_version": "surface_features_v2_3",
    "algorithm_version": "deterministic_surface_typing_rules_v2_3_candidate",
    "threshold_version": "not_applicable",
    "sample_version": "post_val007_development_human_labeled_v2_3",
    "evaluation_split": "development",
    "git_commit": "1459105b335ba3f3dc372c3e5084299b6de2c72e",
    "status": "completed",
    "promoted": False,
    "source_snapshots": [
        {
            "snapshot_id": "MAR-T2A-M3-VAL-007-HUMAN-REVIEW",
            "path": "data/digital_infrastructure/ai_experiments/m3_surface_type_independent_human_review_v2_2.json",
            "git_blob_sha": "a9f8fc78107424ffd33add5830ed743185d1fbaf",
        },
        {
            "snapshot_id": "MAR-T2A-M3-KNOWN-URLS-V2-2",
            "path": "data/digital_infrastructure/ai_experiments/m3_surface_type_known_urls_exclusion_v2_2.json",
            "git_blob_sha": "b33edfc5ba105214e5a651e26e1d90b603216d4f",
        },
    ],
    "output_artifacts": [
        {
            "artifact_id": "MAR-T2A-M3-CAL-008-DEVELOPMENT-EVALUATION",
            "path": "data/digital_infrastructure/ai_experiments/m3_surface_type_post_val007_development_v2_3.json",
            "git_blob_sha": "5ff1df18be014ff810758202a2d8294baa08eb34",
        }
    ],
    "report_path": "docs/research/experiments/2026-09_m3_surface_typing_post_val007_development_v2_3.md",
    "metrics_summary": {
        "fine_exact_accuracy": 0.8064516129032258,
        "fine_macro_f1_supported": 0.8009259259259259,
        "fine_weighted_f1": 0.8663381123058542,
        "item_level_precision": 1.0,
        "item_level_recall": 0.9285714285714286,
        "item_level_f1": 0.962962962962963,
        "item_level_specificity": 1.0,
        "item_level_accuracy": 0.9666666666666667,
    },
    "reviewer_notes": [
        "Development-only replay on the already human-labeled VAL-007 sample; these metrics are not independent validation evidence.",
        "All 117 known human-reviewed M3 units accumulated through VAL-007 are development material and must be excluded from future independent validation.",
        "Generic candidate rules contain no institution-specific names, IDs, or exact slugs.",
        "Final quality checks were green in run 34298716962, job 102300853568 (767 tests passed plus 2 subtests).",
    ],
    "known_limitations": [
        "The candidate was designed after inspecting VAL-007 errors and therefore cannot be validated on VAL-007.",
        "Replay performance may overestimate ecological generalization and must not be interpreted as independent performance.",
    ],
    "valid_reuse": [
        "development-only calibration",
        "design and preregistration of protocol 2.3 independent validation",
    ],
    "invalid_reuse": [
        "independent validation claim",
        "official T2 baseline",
        "production automation",
        "population-prevalence inference",
        "M4 scale",
    ],
}


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    experiments = registry.get("experiments")
    if not isinstance(experiments, list):
        raise SystemExit("Registry experiments must be a list")

    ids = [row.get("experiment_id") for row in experiments if isinstance(row, dict)]
    if len(ids) != len(set(ids)):
        raise SystemExit("Registry already contains duplicate experiment IDs")
    if "MAR-T2A-M3-CAL-006" not in ids:
        raise SystemExit("Expected predecessor MAR-T2A-M3-CAL-006 is absent")

    target_ids = {VAL007["experiment_id"], CAL008["experiment_id"]}
    present = target_ids.intersection(ids)
    if present == target_ids:
        print("VAL-007 and CAL-008 are already registered; no change needed")
        return
    if present:
        raise SystemExit(f"Partial target state is not accepted: {sorted(present)}")

    experiments.extend([VAL007, CAL008])
    registry["updated_on"] = "2026-09-14"
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Registered MAR-T2A-M3-VAL-007 and MAR-T2A-M3-CAL-008")


if __name__ == "__main__":
    main()
