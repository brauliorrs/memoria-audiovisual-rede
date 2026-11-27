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
        for error_code, expected in (
            ("invalid_grant", "oauth_invalid_grant"),
            ("invalid_client", "oauth_invalid_client"),
            ("not_allowed", "oauth_refresh_rejected"),
        ):
            with self.subTest(google_code=error_code):
                # Synthetic exception emulates google-auth's (message, dict) args;
                # imports no OAuth dependencies and makes no network requests.
                error = RuntimeError(
                    "F02_HIDDEN_PROVIDER_MESSAGE",
                    {"error": error_code, "error_description": "F02_HIDDEN_RAW_RESPONSE"},
                )
                result = drive.safe_oauth_refresh_code(error)
                self.assertEqual(result, expected)
                self.assertNotIn("F02_HIDDEN", result)


    def test_oauth_stage_failures_never_expose_exception_contents(self):
        from types import ModuleType
        from unittest.mock import patch
        import sys

        secret = "VERY_PRIVATE_OAUTH_TEST_SENTINEL"
        env = {
            "MAR_P0_DRIVE_OAUTH_CLIENT_ID": secret,
            "MAR_P0_DRIVE_OAUTH_CLIENT_SECRET": secret,
            "MAR_P0_DRIVE_OAUTH_REFRESH_TOKEN": secret,
        }
        names = (
            "google", "google.oauth2", "google.oauth2.credentials",
            "google.auth", "google.auth.transport", "google.auth.transport.requests",
            "google.auth.exceptions", "googleapiclient", "googleapiclient.discovery",
        )
        modules = {name: ModuleType(name) for name in names}

        class SyntheticRefreshError(Exception):
            pass

        class SyntheticTransportError(Exception):
            pass

        class WorkingCredentials:
            def __init__(self, *args, **kwargs):
                self.scopes = kwargs.get("scopes")
                self.granted_scopes = None
                self.valid = True

            def refresh(self, request):
                return None

        modules["google.oauth2.credentials"].Credentials = WorkingCredentials
        modules["google.auth.transport.requests"].Request = lambda: object()
        modules["google.auth.exceptions"].RefreshError = SyntheticRefreshError
        modules["google.auth.exceptions"].TransportError = SyntheticTransportError
        modules["googleapiclient.discovery"].build = lambda *args, **kwargs: object()

        with patch.dict(sys.modules, modules):
            self.assertIsNotNone(drive.get_service(env))

            class BadInit(WorkingCredentials):
                def __init__(self, *args, **kwargs):
                    raise RuntimeError(secret)

            class BadRefresh(WorkingCredentials):
                def refresh(self, request):
                    raise RuntimeError(secret)

            for credential_cls, build_fn, expected in (
                (BadInit, lambda *args, **kwargs: object(), "oauth_credentials_initialization_failed"),
                (BadRefresh, lambda *args, **kwargs: object(), "oauth_refresh_unexpected_failure"),
                (WorkingCredentials, lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError(secret)),
                 "oauth_drive_client_initialization_failed"),
            ):
                with self.subTest(reason=expected):
                    modules["google.oauth2.credentials"].Credentials = credential_cls
                    modules["googleapiclient.discovery"].build = build_fn
                    with self.assertRaises(drive.DriveBackupRejected) as rejected:
                        drive.get_service(env)
                    self.assertEqual(str(rejected.exception), expected)
                    self.assertNotIn(secret, str(rejected.exception))



if __name__ == "__main__":
    unittest.main()
