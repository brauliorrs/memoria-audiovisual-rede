"""Static no-cloud contract for MAR P0 scheduled protected recovery workflows."""
from __future__ import annotations

from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]
DAILY = BASE / ".github/workflows/mar-p0-durable-backup.yml"
WEEKLY = BASE / ".github/workflows/mar-p0-weekly-recovery.yml"
SCRIPT = BASE / "scripts/mar_p0_offsite_s3.py"


class ScheduledP0ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daily = DAILY.read_text(encoding="utf-8")
        cls.weekly = WEEKLY.read_text(encoding="utf-8")
        cls.archive = SCRIPT.read_text(encoding="utf-8")

    def test_daily_is_default_branch_only(self):
        self.assertIn("cron: '17 3 * * *'", self.daily)
        self.assertIn("github.ref == 'refs/heads/main'", self.daily)
        self.assertIn("github.repository == 'brauliorrs/memoria-audiovisual-rede'", self.daily)
        self.assertNotIn("pull_request_target:", self.daily)
        self.assertNotIn("  pull_request:", self.daily)

    def test_weekly_is_default_branch_only(self):
        self.assertIn("cron: '17 6 * * 0'", self.weekly)
        self.assertIn("github.ref == 'refs/heads/main'", self.weekly)
        self.assertIn("github.repository == 'brauliorrs/memoria-audiovisual-rede'", self.weekly)
        self.assertNotIn("pull_request_target:", self.weekly)
        self.assertNotIn("  pull_request:", self.weekly)

    def test_distinct_environments_protect_keys_and_source(self):
        self.assertIn("environment: mar-p0-backup-automation", self.daily)
        self.assertIn("environment: mar-p0-restore-automation", self.daily)
        self.assertIn("environment: mar-p0-restore-automation", self.weekly)
        self.assertIn("secrets.MAR_P0_READONLY_DATABASE_URL", self.daily)
        self.assertNotIn("MAR_P0_READONLY_DATABASE_URL", self.weekly)
        self.assertIn("secrets.MAR_P0_RESTORE_AES_KEY_HEX", self.weekly)
        restore = self.daily.split("  same-day-recovery:", 1)[1]
        self.assertNotIn("MAR_P0_READONLY_DATABASE_URL", restore)

    def test_roles_are_separate_oidc_and_nonpersistent(self):
        self.assertIn("vars.MAR_P0_AWS_UPLOAD_ROLE_ARN", self.daily)
        self.assertIn("vars.MAR_P0_AWS_RESTORE_ROLE_ARN", self.daily)
        self.assertIn("vars.MAR_P0_AWS_RESTORE_ROLE_ARN", self.weekly)
        for workflow in (self.daily, self.weekly):
            self.assertIn("id-token: write", workflow)
            self.assertNotIn("AWS_ACCESS_KEY_ID", workflow)
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", workflow)
            self.assertIn(
                "aws-actions/configure-aws-credentials@e1253824e5c10ff9df46874f81ed3ec929e19cfd",
                workflow,
            )

    def test_daily_has_independent_restore_and_no_plaintext_artifact(self):
        self.assertIn("needs: [archive]", self.daily)
        self.assertIn("mar_p0_offsite_s3 upload", self.daily)
        self.assertIn("mar_p0_offsite_s3 download", self.daily)
        self.assertIn("mar_p0_offsite_pg_restore restore", self.daily)
        self.assertNotIn("actions/upload-artifact@", self.daily)
        self.assertNotIn("pg_dump --file", self.daily)

    def test_weekly_restores_prior_day_without_source(self):
        self.assertIn("--min-age-hours 24 --max-age-hours 192", self.weekly)
        self.assertIn("mar_p0_offsite_pg_restore restore", self.weekly)
        self.assertNotIn("mar_p0_offsite_pg_restore backup", self.weekly)
        self.assertNotIn("neon.tech", self.weekly)

    def test_s3_archive_has_worm_and_protection_guards(self):
        for fragment in (
            'MIN_RETENTION_DAYS = 90',
            'rule.get("Mode") != "COMPLIANCE"',
            'get_bucket_versioning',
            'get_object_lock_configuration',
            'get_public_access_block',
            'get_bucket_encryption',
            'IfNoneMatch="*"',
            'ObjectLockMode="COMPLIANCE"',
            'ChecksumSHA256=',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.archive)

    def test_source_and_destination_are_never_the_same_database(self):
        self.assertIn("createdb --owner=mar_p0_restore", self.daily)
        self.assertIn("createdb --owner=mar_p0_restore", self.weekly)
        self.assertIn("@127.0.0.1/$RESTORE_DB", self.daily)
        self.assertIn("@127.0.0.1/$RESTORE_DB", self.weekly)


if __name__ == "__main__":
    unittest.main()
