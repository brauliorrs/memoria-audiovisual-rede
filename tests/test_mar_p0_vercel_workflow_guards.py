"""Static safeguards for MAR P0 Vercel scheduled backup and restore."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DAILY=(ROOT/".github/workflows/mar-p0-vercel-daily-backup.yml").read_text()
WEEKLY=(ROOT/".github/workflows/mar-p0-vercel-weekly-recovery.yml").read_text()
CLIENT=(ROOT/"scripts/mar_p0_offsite_vercel.py").read_text()


class ScheduledPrivateBlobTests(unittest.TestCase):
    def test_only_reviewed_main_can_schedule_daily(self):
        self.assertIn("cron: '17 3 * * *'", DAILY)
        self.assertIn("github.ref == 'refs/heads/main'", DAILY)
        self.assertIn("github.repository == 'brauliorrs/memoria-audiovisual-rede'", DAILY)
        self.assertNotIn("  pull_request:", DAILY)
        self.assertNotIn("  pull_request_target:", DAILY)

    def test_weekly_is_historical_and_main_only(self):
        self.assertIn("cron: '17 6 * * 0'", WEEKLY)
        self.assertIn("github.ref == 'refs/heads/main'", WEEKLY)
        self.assertIn("--min-age-hours 24 --max-age-hours 192", WEEKLY)
        self.assertNotIn("mar_p0_offsite_pg_restore backup", WEEKLY)

    def test_distinct_protected_environments_separate_neon(self):
        self.assertIn("environment: mar-p0-vercel-export", DAILY)
        self.assertIn("environment: mar-p0-vercel-recovery", DAILY)
        self.assertIn("environment: mar-p0-vercel-recovery", WEEKLY)
        self.assertIn("secrets.MAR_P0_READONLY_DATABASE_URL", DAILY)
        self.assertNotIn("MAR_P0_READONLY_DATABASE_URL", DAILY.split("  restore-private-blob:",1)[1])
        self.assertNotIn("MAR_P0_READONLY_DATABASE_URL", WEEKLY)

    def test_private_blob_token_and_no_public_endpoint(self):
        for workflow in (DAILY,WEEKLY):
            self.assertIn("secrets.MAR_P0_VERCEL_BLOB_READ_WRITE_TOKEN", workflow)
            self.assertNotIn("access: public", workflow)
            self.assertNotIn("AWS_ACCESS_KEY_ID", workflow)
        self.assertIn('access="private"', CLIENT)
        self.assertIn("overwrite=False", CLIENT)

    def test_no_delete_api_or_artifact_short_retention(self):
        for workflow in (DAILY,WEEKLY):
            self.assertNotIn("actions/upload-artifact@", workflow)
            self.assertNotIn("blob delete", workflow.lower())
        self.assertNotIn(".delete(", CLIENT)
        self.assertNotIn("delete_objects(", CLIENT)

    def test_different_restore_runner_and_database(self):
        self.assertIn("needs: [export-to-private-blob]", DAILY)
        self.assertIn("mar_p0_offsite_pg_restore restore", DAILY)
        self.assertIn("mar_p0_offsite_pg_restore restore", WEEKLY)
        for workflow in (DAILY,WEEKLY):
            self.assertIn("mar_p0_restore_$GITHUB_RUN_ID", workflow)
            self.assertIn("@127.0.0.1/$RESTORE_DB", workflow)

    def test_vercel_is_not_misrepresented_as_immutable(self):
        self.assertIn("Not WORM:", CLIENT)
        self.assertIn('"provider_retention_enforced": False', CLIENT)
        self.assertIn('"production_gate": "HOLD"', CLIENT)

    def test_cipher_file_hash_suffixed_and_source_schema_restricted(self):
        self.assertIn("sha256-{expected}.pgcustom.aesgcm", CLIENT)
        self.assertIn("MAGIC = ", CLIENT)
        self.assertIn("--expected-sha256", DAILY)
        self.assertIn("--expected-sha256", WEEKLY)


if __name__ == "__main__":
    unittest.main()
