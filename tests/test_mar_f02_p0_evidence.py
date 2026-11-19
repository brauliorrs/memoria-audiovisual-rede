"""Adversarial offline checks for the dated F02 Neon security baseline.

The live database must be inspected separately: these tests only prevent
a saved failing P0 baseline from being misrepresented as approved.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mar_f02_evidence", ROOT / "scripts/check_mar_f02_p0_evidence.py"
)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)

BASE = json.loads(gate.REPORT.read_text(encoding="utf-8"))


class F02P0EvidenceTests(unittest.TestCase):
    def fixture(self):
        return copy.deepcopy(BASE)

    def test_baseline_is_honest_hold(self):
        self.assertEqual(gate.validate_report(self.fixture()), [])

    def test_never_promote_from_clone_or_ci_only(self):
        doc = self.fixture()
        doc["status"] = "PASSED"
        self.assertTrue(gate.validate_report(doc))

    def test_prod_must_not_be_declared_protected(self):
        doc = self.fixture()
        doc["production"]["protected"] = True
        self.assertTrue(gate.validate_report(doc))

    def test_prod_was_not_modified(self):
        doc = self.fixture()
        doc["production"]["modified"] = True
        self.assertTrue(gate.validate_report(doc))

    def test_real_validation_role_excessive_grants_are_recorded(self):
        doc = self.fixture()
        doc["validation_source"]["grants_before"]["checkpoints"]["update"] = False
        self.assertTrue(gate.validate_report(doc))

    def test_lab_role_cannot_regain_insert_update_delete(self):
        for table in gate.TABLES:
            for privilege in gate.DML:
                doc = self.fixture()
                doc["isolated_lab"]["grants_after"][table][privilege] = True
                with self.subTest(table=table, privilege=privilege):
                    self.assertTrue(gate.validate_report(doc))

    def test_lab_cannot_be_confused_with_independent_restore(self):
        doc = self.fixture()
        doc["isolated_lab"]["independent_restore_proven"] = True
        self.assertTrue(gate.validate_report(doc))

    def test_unavailable_nonroot_snapshot_must_not_be_fabricated(self):
        doc = self.fixture()
        doc["snapshot_probe"]["created"] = True
        self.assertTrue(gate.validate_report(doc))

    def test_no_p0_security_requirement_may_be_preapproved(self):
        for name in gate.REQUIRED:
            doc = self.fixture()
            doc["p0_requirements"][name] = True
            with self.subTest(name=name):
                self.assertTrue(gate.validate_report(doc))

    def test_clone_counts_must_match_source(self):
        doc = self.fixture()
        doc["isolated_lab"]["rows"]["checkpoints"] += 1
        self.assertTrue(gate.validate_report(doc))

    def test_missing_both_row_inventories_fails_closed(self):
        doc = self.fixture()
        del doc["validation_source"]["rows"]
        del doc["isolated_lab"]["rows"]
        self.assertTrue(gate.validate_report(doc))

    def test_partial_matching_inventories_do_not_pass(self):
        doc = self.fixture()
        doc["validation_source"]["rows"] = {"checkpoints": 4}
        doc["isolated_lab"]["rows"] = {"checkpoints": 4}
        self.assertTrue(gate.validate_report(doc))

    def test_fabricated_equal_empty_inventories_do_not_pass(self):
        doc = self.fixture()
        doc["validation_source"]["rows"] = {}
        doc["isolated_lab"]["rows"] = {}
        self.assertTrue(gate.validate_report(doc))

    def test_fabricated_equal_wrong_counts_do_not_pass(self):
        doc = self.fixture()
        for label in ("validation_source", "isolated_lab"):
            doc[label]["rows"]["checkpoints"] = 0
        self.assertTrue(gate.validate_report(doc))

    def test_malformed_row_count_values_do_not_pass(self):
        for malformed in (True, "4", -1, None):
            doc = self.fixture()
            doc["validation_source"]["rows"]["checkpoints"] = malformed
            doc["isolated_lab"]["rows"]["checkpoints"] = malformed
            with self.subTest(malformed=malformed):
                self.assertTrue(gate.validate_report(doc))

    def test_malformed_original_grant_object_does_not_crash_or_pass(self):
        doc = self.fixture()
        doc["validation_source"]["grants_before"]["checkpoints"] = None
        self.assertTrue(gate.validate_report(doc))

    def test_history_and_snapshot_absence_are_exposed(self):
        doc = self.fixture()
        doc["project"]["history_retention_seconds"] = 2592000
        doc["project"]["automatic_snapshots_count"] = 5
        self.assertTrue(gate.validate_report(doc))

    def test_missing_structure_fails_closed(self):
        self.assertTrue(gate.validate_report(None))
        doc = self.fixture()
        del doc["isolated_lab"]["grants_after"]["raw_artifacts"]
        self.assertTrue(gate.validate_report(doc))


if __name__ == "__main__":
    unittest.main()
