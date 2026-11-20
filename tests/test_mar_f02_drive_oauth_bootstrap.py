"""F02 local OAuth onboarding: adversarial tests without network or secrets."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.mar_f02_drive_oauth_bootstrap import (
    ROOT, check_output_file, check_private_file, main,
)
from scripts.mar_p0_offsite_google_drive import DriveBackupRejected


class DriveOAuthBootstrapTests(unittest.TestCase):
    def test_dry_run_never_loads_google_libs_or_writes_anything(self):
        with patch("scripts.mar_f02_drive_oauth_bootstrap.authorize") as auth:
            code = main(["--client-json", "/absent/client.json",
                         "--output", "/absent/result.json"])
        self.assertEqual(code, 0)
        auth.assert_not_called()

    def test_execute_rejects_inaccessible_input_without_creating_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            root.chmod(0o700)
            output = root / "secrets.json"
            code = main(["--client-json", str(root / "does-not-exist.json"),
                         "--output", str(output), "--execute"])
            self.assertEqual(code, 2)
            self.assertFalse(output.exists())

    def test_rejects_output_inside_public_git_repository(self):
        with self.assertRaises(DriveBackupRejected):
            check_output_file(ROOT / "never_write_secrets_to_repo.json")

    def test_rejects_output_in_world_readable_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            root.chmod(0o755)
            with self.assertRaises(DriveBackupRejected):
                check_output_file(root / "secrets.json")

    def test_rejects_existing_output_and_output_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            root.chmod(0o700)
            output = root / "secrets.json"
            output.write_text("sensitive", encoding="utf-8")
            output.chmod(0o600)
            with self.assertRaises(DriveBackupRejected):
                check_output_file(output)
            output.unlink()
            output.symlink_to(root / "not-created.json")
            with self.assertRaises(DriveBackupRejected):
                check_output_file(output)

    def test_oauth_client_requires_private_file_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            root.chmod(0o700)
            client = root / "oauth_client.json"
            client.write_text('{"installed": {}}', encoding="utf-8")
            client.chmod(0o600)
            check_private_file(client)
            client.chmod(0o644)
            with self.assertRaises(DriveBackupRejected):
                check_private_file(client)

    def test_manual_homologation_does_not_enable_scheduled_backup(self):
        workflows = [
            ROOT / ".github/workflows/mar-f02-google-drive-backup.yml",
            ROOT / ".github/workflows/mar-f02-google-drive-old-recovery.yml",
        ]
        for workflow in workflows:
            with self.subTest(workflow=str(workflow.name)):
                content = workflow.read_text(encoding="utf-8")
                self.assertIn("github.event_name == 'workflow_dispatch' && vars.MAR_P0_GOOGLE_DRIVE_BACKUP_TEST_ENABLED == 'true'", content)
                self.assertIn("github.event_name == 'schedule' && vars.MAR_P0_GOOGLE_DRIVE_BACKUP_ENABLED == 'true'", content)
                self.assertIn("github.ref == 'refs/heads/main'", content)
                self.assertIn("permissions:\\n  contents: read", content)

    def test_client_json_requires_private_parent_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            root.chmod(0o755)
            client = root / "desktop.json"
            client.write_text('{"installed": {}}', encoding="utf-8")
            client.chmod(0o600)
            with self.assertRaises(DriveBackupRejected):
                check_private_file(client)

    def test_output_requires_existing_private_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            root.chmod(0o700)
            check_output_file(root / "new-secret.json")
            with self.assertRaises(DriveBackupRejected):
                check_output_file(root / "missing" / "new-secret.json")


if __name__ == "__main__":
    unittest.main()
