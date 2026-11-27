"""Offline regression checks: F02 failures emit only fixed diagnostic codes."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import unittest

from scripts import mar_p0_offsite_google_drive as drive
from scripts import mar_p0_offsite_pg_restore as backup


class F02FailureDiagnosticsTests(unittest.TestCase):
    def test_neon_rejection_reports_safe_code_not_secret(self):
        sentinel = "F02_PRIVATE_CONNECTION_SENTINEL"
        output = io.StringIO()
        with redirect_stdout(output):
            rc = backup.main(
                ["backup", "--encrypted-file", "/tmp/not-created-f02-dump.aesgcm", "--execute"],
                environ={"MAR_P0_READONLY_DATABASE_URL": sentinel},
            )
        self.assertEqual(rc, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "HOLD")
        self.assertEqual(report["rejected_code"], "invalid_connection_url")
        self.assertNotIn(sentinel, output.getvalue())

    def test_drive_rejection_reports_safe_code_not_secret(self):
        sentinel = "F02_PRIVATE_FOLDER_SENTINEL!"
        output = io.StringIO()
        with redirect_stdout(output):
            rc = drive.main(
                ["upload", "--encrypted-file", "/tmp/not-created-f02-dump.aesgcm",
                 "--receipt-file", "/tmp/not-created-f02-receipt.json", "--execute"],
                env={"MAR_P0_GOOGLE_DRIVE_FOLDER_ID": sentinel},
            )
        self.assertEqual(rc, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "HOLD")
        self.assertEqual(report["rejected_code"], "drive_id_invalid")
        self.assertNotIn(sentinel, output.getvalue())


    def test_oauth_google_rejection_is_classified_without_raw_details(self):
        from unittest.mock import patch
        from google.auth.exceptions import RefreshError
        from google.oauth2.credentials import Credentials

        env = {
            "MAR_P0_DRIVE_OAUTH_CLIENT_ID": "synthetic_client_id",
            "MAR_P0_DRIVE_OAUTH_CLIENT_SECRET": "F02_HIDDEN_CLIENT_SECRET",
            "MAR_P0_DRIVE_OAUTH_REFRESH_TOKEN": "F02_HIDDEN_REFRESH_TOKEN",
        }
        for error_code, expected in (
            ("invalid_grant", "oauth_invalid_grant"),
            ("invalid_client", "oauth_invalid_client"),
            ("not_allowed", "oauth_refresh_rejected"),
        ):
            with self.subTest(google_code=error_code):
                error = RefreshError(
                    "F02_HIDDEN_PROVIDER_MESSAGE",
                    {"error": error_code, "error_description": "F02_HIDDEN_RAW_RESPONSE"},
                )
                with patch.object(Credentials, "refresh", side_effect=error):
                    with self.assertRaises(drive.DriveBackupRejected) as rejected:
                        drive.get_service(env)
                self.assertEqual(str(rejected.exception), expected)
                for secret in ("F02_HIDDEN", "client_id", "refresh_token"):
                    self.assertNotIn(secret, str(rejected.exception))



if __name__ == "__main__":
    unittest.main()
