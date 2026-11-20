"""Adversarial tests: a personal Drive folder is not an active or WORM backup."""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mar_f02_google_drive_plan", ROOT / "scripts/check_mar_f02_google_drive_personal_plan.py"
)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)
RECORD = json.loads(gate.REPORT.read_text(encoding="utf-8"))


class DrivePersonalF02PlanTests(unittest.TestCase):
    def fresh(self):
        return copy.deepcopy(RECORD)

    def test_selected_private_destination_is_honestly_hold(self):
        self.assertEqual(gate.validate(self.fresh()), [])

    def test_never_claim_scheduled_backup_just_from_existing_folder(self):
        for field in ("automatic_backup_enabled", "scheduled_workflow_deployed"):
            with self.subTest(field=field):
                record = self.fresh()
                record["activation"][field] = True
                self.assertTrue(gate.validate(record))

    def test_never_claim_uploaded_restorable_data(self):
        for field in (
            "encrypted_backup_uploaded", "upload_sha256_verified",
            "isolated_restore_on_new_runner", "old_backup_restore_tested",
        ):
            with self.subTest(field=field):
                record = self.fresh()
                record["security"][field] = True
                self.assertTrue(gate.validate(record))

    def test_google_drive_is_not_WORM(self):
        for field in (
            "immutable_WORM_supported_by_selected_destination",
            "immutability_proven",
            "retention_90_days_verified",
        ):
            with self.subTest(field=field):
                record = self.fresh()
                record["retention"][field] = True
                self.assertTrue(gate.validate(record))

    def test_explicit_owner_risk_acceptance_is_scoped_and_does_not_prove_worm(self):
        record = self.fresh()
        self.assertTrue(record["retention"]["owner_risk_waiver_for_missing_WORM"])
        self.assertFalse(record["retention"]["immutable_WORM_supported_by_selected_destination"])
        self.assertFalse(record["retention"]["immutability_proven"])
        self.assertFalse(record["retention"]["retention_90_days_verified"])
        self.assertFalse(record["activation"]["automatic_backup_enabled"])
        self.assertFalse(record["activation"]["stage_F02_closed"])
        self.assertEqual(gate.validate(record), [])

        record["retention"]["owner_risk_waiver_for_missing_WORM"] = False
        self.assertTrue(gate.validate(record))

    def test_risk_acceptance_requires_explicit_date_scope_and_limits(self):
        base = self.fresh()
        for key, bad in (
            ("date", "2026-11-18"),
            ("decision", "inferred_from_folder_choice"),
            ("scope", "production_and_public"),
            ("destination", "any_cloud_provider"),
            ("risk", "unknown"),
            ("controls", []),
            ("controls", ["ciphertext_only_AES_256_GCM"]),
            ("does_not_prove", []),
            ("does_not_authorize", []),
        ):
            record = self.fresh()
            record["retention"]["owner_risk_acceptance"][key] = bad
            with self.subTest(key=key, bad=bad):
                self.assertTrue(gate.validate(record))
        record = self.fresh()
        del record["retention"]["owner_risk_acceptance"]
        self.assertTrue(gate.validate(record))

    def test_never_auto_delete_90_day_backups_early(self):
        record = self.fresh()
        record["retention"]["automatic_deletion_enabled"] = True
        self.assertTrue(gate.validate(record))

    def test_never_claim_oauth_integration_using_chat_connector(self):
        for field in (
            "connection_to_github_actions_established",
            "folder_granted_to_backup_oauth_client",
            "oauth_picker_authorization_completed",
        ):
            with self.subTest(field=field):
                record = self.fresh()
                record["destination"][field] = True
                self.assertTrue(gate.validate(record))

    def test_no_main_branch_mutation_or_new_reader_at_source(self):
        record = self.fresh()
        record["source"]["production_modified"] = True
        self.assertTrue(gate.validate(record))
        record = self.fresh()
        record["source"]["reader_provisioned_in_source_branch"] = True
        self.assertTrue(gate.validate(record))

    def test_oauth_scope_must_stay_file_scoped(self):
        record = self.fresh()
        record["destination"]["oauth_scope_target"] = "https://www.googleapis.com/auth/drive"
        self.assertTrue(gate.validate(record))

    def test_private_folder_id_must_not_be_embedded_in_public_repo(self):
        record = self.fresh()
        record["destination"]["folder_id"] = "private-drive-folder"
        self.assertTrue(gate.validate(record))
        record = self.fresh()
        record["destination"]["folder_id_or_url_in_public_repository"] = True
        self.assertTrue(gate.validate(record))

    def test_no_token_or_encryption_key_in_drive_or_repo(self):
        for field in ("drive_token_or_key_in_drive", "drive_token_or_key_in_repository"):
            with self.subTest(field=field):
                record = self.fresh()
                record["security"][field] = True
                self.assertTrue(gate.validate(record))

    def test_encryption_must_happen_before_upload(self):
        record = self.fresh()
        record["security"]["encryption_before_upload"] = "none"
        self.assertTrue(gate.validate(record))

    def test_retention_target_is_90_days_minimum_not_provider_WORM(self):
        for value in (0, 60, 91, "90", True, None):
            with self.subTest(value=value):
                record = self.fresh()
                record["retention"]["operational_target_days"] = value
                self.assertTrue(gate.validate(record))

    def test_production_and_f03_remain_blocked(self):
        for field in ("stage_F02_closed", "stage_F03_open", "public_access_authorized"):
            with self.subTest(field=field):
                record = self.fresh()
                record["activation"][field] = True
                self.assertTrue(gate.validate(record))

    def test_secret_is_not_preconfigured_and_opt_in_is_explicit(self):
        record = self.fresh()
        record["activation"]["automation_secret_configured"] = True
        self.assertTrue(gate.validate(record))
        record = self.fresh()
        record["activation"]["authorization_variable"] = ""
        self.assertTrue(gate.validate(record))

    def test_invalid_root_and_required_sections_fail_closed(self):
        self.assertTrue(gate.validate(None))
        self.assertTrue(gate.validate({}))
        for section in ("destination", "security", "retention", "activation"):
            record = self.fresh()
            del record[section]
            self.assertTrue(gate.validate(record))


if __name__ == "__main__":
    unittest.main()
