"""Append canonical VAL-007/CAL-008 records and reserve VAL-009, schema checked.

Reads existing conclusions; never reruns an evaluation or changes historical data.
"""
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = Path("data/digital_infrastructure/ai_experiments")
REGISTRY = DATA / "experiment_registry_v1.json"


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def artifact(path, role):
    return {"path": str(path), "role": role,
            "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def records():
    evaluation_path = DATA / "m3_surface_type_independent_evaluation_v2_2.json"
    development_path = DATA / "m3_surface_type_post_val007_development_v2_3.json"
    protocol_path = DATA / "m3_surface_type_independent_validation_protocol_v2_3_draft.json"
    evaluation, development, protocol = map(load, (evaluation_path, development_path, protocol_path))
    shared = {"scientific_layer": "mar_intelligence_automation",
              "is_prevalence_sample": False, "does_not_modify_official_baseline": True}
    return [
        {**shared, "experiment_id": evaluation["experiment_id"], "version": "2.2.0",
         "stage": "t2a_mar_surface_typing_independent_validation",
         "experiment_types": ["blind_human_validation", "ecological_validation"],
         "status": "failed", "claim_level": "empirical_validation",
         "decision_date": evaluation["evaluated_on"],
         "blinding": {"human_reviewer_saw_model_predictions": False},
         "question": "Does M3 2.2.0 meet the preregistered semantic, item-level and access gates on independent entities?",
         "sample_summary": {"units_total": evaluation["units_total"],
                            "acceptance_assessment": evaluation["acceptance_assessment"]},
         "scientific_decision": evaluation["scientific_decision"],
         "limitations": evaluation["limitations"],
         "prohibited_interpretations": evaluation["prohibited_interpretations"],
         "artifacts": [artifact(evaluation_path, "frozen_independent_evaluation"),
                       artifact(DATA / "m3_surface_type_independent_human_review_v2_2.json", "human_review"),
                       artifact(DATA / "m3_surface_type_independent_human_review_freeze_v2_2.json", "human_review_freeze"),
                       {**artifact(DATA / "m3_surface_type_independent_prediction_freeze_v2_2.json", "prediction_freeze"),
                        "frozen_before_human_review": evaluation["prediction_frozen_before_human_review"]}]},
        {**shared, "experiment_id": development["experiment_id"], "version": "2.3.0",
         "stage": development["stage"], "experiment_types": ["calibration_experiment", "diagnostic_replay"],
         "status": "completed_calibration_only", "claim_level": "calibration_only",
         "decision_date": development["recorded_on"], "source_experiment_id": evaluation["experiment_id"],
         "question": "Can generic 2.3.0 candidate rules address known VAL-007 failures while preserving development regressions?",
         "sample_summary": {"known_development_units_total": development["known_development_units_total"]},
         "scientific_decision": development["development_gate_interpretation"]["reason"],
         "limitations": ["Development replay after observing VAL-007; no independent generalisation evidence."],
         "prohibited_interpretations": development["prohibited_interpretations"],
         "artifacts": [artifact(development_path, "historical_development_evaluation")]},
        {**shared, "experiment_id": protocol["experiment_id"], "version": "2.3.0",
         "stage": "t2a_mar_surface_typing_independent_preregistration",
         # Blind review is planned, not claimed as conducted without human artifacts.
         "experiment_types": ["ecological_validation"],
         "status": "reserved_draft_not_executed", "claim_level": "protocol_scope",
         "created_on": protocol["prepared_on"], "question": protocol["question"],
         "scientific_use": "Reserve the identifier for planned blind ecological validation only. Complete readiness and seal before any independent sampling. No human review yet. M4 remains blocked.",
         "limitations": ["No new collection, human review, independent metrics or freeze exists for this draft."],
         "prohibited_interpretations": ["No independent validation claim", "No M4 promotion", "No reuse of known development units as independent evidence"],
         "artifacts": [artifact(protocol_path, "initial_preregistration_draft")]
         },
    ]


def main():
    registry = load(REGISTRY)
    ids = [record["experiment_id"] for record in registry["experiments"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate registry IDs")
    additions = records()
    present = {record["experiment_id"] for record in additions} & set(ids)
    if present:
        if len(present) == len(additions):
            print("All three IDs already registered; no records rewritten")
            return
        raise ValueError("Partial registration requires inspection; no historical records rewritten")
    registry["experiments"].extend(additions)
    registry["updated_on"] = "2026-09-15"
    Draft202012Validator(load(Path("schemas/digital_infrastructure/experiment_registry.schema.json"))).validate(registry)
    (ROOT / REGISTRY).write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Registered VAL-007, CAL-008; reserved VAL-009 as draft, not executed")


if __name__ == "__main__":
    main()
