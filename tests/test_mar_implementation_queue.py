"""Stable adversarial fixtures for MAR serial stage gate (offline).

The fixture must NOT be derived from the live manifest: otherwise legitimate
advances to F02 or F13 would break tests that assume F01 is still active.
"""
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

FIXTURE = {
    "schema": "mar.engineering.stage-gate.v1",
    "queue_issue": gate.ISSUE,
    "active_stage": "F01",
    "new_features_frozen": True,
    "public_access_authorized": False,
    "stages": [
        {
            "id": sid,
            "title": f"Contract test {sid}",
            "status": "completed" if i == 0 else "active" if i == 1 else "blocked",
            "evidence": {},
        }
        for i, sid in enumerate(gate.STAGES)
    ],
}
SHA = "a" * 40
REF = "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/123"
PROOF = {
    "reference": REF,
    "commit_sha": SHA,
    "reviewed_by": "human-reviewer",
    "result": "accepted",
}


def complete_through(index: int) -> dict:
    """Build a fully evidenced, valid synthetic queue state for any stage."""
    if not 0 <= index < len(gate.STAGES):
        raise ValueError("Invalid stage index")
    doc = copy.deepcopy(FIXTURE)
    for i in range(1, index + 1):
        stage = doc["stages"][i]
        stage["status"] = "completed"
        stage["evidence"] = {
            key: dict(PROOF)
            for key in (*gate.BASE_GATES, *gate.EXTRA_GATES.get(stage["id"], ()))
        }
    if index + 1 < len(gate.STAGES):
        doc["active_stage"] = gate.STAGES[index + 1]
        doc["stages"][index + 1]["status"] = "active"
    else:
        doc["active_stage"] = None
        doc["public_access_authorized"] = True
        doc["new_features_frozen"] = False
    return doc


class EngineeringQueueGateTests(unittest.TestCase):
    def fixture(self):
        return copy.deepcopy(FIXTURE)

    def test_live_manifest_is_structurally_valid_regardless_of_active_stage(self):
        current = json.loads(
            (ROOT / "docs/engineering/mar-implementation-stage-gates.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(gate.validate_manifest(current), [])

    def test_fixed_f01_fixture_is_valid(self):
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
        doc = complete_through(1)
        self.assertEqual(gate.validate_manifest(doc), [])
        self.assertEqual(doc["active_stage"], "F02")

    def test_subsequent_valid_transitions_cannot_break_f01_fixtures(self):
        for completed in range(1, len(gate.STAGES)):
            with self.subTest(stage=completed):
                doc = complete_through(completed)
                self.assertEqual(gate.validate_manifest(doc), [])

    def test_bot_cannot_attest_functional_acceptance(self):
        doc = complete_through(1)
        doc["stages"][1]["evidence"]["functional_acceptance"] = {
            **PROOF, "reviewed_by": "github-actions"
        }
        self.assertTrue(gate.validate_manifest(doc))

    def test_bad_sha_fails_closed(self):
        doc = complete_through(1)
        doc["stages"][1]["evidence"]["tests"] = {
            **PROOF, "commit_sha": "latest"
        }
        self.assertTrue(gate.validate_manifest(doc))

    def test_scientific_review_required_for_f04(self):
        doc = complete_through(4)
        del doc["stages"][4]["evidence"]["scientific_scope_review"]
        self.assertTrue(any("scientific_scope_review" in e for e in gate.validate_manifest(doc)))

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

    def test_completed_f13_manifest_must_require_public_approval(self):
        doc = complete_through(13)
        self.assertEqual(gate.validate_manifest(doc), [])
        doc["public_access_authorized"] = False
        self.assertTrue(gate.validate_manifest(doc))

    def test_pr_requires_exact_active_stage_declaration(self):
        self.assertEqual(gate.validate_pull_request("MAR-STAGE: F01", "F01"), [])
        self.assertTrue(gate.validate_pull_request("MAR-STAGE: F02", "F01"))
        self.assertTrue(gate.validate_pull_request("", "F01"))
        self.assertTrue(gate.validate_pull_request(
            "MAR-STAGE: F01\nMAR-STAGE: F01", "F01"
        ))

    def test_pr_marker_valid_when_stage_advances(self):
        self.assertEqual(gate.validate_pull_request("MAR-STAGE: F02", "F02"), [])
        self.assertTrue(gate.validate_pull_request("MAR-STAGE: F01", "F02"))

    def test_f13_completion_pr_may_pass_when_active_stage_is_null(self):
        self.assertEqual(gate.validate_pull_request("MAR-STAGE: F13", None), [])

    def test_post_queue_pr_requires_explicit_complete_marker(self):
        self.assertEqual(gate.validate_pull_request("MAR-QUEUE: COMPLETE", None), [])
        self.assertTrue(gate.validate_pull_request("MAR-STAGE: F02", None))
        self.assertTrue(gate.validate_pull_request("", None))
        self.assertTrue(gate.validate_pull_request(
            "MAR-STAGE: F13\nMAR-QUEUE: COMPLETE", None
        ))
        self.assertTrue(gate.validate_pull_request(
            "MAR-STAGE: F01\nMAR-QUEUE: COMPLETE", "F01"
        ))


if __name__ == "__main__":
    unittest.main()
