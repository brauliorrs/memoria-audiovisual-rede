"""Adversarial tests for the MAR serial stage gate (offline / no secrets)."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mar_queue_gate", ROOT / "scripts/check_mar_implementation_queue.py"
)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)

BASE = json.loads(
    (ROOT / "docs/engineering/mar-implementation-stage-gates.json").read_text(
        encoding="utf-8"
    )
)
SHA = "a" * 40
REF = "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/123"
PROOF = {
    "reference": REF,
    "commit_sha": SHA,
    "reviewed_by": "human-reviewer",
    "result": "accepted",
}


class EngineeringQueueGateTests(unittest.TestCase):
    def fixture(self):
        return copy.deepcopy(BASE)

    def test_current_stage_is_the_only_active_stage(self):
        self.assertEqual(gate.validate_manifest(self.fixture()), [])

    def test_cannot_start_next_stage_in_parallel(self):
        doc = self.fixture()
        doc["stages"][2]["status"] = "active"
        self.assertTrue(gate.validate_manifest(doc))

    def test_cannot_skip_a_stage(self):
        doc = self.fixture()
        doc["stages"][2]["status"] = "completed"
        self.assertTrue(gate.validate_manifest(doc))

    def test_green_ci_alone_does_not_complete_f01(self):
        doc = self.fixture()
        doc["stages"][1]["status"] = "completed"
        doc["stages"][1]["evidence"] = {"tests": dict(PROOF)}
        doc["stages"][2]["status"] = "active"
        doc["active_stage"] = "F02"
        errors = gate.validate_manifest(doc)
        self.assertTrue(any("completion missing independent gates" in e for e in errors))

    def test_all_f01_gates_can_allow_next_stage(self):
        doc = self.fixture()
        doc["stages"][1]["status"] = "completed"
        doc["stages"][1]["evidence"] = {
            k: dict(PROOF) for k in (
                *gate.BASE_GATES, *gate.EXTRA_GATES["F01"]
            )
        }
        doc["stages"][2]["status"] = "active"
        doc["active_stage"] = "F02"
        self.assertEqual(gate.validate_manifest(doc), [])

    def test_bot_cannot_attest_functional_acceptance(self):
        doc = self.fixture()
        doc["stages"][1]["evidence"]["functional_acceptance"] = {
            **PROOF,
            "reviewed_by": "github-actions",
        }
        self.assertTrue(gate.validate_manifest(doc))

    def test_bad_sha_fails_closed(self):
        doc = self.fixture()
        doc["stages"][1]["evidence"]["tests"] = {**PROOF, "commit_sha": "latest"}
        self.assertTrue(gate.validate_manifest(doc))

    def test_public_access_cannot_be_enabled_early(self):
        doc = self.fixture()
        doc["public_access_authorized"] = True
        self.assertTrue(gate.validate_manifest(doc))

    def test_feature_freeze_cannot_be_disabled_early(self):
        doc = self.fixture()
        doc["new_features_frozen"] = False
        self.assertTrue(gate.validate_manifest(doc))

    def test_blocked_stage_cannot_claim_progress(self):
        doc = self.fixture()
        doc["stages"][3]["evidence"]["tests"] = dict(PROOF)
        self.assertTrue(gate.validate_manifest(doc))

    def test_scientific_review_is_not_automatic(self):
        doc = self.fixture()
        doc["stages"][4]["status"] = "completed"
        doc["stages"][4]["evidence"] = {
            k: dict(PROOF) for k in gate.BASE_GATES
        }
        self.assertTrue(gate.validate_manifest(doc))

    def test_pr_requires_exact_active_stage_declaration(self):
        self.assertEqual(gate.validate_pull_request("MAR-STAGE: F01", "F01"), [])
        self.assertTrue(gate.validate_pull_request("MAR-STAGE: F02", "F01"))
        self.assertTrue(gate.validate_pull_request("", "F01"))
        self.assertTrue(
            gate.validate_pull_request("MAR-STAGE: F01\nMAR-STAGE: F01", "F01")
        )


if __name__ == "__main__":
    unittest.main()
